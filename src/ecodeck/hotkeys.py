# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Atalhos Win32 sem hooks de teclado, polling ou permissão de administrador."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

MODIFIERS = {"ctrl": 0x2, "alt": 0x1, "shift": 0x4, "win": 0x8, "meta": 0x8}
KEYS = {
    "space": 0x20,
    "esc": 0x1B,
    "escape": 0x1B,
    "pause": 0x13,
    "home": 0x24,
    "end": 0x23,
    "insert": 0x2D,
    "delete": 0x2E,
}
KEYS.update({f"f{i}": 0x6F + i for i in range(1, 25)})


def parse_hotkey(sequence: str) -> tuple[int, int]:
    if not isinstance(sequence, str) or not sequence or len(sequence) > 80:
        raise ValueError("Informe um atalho, por exemplo Ctrl+Alt+1.")
    parts = [p.strip().lower() for p in sequence.split("+")]
    mods = 0
    for part in parts[:-1]:
        bit = MODIFIERS.get(part)
        if bit is None or mods & bit:
            raise ValueError("Combinação de modificadores inválida.")
        mods |= bit
    key = parts[-1]
    vk = ord(key.upper()) if len(key) == 1 and key.isascii() and key.isalnum() else KEYS.get(key)
    if vk is None or not mods & (0x1 | 0x2):
        raise ValueError("Use Ctrl ou Alt com uma letra, número, F1–F24 ou Space.")
    if key == "f12":
        raise ValueError("F12 é reservado pelo Windows; escolha outra tecla.")
    return mods | 0x4000, vk  # MOD_NOREPEAT


class Hotkeys:
    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self.actions: dict[int, str] = {}
        self.user32 = None
        if sys.platform == "win32":
            self.user32 = ctypes.WinDLL("user32", use_last_error=True)
            self.user32.RegisterHotKey.argtypes = [
                wintypes.HWND,
                ctypes.c_int,
                wintypes.UINT,
                wintypes.UINT,
            ]
            self.user32.RegisterHotKey.restype = wintypes.BOOL
            self.user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
            self.user32.UnregisterHotKey.restype = wintypes.BOOL

    def clear(self):
        if self.user32:
            for ident in self.actions:
                self.user32.UnregisterHotKey(self.hwnd, ident)
        self.actions.clear()

    def configure(self, bindings: dict[str, str]) -> list[str]:
        self.clear()
        errors = []
        for ident, (action, sequence) in enumerate(bindings.items(), 1):
            if not sequence:
                continue
            mods, key = parse_hotkey(sequence)
            if not self.user32 or not self.user32.RegisterHotKey(self.hwnd, ident, mods, key):
                errors.append(f"{sequence}: indisponível ou já usado por outro aplicativo.")
            else:
                self.actions[ident] = action
        return errors

    def action(self, message: int) -> str | None:
        if not self.user32:
            return None
        msg = wintypes.MSG.from_address(message)
        return self.actions.get(int(msg.wParam)) if msg.message == 0x0312 else None
