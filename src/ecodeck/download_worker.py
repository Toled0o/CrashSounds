# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Worker sem Qt: protocolo JSON por pipes, inclusive no EXE windowed."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ecodeck.download_types import (
    MAX_AUDIO_SOURCE_BYTES,
    MAX_SOURCE_SECONDS,
    MAX_VIDEO_BYTES,
    DownloadFailure,
    DownloadRequest,
    check_metadata,
    require_tools,
)


def repair_stdio():
    # Python/PyInstaller windowed deixa sys.std* em None. Os pipes herdados
    # continuam nos handles Win32; duplicá-los permite IPC sem abrir console.
    for stream in (sys.stdin, sys.stdout):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if sys.platform != "win32":
        return
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetStdHandle.argtypes = [wintypes.DWORD]
    kernel.GetStdHandle.restype = wintypes.HANDLE
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.DuplicateHandle.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    kernel.DuplicateHandle.restype = wintypes.BOOL
    process = kernel.GetCurrentProcess()
    for name, number, flags, mode in (
        ("stdin", -10, os.O_RDONLY, "r"),
        ("stdout", -11, os.O_WRONLY, "w"),
    ):
        if getattr(sys, name) is not None:
            continue
        handle = kernel.GetStdHandle(number & 0xFFFFFFFF)
        duplicate = wintypes.HANDLE()
        if not handle or not kernel.DuplicateHandle(
            process, handle, process, ctypes.byref(duplicate), 0, False, 2
        ):
            raise OSError("Pipe de download indisponível.")
        descriptor = msvcrt.open_osfhandle(duplicate.value, flags | os.O_BINARY)
        setattr(sys, name, os.fdopen(descriptor, mode, encoding="utf-8", buffering=1))
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def emit(kind: str, **values):
    sys.stdout.write(
        json.dumps({"event": kind, **values}, ensure_ascii=False, allow_nan=False) + "\n"
    )
    sys.stdout.flush()


def native_run(arguments: list[str], *, timeout=180) -> str:
    completed = subprocess.run(
        arguments,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        timeout=timeout,
    )
    if completed.returncode:
        raise DownloadFailure("Não foi possível converter este arquivo de mídia.")
    return completed.stdout.decode("utf-8", errors="replace")


def probe(path: Path, tools: Path) -> dict:
    return json.loads(
        native_run(
            [
                str(tools / "ffmpeg" / "ffprobe.exe"),
                "-v",
                "error",
                "-show_entries",
                "format=duration,size:stream=codec_type,width,height",
                "-of",
                "json",
                str(path),
            ],
            timeout=30,
        )
    )


class SilentLogger:
    def debug(self, message):
        pass

    def info(self, message):
        pass

    def warning(self, message):
        pass

    def error(self, message):
        pass


def options(request: DownloadRequest, workspace: Path, tools: Path, report):
    maximum = MAX_VIDEO_BYTES if request.mode == "video" else MAX_AUDIO_SOURCE_BYTES
    last_report = 0.0

    def progress(data):
        nonlocal last_report
        # Incluir .part e fragmentos; o teto vale para o trabalho inteiro.
        size = sum(p.stat().st_size for p in workspace.iterdir() if p.is_file())
        if size > maximum:
            raise DownloadFailure("O download excedeu o limite de tamanho.")
        now = time.monotonic()
        if now - last_report >= 0.15 or data.get("status") == "finished":
            last_report = now
            report(
                "progress",
                downloaded=int(data.get("downloaded_bytes") or 0),
                total=int(data.get("total_bytes") or data.get("total_bytes_estimate") or 0),
                speed=float(data.get("speed") or 0),
            )

    def match(info, *, incomplete=False):
        if not incomplete:
            check_metadata(info, request)
        return None

    result = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "logger": SilentLogger(),
        "enable_file_urls": False,
        "hls_prefer_native": True,
        "cachedir": False,
        "usenetrc": False,
        "cookiefile": None,
        "cookiesfrombrowser": None,
        "noplaylist": True,
        "playlistend": 1,
        "max_downloads": 1,
        "socket_timeout": 20,
        "retries": 2,
        "fragment_retries": 2,
        "concurrent_fragment_downloads": 1,
        "max_filesize": maximum,
        "outtmpl": str(workspace / "source.%(ext)s"),
        "restrictfilenames": True,
        "windowsfilenames": True,
        "overwrites": False,
        "ffmpeg_location": str(tools / "ffmpeg"),
        "js_runtimes": {"node": {"path": str(tools / "node" / "node.exe")}},
        "remote_components": [],
        "progress_hooks": [progress],
        "match_filter": match,
        "postprocessor_hooks": [lambda data: report("stage", text="Preparando o arquivo…")],
        "writethumbnail": False,
        "writeinfojson": False,
        "writesubtitles": False,
    }
    if request.mode == "audio":
        result["format"] = "bestaudio/best"
    else:
        height = request.height
        result["format"] = (
            f"bv[ext=mp4][height<=?{height}]+ba[ext=m4a]/b[ext=mp4][height<=?{height}]"
        )
        result["merge_output_format"] = "mp4"
    return result


