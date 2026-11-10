# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from ecodeck import startup
from ecodeck.storage import Store
from ecodeck.ui import MainWindow
from ecodeck.visuals import app_icon


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="EcoDeck — soundboard local para Windows")
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
    args = parser.parse_args(argv)
    if args.smoke_test:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("EcoDeck")
    app.setOrganizationName("Toled0o")
    app.setStyle("Fusion")
    app.setWindowIcon(app_icon())
    if args.smoke_test:
        from ecodeck.qa import run_smoke

        return run_smoke(app, args.screenshot)
    root = (
        args.data_dir
        or Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / "EcoDeck"
    )
    root.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(root / "ecodeck.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(
            None, "EcoDeck já está aberto", "Abra o EcoDeck pelo ícone na bandeja do Windows."
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
    if not args.minimized or not QSystemTrayIcon.isSystemTrayAvailable():
        window.show()
    app.aboutToQuit.connect(window.shutdown)
    result = app.exec()
    lock.unlock()
    return result
