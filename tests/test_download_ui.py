# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from ecodeck import download_client
from ecodeck.download_client import DownloadResult
from ecodeck.storage import Store
from ecodeck.ui import MainWindow


@pytest.fixture
def window(tmp_path):
    app = QApplication.instance() or QApplication([])
    result = MainWindow(Store(tmp_path / "profile"), qa_mode=True)
    yield result
    result.shutdown()
    result.close()
    app.processEvents()


def test_opening_downloader_does_not_start_network_or_audio(window, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No worker before explicit download")

    monkeypatch.setattr(download_client.subprocess, "Popen", forbidden)
    window.open_downloader()
    dialog = window.download_dialog
    assert dialog.url.text() == ""
    assert dialog.thread is None
    assert not window.engine.streams
    assert dialog.height.isEnabled()
    dialog.mode.setCurrentIndex(1)
    assert dialog.duration.isEnabled()
    assert not dialog.height.isEnabled()


def test_downloaded_audio_is_imported_into_library(window, wav):
    window.open_downloader()
    dialog = window.download_dialog
    dialog.mode_value = "audio"
    dialog.category_value = "Links"
    dialog.on_success(DownloadResult(wav, "Reação baixada"))
    assert len(window.store.state.sounds) == 1
    assert window.store.state.sounds[0].name == "Reação baixada"
    assert window.store.state.sounds[0].category == "Links"
    assert window.table.rowCount() == 1
    assert dialog.progress.value() == 100
    assert not window.engine.streams


def test_close_requests_cancel_and_waits_for_worker_finish(window):
    window.open_downloader()
    dialog = window.download_dialog
    cancelled = []
    dialog.thread = SimpleNamespace(cancel=lambda: cancelled.append(True))
    dialog.reject()
    assert cancelled == [True]
    assert dialog.close_requested
    assert dialog.isVisible()
    dialog.thread = None
    dialog.on_finished()
    assert not dialog.isVisible()


def test_import_title_failure_does_not_leave_partial_library_entry(window, wav, monkeypatch):
    window.open_downloader()
    dialog = window.download_dialog
    dialog.mode_value = "audio"
    dialog.category_value = "Links"
    original = window.store.commit

    def reject_title(state):
        if any(sound.name == "Título rejeitado" for sound in state.sounds):
            raise OSError("Falha simulada na gravação")
        original(state)

    monkeypatch.setattr(window.store, "commit", reject_title)
    dialog.on_success(DownloadResult(wav, "Título rejeitado"))
    assert not window.store.state.sounds
    assert not list(window.store.media.iterdir())
    assert "Falha simulada" in dialog.status.text()
