# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Janela de links: nenhum acesso à rede antes do clique em Baixar."""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ecodeck.download_client import run_download
from ecodeck.download_types import DownloadCancelled, DownloadRequest, require_tools
from ecodeck.models import text


class DownloadThread(QThread):
    progress = Signal(object)
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, request, destination, parent=None):
        super().__init__(parent)
        self.request, self.destination = request, destination
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            result = run_download(
                self.request, self.destination, self.progress.emit, self.cancel_event
            )
            self.succeeded.emit(result)
        except DownloadCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class DownloadDialog(QDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Baixar por link · CrashSounds")
        self.setMinimumWidth(580)
        self.thread = None
        self.staging = None
        self.close_requested = False
        self.shutting_down = False
        self.last_saved = None
        self.category_value = "Downloads"
        self.mode_value = "video"
        layout = QVBoxLayout(self)
        title = QLabel("Do link para o CrashSounds")
        title.setObjectName("title")
        layout.addWidget(title)
        hint = QLabel("Salve um vídeo MP4 ou transforme um trecho em som para sua biblioteca.")
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        layout.addWidget(hint)
        form = QFormLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText("https://…")
        self.url.setMaxLength(4096)
        self.url.setAccessibleName("Link público do vídeo")
        self.mode = QComboBox()
        self.mode.addItem("Salvar vídeo MP4", "video")
        self.mode.addItem("Trecho de áudio para a biblioteca", "audio")
        self.height = QComboBox()
        for value in (360, 720, 1080):
            self.height.addItem(f"Até {value}p", value)
        self.height.setCurrentIndex(1)
        self.start = QSpinBox()
        self.start.setRange(0, 3599)
        self.start.setSuffix(" s")
        self.duration = QSpinBox()
        self.duration.setRange(1, 120)
        self.duration.setValue(30)
        self.duration.setSuffix(" s")
        self.category = QComboBox()
        self.category.setEditable(True)
        self.category.addItems(
            sorted({"Downloads"} | {s.category for s in window.store.state.sounds})
        )
        self.category.setCurrentText("Downloads")
        self.audio_note = QLabel(
            "O arquivo de origem pode ser baixado por inteiro antes do recorte. O trecho terá até a duração escolhida."
        )
        self.audio_note.setWordWrap(True)
        self.audio_note.setObjectName("muted")
        form.addRow("Link do vídeo", self.url)
        form.addRow("O que baixar", self.mode)
        form.addRow("Resolução do vídeo", self.height)
        form.addRow("Início do trecho", self.start)
        form.addRow("Duração máxima", self.duration)
        form.addRow("Categoria", self.category)
        form.addRow(self.audio_note)
        self.form = form
        layout.addLayout(form)
        self.mode.currentIndexChanged.connect(self.update_mode)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.status = QLabel("Cole o link de um vídeo público e clique em Baixar.")
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        limits = QLabel(
            "Um vídeo por vez · até 1 hora · vídeo até 1 GiB · fonte de áudio até 256 MiB.\nAlguns sites ou vídeos podem exigir login e não funcionar nesta versão."
        )
        limits.setWordWrap(True)
        limits.setObjectName("muted")
        layout.addWidget(limits)
        controls = QHBoxLayout()
        self.open_folder = QPushButton("Abrir pasta")
        self.open_folder.setEnabled(False)
        self.open_folder.clicked.connect(self.show_folder)
        controls.addWidget(self.open_folder)
        controls.addStretch()
        self.close_button = QPushButton("Fechar")
        self.close_button.clicked.connect(self.reject)
        controls.addWidget(self.close_button)
        self.cancel_button = QPushButton("Cancelar download")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_download)
        controls.addWidget(self.cancel_button)
        self.start_button = QPushButton("Baixar")
        self.start_button.setObjectName("accent")
        self.start_button.clicked.connect(self.start_download)
        controls.addWidget(self.start_button)
        layout.addLayout(controls)
        self.update_mode()

    def update_mode(self):
        audio = self.mode.currentData() == "audio"
        self.form.setRowVisible(self.height, not audio)
        for widget in (self.start, self.duration, self.category):
            self.form.setRowVisible(widget, audio)
        for widget in (self.start, self.duration, self.category):
            widget.setEnabled(audio and self.thread is None)
        self.height.setEnabled(not audio and self.thread is None)
        self.audio_note.setVisible(audio)

    def set_busy(self, busy):
        self.url.setEnabled(not busy)
        self.mode.setEnabled(not busy)
        self.start_button.setEnabled(not busy)
        self.cancel_button.setEnabled(busy)
        if busy:
            for widget in (self.height, self.start, self.duration, self.category):
                widget.setEnabled(False)
        else:
            self.update_mode()

    def start_download(self):
        if self.thread is not None:
            return
        try:
            request = DownloadRequest(
                self.url.text().strip(),
                self.mode.currentData(),
                self.height.currentData(),
                self.start.value(),
                self.duration.value(),
            ).validate()
            require_tools()
            if request.mode == "audio":
                self.category_value = text(self.category.currentText(), "Categoria", 60)
                self.staging = tempfile.TemporaryDirectory(
                    prefix="crashsounds-import-", dir=self.window.store.root
                )
                destination = Path(self.staging.name) / "Áudio do link.wav"
            else:
                location = QStandardPaths.writableLocation(
                    QStandardPaths.StandardLocation.DownloadLocation
                )
                chosen, _ = QFileDialog.getSaveFileName(
                    self, "Salvar vídeo", str(Path(location) / "Vídeo.mp4"), "Vídeo MP4 (*.mp4)"
                )
                if not chosen:
                    return
                destination = Path(chosen)
                if destination.suffix.lower() != ".mp4":
                    destination = destination.with_suffix(".mp4")
                    if (
                        destination.exists()
                        and QMessageBox.question(
                            self, "Substituir arquivo?", f"Substituir {destination.name}?"
                        )
                        != QMessageBox.StandardButton.Yes
                    ):
                        return
            self.mode_value = request.mode
            self.close_requested = False
            self.last_saved = None
            self.open_folder.setEnabled(False)
            self.progress.setRange(0, 0)
            self.status.setText("Preparando download…")
            thread = DownloadThread(request, destination, self)
            self.thread = thread
            thread.progress.connect(self.on_progress)
            thread.succeeded.connect(self.on_success)
            thread.failed.connect(self.on_error)
            thread.cancelled.connect(
                lambda: self.status.setText("Download cancelado. Arquivos temporários removidos.")
            )
            thread.finished.connect(self.on_finished)
            self.set_busy(True)
            thread.start()
        except Exception as exc:
            self.cleanup_staging()
            self.status.setText(str(exc))

    def on_progress(self, item):
        if self.shutting_down or self.close_requested:
            return
        if item.get("event") == "stage":
            self.status.setText(str(item.get("text", "")))
        else:
            total, downloaded = item.get("total", 0), item.get("downloaded", 0)
            if total > 0:
                self.progress.setRange(0, 100)
                self.progress.setValue(min(99, int(downloaded * 100 / total)))
            else:
                self.progress.setRange(0, 0)
            mib = downloaded / (1024 * 1024)
            speed = item.get("speed", 0) / (1024 * 1024)
            self.status.setText(f"Baixando… {mib:.1f} MiB · {speed:.1f} MiB/s")

    def on_success(self, result):
        if self.shutting_down or self.close_requested or self.window.quitting:
            return
        try:
            if self.mode_value == "audio":
                sound = self.window.store.add(
                    result.path, self.category_value, name=text(result.title, "Nome")
                )
                self.window.refresh()
                self.last_saved = self.window.store.media / sound.file
                self.status.setText(f"Áudio adicionado à biblioteca: {result.title}")
            else:
                self.last_saved = result.path
                self.status.setText(f"Vídeo salvo: {result.path.name}")
            self.open_folder.setEnabled(True)
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
        except Exception as exc:
            self.on_error(str(exc))

    def on_error(self, message):
        if not self.shutting_down:
            self.status.setText(message)

    def on_finished(self):
        thread, self.thread = self.thread, None
        if thread:
            thread.deleteLater()
        self.cleanup_staging()
        self.set_busy(False)
        if self.last_saved is None:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
        if self.close_requested:
            super().reject()

    def cleanup_staging(self):
        if self.staging:
            self.staging.cleanup()
            self.staging = None

    def cancel_download(self):
        if self.thread:
            self.cancel_button.setEnabled(False)
            self.status.setText("Cancelando download…")
            self.thread.cancel()

    def reject(self):
        if self.thread:
            self.close_requested = True
            self.cancel_download()
            return
        super().reject()

    def shutdown(self):
        self.shutting_down = True
        if self.thread:
            self.thread.cancel()
            self.thread.wait()
        self.cleanup_staging()

    def show_folder(self):
        if self.last_saved:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_saved.parent)))
