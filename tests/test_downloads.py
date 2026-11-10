# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
import sys
import threading

import pytest

from ecodeck import download_client
from ecodeck.download_client import run_download, worker_messages
from ecodeck.download_types import (
    DownloadCancelled,
    DownloadFailure,
    DownloadRequest,
    check_metadata,
    validate_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "file:///C:/secret.txt",
        "data:video/mp4;base64,AAAA",
        "javascript:alert(1)",
        "ftp://example.org/a.mp4",
        "http://example.org/a.mp4",
        "https://user:pass@example.org/a",
        "https://localhost/a",
        "https://127.0.0.1/a",
        "https://10.0.0.1/a",
        "https://192.168.1.1/a",
        "https://host.local/a",
        "https://example.org:22/a",
        "https://example.org/a\n--exec",
    ],
)
def test_public_download_rejects_non_public_or_non_https_inputs(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_single_https_url_is_not_a_shell_command():
    url = "https://www.youtube.com/watch?v=example&list=other"
    assert validate_url(url) == url
    assert validate_url("https://vimeo.com/123") == "https://vimeo.com/123"
    with pytest.raises(ValueError):
        validate_url("http://127.0.0.1:8000/a.mp4")
    assert validate_url("http://127.0.0.1:8000/a.mp4", fixture=True).startswith("http://127.")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "shell"},
        {"height": 9999},
        {"duration": 0},
        {"duration": 121},
        {"start": -1},
        {"start": 3600},
        {"start": True},
        {"duration": float("nan")},
    ],
)
def test_request_rejects_invalid_limits(kwargs):
    with pytest.raises(ValueError):
        DownloadRequest("https://example.org/video", **kwargs).validate()


@pytest.mark.parametrize(
    "info",
    [
        {"_type": "playlist"},
        {"is_live": True},
        {"live_status": "is_upcoming"},
        {"duration": 3602},
        {"duration": float("inf")},
        {"duration": -1},
        {"filesize": 1024 * 1024 * 1024 + 1},
    ],
)
def test_metadata_limits_apply_before_downloading(info):
    with pytest.raises(DownloadFailure):
        check_metadata(info, DownloadRequest("https://example.org/video"))


def test_audio_start_after_end_is_rejected():
    with pytest.raises(DownloadFailure):
        check_metadata(
            {"duration": 15}, DownloadRequest("https://example.org/v", mode="audio", start=20)
        )


def test_failure_keeps_existing_destination_and_removes_workspace(tmp_path, monkeypatch):
    target = tmp_path / "existing.mp4"
    target.write_bytes(b"previous")

    def fail(payload, *args, **kwargs):
        from pathlib import Path

        (Path(payload["workspace"]) / "source.part").write_bytes(b"partial")
        raise DownloadFailure("site unavailable")

    monkeypatch.setattr(download_client, "worker_messages", fail)
    with pytest.raises(DownloadFailure):
        run_download(
            DownloadRequest("https://example.org/video"), target, lambda _: None, threading.Event()
        )
    assert target.read_bytes() == b"previous"
    assert not list(tmp_path.glob("crashsounds-download-*"))


def test_worker_cannot_return_path_outside_workspace(tmp_path, monkeypatch):
    secret = tmp_path / "private.mp4"
    secret.write_bytes(b"preserve")
    monkeypatch.setattr(
        download_client,
        "worker_messages",
        lambda *args, **kwargs: {"event": "done", "file": "../private.mp4"},
    )
    with pytest.raises(DownloadFailure):
        run_download(
            DownloadRequest("https://example.org/v"),
            tmp_path / "target.mp4",
            lambda _: None,
            threading.Event(),
        )
    assert secret.read_bytes() == b"preserve"
    assert not (tmp_path / "target.mp4").exists()


def test_pre_cancelled_request_does_not_spawn_process(monkeypatch):
    event = threading.Event()
    event.set()

    def forbidden(*args, **kwargs):
        raise AssertionError("process should not start")

    monkeypatch.setattr(download_client.subprocess, "Popen", forbidden)
    with pytest.raises(DownloadCancelled):
        worker_messages({}, lambda _: None, event)


def test_broken_worker_protocol_is_reported_without_hanging():
    script = "import sys; sys.stdin.readline(); print('not-json',flush=True)"
    with pytest.raises(DownloadFailure, match="inválida"):
        worker_messages(
            {},
            lambda _: None,
            threading.Event(),
            command=[sys.executable, "-u", "-c", script],
            timeout=10,
        )


def test_hung_worker_is_terminated_on_deadline():
    script = "import sys,time; sys.stdin.readline(); time.sleep(30)"
    with pytest.raises(DownloadFailure, match="excedeu"):
        worker_messages(
            {},
            lambda _: None,
            threading.Event(),
            command=[sys.executable, "-u", "-c", script],
            timeout=0.3,
        )


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Object")
def test_cancellation_terminates_worker_and_its_child():
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    event = threading.Event()
    handles = []

    def receive(item):
        if item.get("event") == "stage":
            handle = kernel.OpenProcess(0x00100000, False, int(item["text"]))
            assert handle
            handles.append(handle)
            event.set()

    script = (
        "import sys,subprocess,time,json; sys.stdin.readline(); "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
        "print(json.dumps({'event':'stage','text':str(p.pid)}),flush=True); time.sleep(60)"
    )
    try:
        with pytest.raises(DownloadCancelled):
            worker_messages(
                {}, receive, event, command=[sys.executable, "-u", "-c", script], timeout=10
            )
        assert len(handles) == 1
        assert kernel.WaitForSingleObject(handles[0], 5000) == 0
    finally:
        for handle in handles:
            kernel.CloseHandle(handle)
