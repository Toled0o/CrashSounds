# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from ecodeck import startup
from ecodeck.instance import InstanceChannel, activate_legacy_window, notify_existing
from ecodeck.storage import Store
from ecodeck.ui import MainWindow
from ecodeck.visuals import app_icon


def default_data_dir() -> Path:
    # Manter o perfil existente: a troca de marca não move nem duplica sons.
    return Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "EcoDeck"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CrashSounds — soundboard local para Windows")
    parser.add_argument("--data-dir", type=Path, help="Diretório isolado para testes/perfis")
    parser.add_argument(
        "--minimized", action="store_true", help="Abrir na bandeja sem ativar captura"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="QA isolado sem captura, reprodução ou registro de atalhos",
    )
    parser.add_argument("--screenshot", type=Path, help="Salvar captura do QA em PNG")
    parser.add_argument("--downloads", action="store_true", help="Abrir a janela de links")
    args = parser.parse_args(argv)
    if args.smoke_test:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("CrashSounds")
    app.setOrganizationName("Toled0o")
    app.setStyle("Fusion")
    app.setWindowIcon(app_icon())
    if args.smoke_test:
        from ecodeck.qa import run_smoke

        return run_smoke(app, args.screenshot)
    root = args.data_dir or default_data_dir()
    root.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(root / "ecodeck.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        if args.minimized:
            return 0
        pid, _host, _name = lock.getLockInfo()
        action = "downloads" if args.downloads else "show"
        if notify_existing(root, action=action, pid=pid):
            return 0
        if activate_legacy_window(pid):
            return 0
        # A instância anterior pode ter acabado de encerrar.
        if not lock.tryLock(300):
            QMessageBox.information(
                None,
                "CrashSounds",
                "O aplicativo está encerrando. Tente abrir novamente em alguns segundos.",
            )
            return 0
    try:
        store = Store(root)
    except Exception as exc:
        QMessageBox.critical(
            None, "Biblioteca não carregada", f"Seus dados foram preservados em {root}.\n\n{exc}"
        )
        return 1
    # O instalador e a interface compartilham a entrada Run do usuário.
    store.state.settings.start_with_windows = startup.is_enabled()
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow(store)

    def receive(action):
        window.show_window()
        if action == "downloads":
            window.open_downloader()

    channel = InstanceChannel(root, receive, app)
    channel.listen()
    if args.downloads:
        receive("downloads")
    elif not args.minimized or not QSystemTrayIcon.isSystemTrayAvailable():
        window.show()
    app.aboutToQuit.connect(window.shutdown)
    app.aboutToQuit.connect(channel.close)
    result = app.exec()
    lock.unlock()
    return result
