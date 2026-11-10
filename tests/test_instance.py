# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
import subprocess
import sys
import time

from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from ecodeck.instance import InstanceChannel, channel_name
from ecodeck.storage import Store
from ecodeck.ui import MainWindow


def test_shortcut_restores_existing_window_and_opens_links(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Store(tmp_path), qa_mode=True)

    def receive(action):
        window.show_window()
        if action == "downloads":
            window.open_downloader()

    channel = InstanceChannel(tmp_path, receive)
    assert channel.listen()
    try:
        for action in ("show", "downloads"):
            window.hide()
            code = "from PySide6.QtCore import QCoreApplication; from pathlib import Path; from ecodeck.instance import notify_existing; import sys; app=QCoreApplication([]); sys.exit(0 if notify_existing(Path(sys.argv[1]), action=sys.argv[2],timeout=3000) else 1)"
            process = subprocess.Popen([sys.executable, "-c", code, str(tmp_path), action])
            deadline = time.monotonic() + 8
            while process.poll() is None and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.005)
            assert process.wait(timeout=1) == 0
            assert window.isVisible()
        assert window.download_dialog.isVisible()
        assert not window.engine.streams
        assert window.download_dialog.thread is None
    finally:
        channel.close()
        window.close()
        app.processEvents()


def test_channel_is_separate_per_profile(tmp_path):
    assert channel_name(tmp_path / "one") != channel_name(tmp_path / "two")


def test_stop_notice_expires_and_close_exits(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow(Store(tmp_path), qa_mode=True)
    window.show()
    window.stop_sounds()
    assert window.statusBar().currentMessage() == "Sons parados."
    QTest.qWait(2800)
    assert window.statusBar().currentMessage() == ""
    assert any(b.text() == "Baixar por link" for b in window.findChildren(QPushButton))
    # Run a real Qt loop: X must end it, rather than hide in the tray.
    QTimer.singleShot(20, window.close)
    watchdog = QTimer()
    watchdog.setSingleShot(True)
    watchdog.timeout.connect(app.quit)
    watchdog.start(2000)
    app.exec()
    assert watchdog.isActive()
    watchdog.stop()
    assert window.quitting
    assert not window.isVisible()
    assert not window.tray.isVisible()
    assert not window.engine.streams
