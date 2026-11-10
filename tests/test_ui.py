# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
import copy

import pytest
from PySide6.QtWidgets import QApplication

from ecodeck import ui
from ecodeck.qa import run_smoke
from ecodeck.storage import Store
from ecodeck.ui import MainWindow, SettingsDialog, SoundDialog


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path, wav):
    store = Store(tmp_path / "profile")
    store.add(wav, "Reações")
    result = MainWindow(store, qa_mode=True)
    yield result
    result.shutdown()
    result.close()
    app.processEvents()


def test_smoke_both_themes_screenshot(app, tmp_path):
    output = tmp_path / "preview.png"
    assert run_smoke(app, output) == 0
    assert output.stat().st_size > 1000
    assert output.with_stem("preview-light").exists()


def test_favorite_search_and_volume_persist(window, app):
    ident = window.store.state.sounds[0].id
    window.toggle_favorite(ident)
    window.categories.setCurrentRow(1)
    assert window.table.rowCount() == 1
    window.search.setText("ausente")
    assert window.table.rowCount() == 0
    window.search.setText("reaç")
    assert window.table.rowCount() == 1
    window.master.setValue(25)
    window.save_master()
    window.save_volume(ident, 40)
    reopened = Store(window.store.root)
    assert reopened.state.settings.master == 0.25
    assert reopened.state.sounds[0].volume == 0.4
    assert reopened.state.sounds[0].favorite
    assert not window.engine.streams


def test_edit_dialog_roundtrip_without_device_access(window):
    sound = copy.deepcopy(window.store.state.sounds[0])
    dialog = SoundDialog(sound, ["Reações"])
    dialog.name.setText("Novo nome")
    dialog.category.setCurrentText("Jogos")
    dialog.hotkey.setText("Ctrl+Alt+2")
    dialog.update_sound(sound)
    assert sound.name == "Novo nome"
    assert sound.category == "Jogos"
    assert sound.hotkey == "Ctrl+Alt+2"
    dialog.close()


def test_settings_does_not_capture_until_explicit_apply(window, monkeypatch):
    monkeypatch.setattr(
        ui,
        "devices",
        lambda: [
            {"key": "a", "name": "Fones fictícios", "outputs": 2, "inputs": 0},
            {"key": "b", "name": "Cabo fictício", "outputs": 2, "inputs": 0},
            {"key": "c", "name": "Mic fictício", "outputs": 0, "inputs": 1},
        ],
    )
    dialog = SettingsDialog(window.store.state.settings)
    dialog.monitor.setCurrentIndex(1)
    dialog.virtual.setCurrentIndex(2)
    dialog.microphone.setCurrentIndex(1)
    dialog.mix.setChecked(True)
    settings = dialog.settings()
    assert settings.mix_microphone
    assert settings.monitor == "a"
    assert settings.virtual == "b"
    assert not window.engine.streams
    dialog.reject()


def test_stop_rejects_stale_worker_result(window):
    previous = window.engine.epoch
    window.pending = 1
    window.stop_sounds()
    window.loaded("fake", None, previous, window.engine.routing_epoch, "")
    assert window.pending == 0
    assert not window.engine.monitor.voices
