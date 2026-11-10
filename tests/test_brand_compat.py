# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from ecodeck import startup
from ecodeck.app import default_data_dir


def test_renamed_app_keeps_legacy_profile_without_moving_data(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert default_data_dir() == tmp_path / "EcoDeck"
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("legacy", [None, "own", "other"])
def test_new_startup_key_cleans_only_own_legacy_alias(monkeypatch, legacy):
    import sys

    monkeypatch.setattr(startup.sys, "platform", "win32")
    monkeypatch.setattr(startup.sys, "frozen", True, raising=False)
    monkeypatch.setattr(startup.sys, "executable", r"C:\Apps\CrashSounds\CrashSounds.exe")
    own = startup.command()
    values = {}
    if legacy:
        values["EcoDeck"] = own if legacy == "own" else '"C:\\Other\\EcoDeck.exe" --minimized'

    def query(key, name):
        if name not in values:
            raise FileNotFoundError(name)
        return values[name], 1

    def remove(key, name):
        if name not in values:
            raise FileNotFoundError(name)
        del values[name]

    registry = SimpleNamespace(
        HKEY_CURRENT_USER=1,
        REG_SZ=1,
        CreateKey=lambda *args: nullcontext("test"),
        OpenKey=lambda *args: nullcontext("test"),
        QueryValueEx=query,
        SetValueEx=lambda key, name, reserved, kind, value: values.__setitem__(name, value),
        DeleteValue=remove,
    )
    monkeypatch.setitem(sys.modules, "winreg", registry)
    startup.set_enabled(True)
    assert values["CrashSounds"] == own
    assert ("EcoDeck" in values) is (legacy == "other")
    assert startup.is_enabled()
    startup.set_enabled(False)
    assert not startup.is_enabled()
    assert ("EcoDeck" in values) is (legacy == "other")


def test_current_binary_is_recognized_under_legacy_startup_alias(monkeypatch):
    import sys

    monkeypatch.setattr(startup.sys, "platform", "win32")
    monkeypatch.setattr(startup.sys, "frozen", True, raising=False)
    monkeypatch.setattr(startup.sys, "executable", r"C:\Apps\CrashSounds\CrashSounds.exe")

    def query(key, name):
        if name != "EcoDeck":
            raise FileNotFoundError(name)
        return startup.command(), 1

    monkeypatch.setitem(
        sys.modules,
        "winreg",
        SimpleNamespace(
            HKEY_CURRENT_USER=1,
            REG_SZ=1,
            OpenKey=lambda *args: nullcontext("test"),
            QueryValueEx=query,
        ),
    )
    assert startup.is_enabled()