def download(request: DownloadRequest, workspace: Path, *, fixture=False, report=emit) -> dict:
    request.validate(fixture=fixture)
    tools = require_tools()
    from yt_dlp import YoutubeDL
    from yt_dlp.globals import plugin_dirs
    from yt_dlp.utils import MaxDownloadsReached

    plugin_dirs.value = []  # Não procurar plugins do perfil/CWD.
    report("stage", text="Consultando o link…")
    with YoutubeDL(options(request, workspace, tools, report)) as downloader:
        info = downloader.extract_info(request.url, download=False)
        check_metadata(info, request)
        report("stage", text="Baixando mídia…")
        try:
            result = downloader.extract_info(request.url, download=True)
        except MaxDownloadsReached:
            # Sinal de término após o primeiro arquivo; a presença e o conteúdo
            # do resultado ainda são validados abaixo.
            result = info
        check_metadata(result, request)
    # Nome fixo do nosso template; não aceitar caminho informado pelo site.
    candidates = [
        p
        for p in workspace.iterdir()
        if p.is_file()
        and p.name.startswith("source.")
        and p.suffix.lower()
        in {".mp4", ".m4a", ".webm", ".ogg", ".opus", ".mp3", ".wav", ".aac", ".flac", ".mkv"}
    ]
    if len(candidates) != 1:
        raise DownloadFailure("O site não entregou um arquivo de mídia compatível.")
    source = candidates[0]
    meta = probe(source, tools)
    duration = float(meta.get("format", {}).get("duration") or 0)
    if not 0 < duration <= MAX_SOURCE_SECONDS + 1:
        raise DownloadFailure("Use um vídeo com duração de até uma hora.")
    streams = meta.get("streams", [])
    if not any(s.get("codec_type") == "audio" for s in streams):
        raise DownloadFailure("Este vídeo não contém uma faixa de áudio.")
    if request.mode == "video":
        video = [s for s in streams if s.get("codec_type") == "video"]
        if source.suffix != ".mp4" or not video:
            raise DownloadFailure("O site não disponibilizou vídeo MP4.")
        if any(s.get("height", 0) > request.height for s in video):
            raise DownloadFailure("O vídeo não está disponível na resolução escolhida.")
        target = workspace / "media.mp4"
        source.replace(target)
    else:
        if request.start >= duration:
            raise DownloadFailure("O início do trecho está depois do fim do vídeo.")
        report("stage", text="Recortando o áudio…")
        target = workspace / "media.wav"
        native_run(
            [
                str(tools / "ffmpeg" / "ffmpeg.exe"),
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(request.start),
                "-i",
                str(source),
                "-t",
                str(request.duration),
                "-vn",
                "-ac",
                "2",
                "-ar",
                "48000",
                "-c:a",
                "pcm_s16le",
                "-n",
                str(target),
            ]
        )
        if not target.is_file() or target.stat().st_size <= 44:
            raise DownloadFailure("O trecho selecionado não contém áudio.")
    maximum = MAX_VIDEO_BYTES if request.mode == "video" else MAX_AUDIO_SOURCE_BYTES
    if target.stat().st_size > maximum:
        raise DownloadFailure("O arquivo excedeu o limite de tamanho.")
    title = "".join(c for c in str(info.get("title") or "Áudio do link") if c.isprintable())[:100]
    return {"file": target.name, "title": title or "Áudio do link"}


def main() -> int:
    try:
        repair_stdio()
    except Exception:
        return 2  # Sem diálogo de exceção do bootloader quando não há pipes.
    try:
        raw = sys.stdin.readline(8193)
        if len(raw) > 8192:
            raise ValueError("Pedido muito grande.")
        payload = json.loads(raw)
        if payload.get("kind") == "probe":
            tools = require_tools()
            from importlib.metadata import version

            versions = {"yt_dlp": version("yt-dlp"), "ejs": version("yt-dlp-ejs")}
            versions["ffmpeg"] = native_run(
                [str(tools / "ffmpeg" / "ffmpeg.exe"), "-version"], timeout=30
            ).splitlines()[0]
            versions["node"] = native_run(
                [str(tools / "node" / "node.exe"), "--version"], timeout=30
            ).strip()
            emit("probe", versions=versions)
            return 0
        request = DownloadRequest(**payload["request"])
        workspace = Path(payload["workspace"]).resolve()
        if not workspace.is_dir() or not workspace.name.startswith("crashsounds-download-"):
            raise ValueError("Área temporária inválida.")
        result = download(request, workspace, fixture="--download-worker-self-test" in sys.argv)
        emit("done", **result)
        return 0
    except (DownloadFailure, ValueError) as exc:
        emit("error", message=str(exc))
    except Exception as exc:
        message = (
            f"{type(exc).__name__}: {exc}"
            if "--download-worker-self-test" in sys.argv
            else "Não foi possível baixar este link. Confira se o vídeo é público e se o site é compatível; tente novamente ou use outro link."
        )
        emit("error", message=message)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
