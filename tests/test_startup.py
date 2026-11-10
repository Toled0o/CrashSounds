# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from ecodeck import startup


@pytest.mark.parametrize(
    "registered,expected",
    [
        ('"C:\\Apps\\CrashSounds\\CrashSounds.exe" --minimized', True),
        ('"C:\\Other\\CrashSounds.exe" --minimized', False),
        ('"C:\\Apps\\CrashSounds\\CrashSounds.exe" --other', False),
    ],
)
def test_installer_registry_entry_is_recognized_without_writing(monkeypatch, registered, expected):
    import sys

    monkeypatch.setattr(startup.sys, "platform", "win32")
    monkeypatch.setattr(startup.sys, "frozen", True, raising=False)
    monkeypatch.setattr(startup.sys, "executable", r"C:\Apps\CrashSounds\CrashSounds.exe")
    registry = SimpleNamespace(
        HKEY_CURRENT_USER=1,
        REG_SZ=1,
        OpenKey=lambda *args: nullcontext("test"),
        QueryValueEx=lambda *args: (registered, 1),
    )
    monkeypatch.setitem(sys.modules, "winreg", registry)
    assert startup.is_enabled() is expected


def test_missing_startup_entry_is_disabled(monkeypatch):
    import sys

    def absent(*args):
        raise FileNotFoundError()

    monkeypatch.setattr(startup.sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "winreg", SimpleNamespace(HKEY_CURRENT_USER=1, OpenKey=absent))
    assert not startup.is_enabled()
