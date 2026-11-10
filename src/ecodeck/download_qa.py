# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Download real via HTTP apenas de fixture sintética em loopback."""

from __future__ import annotations

import functools
import http.server
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path

from ecodeck.download_client import run_download, worker_messages
from ecodeck.download_types import DownloadFailure, DownloadRequest, require_tools
from ecodeck.download_worker import native_run
from ecodeck.storage import Store


@contextmanager
def fixture_server(root: Path):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Handler, directory=str(root))
    )
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=0.05), daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/fixture.mp4"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def make_fixture(root: Path, *, silent=False):
    tools = require_tools()
    arguments = [
        str(tools / "ffmpeg" / "ffmpeg.exe"),
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=0x7c3aed:s=64x64:r=10:d=1",
    ]
    if not silent:
        arguments += ["-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-c:a", "aac"]
    else:
        arguments += ["-an"]
    arguments += ["-c:v", "mpeg4", "-shortest", "-n", str(root / "fixture.mp4")]
    native_run(arguments, timeout=30)


def run_download_smoke():
    versions = worker_messages({"kind": "probe"}, lambda event: None, threading.Event())
    assert versions["versions"]["node"].startswith("v26.")
    assert versions["versions"]["ejs"]
    with tempfile.TemporaryDirectory(prefix="crashsounds-download-qa-") as directory:
        root = Path(directory)
        make_fixture(root)
        with fixture_server(root) as url:
            messages = []
            video = run_download(
                DownloadRequest(url, mode="video", height=360),
                root / "saved.mp4",
                messages.append,
                threading.Event(),
                fixture=True,
            )
            assert video.path.stat().st_size > 100
            audio = run_download(
                DownloadRequest(url, mode="audio", duration=1),
                root / "saved.wav",
                messages.append,
                threading.Event(),
                fixture=True,
            )
            store = Store(root / "profile")
            imported = store.add(audio.path, "Downloads")
            assert (store.media / imported.file).is_file()
            assert messages
            (root / "fixture.mp4").unlink()
            make_fixture(root, silent=True)
            silent = run_download(
                DownloadRequest(url, mode="video", height=360),
                root / "silent.mp4",
                messages.append,
                threading.Event(),
                fixture=True,
            )
            assert silent.path.is_file()
            try:
                run_download(
                    DownloadRequest(url, mode="audio", duration=1),
                    root / "silent.wav",
                    messages.append,
                    threading.Event(),
                    fixture=True,
                )
            except DownloadFailure:
                pass
            else:
                raise AssertionError("Vídeo silencioso não pode produzir áudio.")
            assert not (root / "silent.wav").exists()
        assert not list(root.glob("crashsounds-download-*"))
    return versions["versions"]
