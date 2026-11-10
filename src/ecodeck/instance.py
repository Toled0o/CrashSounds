# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Abrir a janela da instância existente pelo atalho, com IPC por perfil."""

from __future__ import annotations

import ctypes
import hashlib
import sys
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtNetwork import QLocalServer, QLocalSocket


def channel_name(profile: Path) -> str:
    identity = (
        str(profile.resolve()).casefold() if sys.platform == "win32" else str(profile.resolve())
    )
    return "CrashSounds-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]


def allow_foreground(pid: int):
    if sys.platform == "win32" and pid > 0:
        user = ctypes.WinDLL("user32", use_last_error=True)
        user.AllowSetForegroundWindow.argtypes = [wintypes.DWORD]
        user.AllowSetForegroundWindow.restype = wintypes.BOOL
        user.AllowSetForegroundWindow(pid)


def notify_existing(profile: Path, *, action="show", pid=0, timeout=1000) -> bool:
    if action not in {"show", "downloads"}:
        return False
    allow_foreground(pid)
    socket = QLocalSocket()
    try:
        socket.connectToServer(channel_name(profile))
        if not socket.waitForConnected(timeout):
            return False
        socket.write((action + "\n").encode("ascii"))
        if socket.bytesToWrite() and not socket.waitForBytesWritten(timeout):
            return False
        if not socket.bytesAvailable() and not socket.waitForReadyRead(timeout):
            return False
        return bytes(socket.readAll()).strip() == b"ok"
    finally:
        socket.abort()


def activate_legacy_window(pid: int) -> bool:
    """Compatibilidade com versões anteriores ao IPC, sem encerrar processos."""
    if sys.platform != "win32" or pid <= 0:
        return False
    user = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user.EnumWindows.restype = wintypes.BOOL
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.IsIconic.argtypes = [wintypes.HWND]
    user.IsIconic.restype = wintypes.BOOL
    user.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
    user.SetForegroundWindow.argtypes = [wintypes.HWND]
    user.SetForegroundWindow.restype = wintypes.BOOL
    found = []

    @callback_type
    def visit(hwnd, _):
        owner = wintypes.DWORD()
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            title = ctypes.create_unicode_buffer(256)
            user.GetWindowTextW(hwnd, title, len(title))
            if title.value.startswith(("CrashSounds —", "EcoDeck —")):
                found.append(hwnd)
                return False
        return True

    user.EnumWindows(visit, 0)
    if not found:
        return False
    allow_foreground(pid)
    hwnd = found[0]
    user.ShowWindowAsync(hwnd, 9 if user.IsIconic(hwnd) else 5)
    user.SetForegroundWindow(hwnd)
    return True


class InstanceChannel(QObject):
    def __init__(self, profile: Path, callback, parent=None):
        super().__init__(parent)
        self.name = channel_name(profile)
        self.callback = callback
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.server.newConnection.connect(self.accept)
        self.clients = set()

    def listen(self) -> bool:
        # Chamado somente depois que este processo adquiriu QLockFile do perfil.
        QLocalServer.removeServer(self.name)
        return self.server.listen(self.name)

    def accept(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.setParent(self)
            socket._request = bytearray()
            self.clients.add(socket)
            socket.readyRead.connect(lambda client=socket: self.read(client))
            socket.disconnected.connect(lambda client=socket: self.discard(client))
            QTimer.singleShot(2000, socket, socket.disconnectFromServer)
            self.read(socket)

    def read(self, socket):
        socket._request.extend(bytes(socket.readAll()))
        if len(socket._request) > 32:
            socket.abort()
            return
        if b"\n" not in socket._request:
            return
        command = bytes(socket._request).strip()
        if command not in {b"show", b"downloads"}:
            socket.abort()
            return
        self.callback(command.decode("ascii"))
        socket.write(b"ok\n")
        socket.flush()
        socket.disconnectFromServer()

    def discard(self, socket):
        self.clients.discard(socket)
        socket.deleteLater()

    def close(self):
        for socket in list(self.clients):
            socket.abort()
        self.server.close()
