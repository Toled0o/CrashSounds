# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
import copy
import json

import pytest

from ecodeck import storage
from ecodeck.models import Sound, State
from ecodeck.storage import Store


def test_add_persists_and_source_is_independent(tmp_path, wav):
    store = Store(tmp_path / "profile")
    sound = store.add(wav, "Memes")
    wav.unlink()
    assert (store.media / sound.file).exists()
    reopened = Store(store.root)
    assert reopened.state.sounds[0].name == "Reação"
    assert reopened.state.sounds[0].category == "Memes"
    reopened.remove(sound.id)
    assert not Store(store.root).state.sounds


def test_portable_roundtrip_and_privacy(tmp_path, wav):
    store = Store(tmp_path / "a")
    sound = store.add(wav)
    store.state.settings.mix_microphone = True
    store.state.settings.start_with_windows = True
    store.state.settings.virtual = "device from another PC"
    bundle = tmp_path / "backup.json"
    store.export_bundle(bundle)
    imported = Store(tmp_path / "b")
    imported.import_bundle(bundle)
    result = imported.state.sounds[0]
    assert result.name == sound.name
    assert result.id != sound.id
    assert (imported.media / result.file).read_bytes() == wav.read_bytes()
    assert not imported.state.settings.mix_microphone
    assert not imported.state.settings.start_with_windows
    assert imported.state.settings.virtual is None


@pytest.mark.parametrize("file", ["../../evil.wav", "C:\\Windows\\evil.wav", "/tmp/x.wav", "a.wav"])
def test_reject_paths(file):
    with pytest.raises(ValueError, match="Caminho"):
        Sound.load({"id": "a" * 32, "name": "x", "file": file})


@pytest.mark.parametrize("volume", [float("nan"), float("inf"), -1, 1.1, "1", True])
def test_reject_invalid_volume(volume):
    state = State().dump()
    state["settings"]["master"] = volume
    with pytest.raises(ValueError):
        State.load(state)


def test_duplicate_hotkeys_case_insensitive(wav, tmp_path):
    store = Store(tmp_path / "a")
    store.add(wav)
    state = copy.deepcopy(store.state)
    state.sounds[0].hotkey = "ctrl+alt+space"
    with pytest.raises(ValueError, match="repetido"):
        store.commit(state)


def test_failed_atomic_save_preserves_memory_and_disk(monkeypatch, tmp_path, wav):
    store = Store(tmp_path / "a")
    store.add(wav)
    before = store.path.read_bytes()
    changed = copy.deepcopy(store.state)
    changed.sounds[0].name = "Changed"

    def fail(*_):
        raise OSError("disk full")

    monkeypatch.setattr(storage.os, "replace", fail)
    with pytest.raises(OSError):
        store.commit(changed)
    assert store.path.read_bytes() == before
    assert store.state.sounds[0].name == "Reação"
    assert not list(store.root.glob(".ecodeck-*"))


@pytest.mark.parametrize("damage", ["base64", "audio", "path", "extra", "schema"])
def test_invalid_import_is_transactional(tmp_path, wav, damage):
    store = Store(tmp_path / "a")
    sound = store.add(wav)
    bundle = tmp_path / "backup.json"
    store.export_bundle(bundle)
    payload = json.loads(bundle.read_text(encoding="utf-8"))
    if damage == "base64":
        payload["files"][sound.file] = "!!!"
    elif damage == "audio":
        payload["files"][sound.file] = "bm90IGF1ZGlv"
    elif damage == "path":
        payload["library"]["sounds"][0]["file"] = "../outside.wav"
    elif damage == "extra":
        payload["files"]["../outside.wav"] = ""
    else:
        payload["library"]["schema"] = 100
    bundle.write_text(json.dumps(payload), encoding="utf-8")
    before = store.path.read_bytes()
    files = list(store.media.iterdir())
    with pytest.raises((ValueError, RuntimeError)):
        store.import_bundle(bundle)
    assert store.path.read_bytes() == before
    assert list(store.media.iterdir()) == files


def test_corrupt_library_never_overwritten(tmp_path):
    root = tmp_path / "a"
    root.mkdir()
    path = root / "library.json"
    path.write_text("invalid json", encoding="utf-8")
    with pytest.raises(ValueError):
        Store(root)
    assert path.read_text() == "invalid json"
