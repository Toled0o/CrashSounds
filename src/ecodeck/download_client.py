# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Cliente do worker: cancelamento, limite de tempo e commit atômico do arquivo."""

from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from ecodeck.child_process import ChildGuard
from ecodeck.download_types import (
    MAX_JOB_SECONDS,
    DownloadCancelled,
    DownloadFailure,
    DownloadRequest,
)


def worker_command(*, fixture=False) -> list[str]:
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--download-worker"]
    else:
        executable = Path(sys.executable)
        console = executable.with_name("python.exe")
        command = [
            str(console if console.exists() else executable),
            "-m",
            "ecodeck",
            "--download-worker",
        ]
    if fixture:
        command.append("--download-worker-self-test")
    return command


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    title: str


def worker_messages(
    payload: dict,
    notify,
    cancel: threading.Event,
    *,
    fixture=False,
    command=None,
    timeout=MAX_JOB_SECONDS,
) -> dict:
    if cancel.is_set():
        raise DownloadCancelled()
    environment = dict(os.environ)
    for name in ("NODE_OPTIONS", "NODE_PATH", "PYTHONSTARTUP", "PYTHONPATH"):
        environment.pop(name, None)
    process = subprocess.Popen(
        command or worker_command(fixture=fixture),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        start_new_session=sys.platform != "win32",
        env=environment,
    )
    guard = None
    messages = queue.Queue(maxsize=64)
    stop_reader = threading.Event()

    def reader():
        try:
            while not stop_reader.is_set():
                line = process.stdout.readline(65537)
                if not line:
                    break
                if len(line) > 65536:
                    raise ValueError("Mensagem inválida do downloader.")
                item = json.loads(line)
                while not stop_reader.is_set():
                    try:
                        messages.put(item, timeout=0.1)
                        break
                    except queue.Full:
                        continue
        except Exception:
            try:
                messages.put(
                    {"event": "error", "message": "Resposta inválida do downloader."}, timeout=0.1
                )
            except queue.Full:
                pass

    read_thread = None
    try:
        # O worker espera stdin: associar ao job antes de permitir criar filhos.
        guard = ChildGuard(process)
        process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        process.stdin.close()
        read_thread = threading.Thread(target=reader, daemon=True)
        read_thread.start()
        deadline = time.monotonic() + timeout
        result = None
        failure = None
        while True:
            if cancel.is_set():
                raise DownloadCancelled()
            if time.monotonic() > deadline:
                raise DownloadFailure("O download excedeu 15 minutos. Tente um vídeo menor.")
            try:
                item = messages.get(timeout=0.1)
            except queue.Empty:
                if process.poll() is not None and not read_thread.is_alive():
                    break
                continue
            if not isinstance(item, dict):
                raise DownloadFailure("Resposta inválida do downloader.")
            kind = item.get("event")
            if kind in {"done", "probe"}:
                result = item
            elif kind == "error":
                failure = str(item.get("message") or "Falha no download.")[:700]
            elif kind in {"progress", "stage"}:
                notify(item)
        if cancel.is_set():
            raise DownloadCancelled()
        if failure or process.returncode or result is None:
            raise DownloadFailure(failure or "Não foi possível concluir o download.")
        return result
    finally:
        stop_reader.set()
        if guard:
            guard.close()
        else:
            process.kill()
            process.wait(timeout=5)
        if read_thread:
            read_thread.join(timeout=2)
        if process.stdout:
            process.stdout.close()
        if process.stdin and not process.stdin.closed:
            process.stdin.close()


def run_download(
    request: DownloadRequest, target: Path, notify, cancel: threading.Event, *, fixture=False
) -> DownloadResult:
    request.validate(fixture=fixture)
    target = target.resolve()
    expected = "media.mp4" if request.mode == "video" else "media.wav"
    with tempfile.TemporaryDirectory(
        prefix="crashsounds-download-", dir=target.parent
    ) as temporary:
        workspace = Path(temporary)
        result = worker_messages(
            {"kind": "download", "request": asdict(request), "workspace": str(workspace)},
            notify,
            cancel,
            fixture=fixture,
        )
        if result.get("file") != expected:
            raise DownloadFailure("Arquivo inesperado retornado pelo downloader.")
        source = workspace / expected
        if not source.is_file() or source.is_symlink():
            raise DownloadFailure("O arquivo baixado não foi encontrado.")
        if cancel.is_set():
            raise DownloadCancelled()
        notify({"event": "stage", "text": "Salvando arquivo…"})
        os.replace(source, target)
        return DownloadResult(target, str(result.get("title") or "Áudio do link")[:100])
