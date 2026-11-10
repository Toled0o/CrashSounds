# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
import threading

import pytest

from ecodeck.download_client import run_download
from ecodeck.download_qa import fixture_server, make_fixture, run_download_smoke
from ecodeck.download_types import DownloadFailure, DownloadRequest, require_tools


@pytest.fixture(scope="module", autouse=True)
def media_runtime():
    try:
        require_tools()
    except DownloadFailure:
        pytest.skip("Execute python scripts/prepare_media_tools.py para testes de mídia.")


def test_real_video_download_audio_cut_and_library_import():
    versions = run_download_smoke()
    assert versions["yt_dlp"] and versions["ffmpeg"]


def test_http_failure_does_not_replace_existing_file(tmp_path):
    make_fixture(tmp_path)
    destination = tmp_path / "keep.mp4"
    destination.write_bytes(b"old-file")
    with fixture_server(tmp_path) as source:
        missing = source.replace("fixture.mp4", "not-found.mp4")
        with pytest.raises(DownloadFailure):
            run_download(
                DownloadRequest(missing),
                destination,
                lambda _: None,
                threading.Event(),
                fixture=True,
            )
    assert destination.read_bytes() == b"old-file"
    assert not list(tmp_path.glob("crashsounds-download-*"))
