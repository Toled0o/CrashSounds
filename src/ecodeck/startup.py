# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from __future__ import annotations

import subprocess
import sys


def command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --minimized'
    # Usar pythonw quando disponível: não abrir console no login.
    from pathlib import Path

    executable = Path(sys.executable)
    windowless = executable.with_name("pythonw.exe")
    return subprocess.list2cmdline(
        [str(windowless if windowless.exists() else executable), "-m", "ecodeck", "--minimized"]
    )


def set_enabled(enabled: bool):
    if sys.platform != "win32":
        if enabled:
            raise OSError("Inicialização automática é suportada apenas no Windows.")
        return
    import winreg

    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"
    ) as key:
        if enabled:
            winreg.SetValueEx(key, "CrashSounds", 0, winreg.REG_SZ, command())
        else:
            try:
                winreg.DeleteValue(key, "CrashSounds")
            except FileNotFoundError:
                pass
        try:
            value, kind = winreg.QueryValueEx(key, "EcoDeck")
            if kind == winreg.REG_SZ and value.strip().casefold() == command().casefold():
                winreg.DeleteValue(key, "EcoDeck")
        except FileNotFoundError:
            pass


def is_enabled() -> bool:
    """Lê somente a entrada do CrashSounds; não altera o registro ao abrir o app."""
    if sys.platform != "win32":
        return False
    import winreg

    for name in ("CrashSounds", "EcoDeck"):
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"
            ) as key:
                value, kind = winreg.QueryValueEx(key, name)
            if kind == winreg.REG_SZ and isinstance(value, str):
                if value.strip().casefold() == command().casefold():
                    return True
        except FileNotFoundError:
            continue
    return False
