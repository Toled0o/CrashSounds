# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Registro nativo e entrega à janela, sem injetar teclas ou reproduzir áudio."""

import os
import subprocess
import sys

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 apenas")
def test_native_hotkey_message_dispatch():
    # Offscreen fornece winId sintético. Processo separado, backend Windows,
    # janela oculta: sem teclado simulado, bandeja ou streams de áudio.
    script = """
import ctypes, tempfile
from ctypes import wintypes
from pathlib import Path
from PySide6.QtWidgets import QApplication
from ecodeck.hotkeys import Hotkeys
from ecodeck.storage import Store
from ecodeck.ui import MainWindow
app = QApplication([])
with tempfile.TemporaryDirectory(prefix="ecodeck-native-qa-") as directory:
    window = MainWindow(Store(Path(directory)), qa_mode=True)
    native = Hotkeys(int(window.winId()))
    try:
        errors = native.configure({"__stop__": "Ctrl+Alt+Shift+F11"})
        if errors:
            code = ctypes.get_last_error()
            if code == 1409:
                raise SystemExit(77)
            raise OSError(code, str(errors))
        window.hotkeys = native
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostMessageW.restype = wintypes.BOOL
        previous = window.engine.epoch
        assert user32.PostMessageW(int(window.winId()), 0x0312, 1, 0)
        app.processEvents()
        assert window.engine.epoch == previous + 1
    finally:
        window.shutdown()
        window.close()
        app.processEvents()
    assert not native.actions
"""
    environment = dict(os.environ, QT_QPA_PLATFORM="windows")
    result = subprocess.run(
        [sys.executable, "-c", script], env=environment, capture_output=True, text=True, timeout=30
    )
    if result.returncode == 77:
        pytest.skip("Combinação de QA já está em uso por outro programa.")
    assert result.returncode == 0, result.stdout + result.stderr
