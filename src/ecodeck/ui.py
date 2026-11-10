# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from __future__ import annotations

import copy
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSlider,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ecodeck import __version__, startup
from ecodeck.audio import AudioEngine, devices
from ecodeck.hotkeys import Hotkeys
from ecodeck.models import Settings, Sound, State
from ecodeck.storage import Store
from ecodeck.visuals import app_icon, stylesheet


def button(label, action, style=""):
    result = QPushButton(label)
    result.setObjectName(style)
    result.clicked.connect(action)
    return result


def label(text, style=""):
    result = QLabel(text)
    result.setObjectName(style)
    return result


class SoundDialog(QDialog):
    def __init__(self, sound: Sound, categories: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editar som")
        self.setMinimumWidth(420)
        form = QFormLayout(self)
        self.name = QLineEdit(sound.name)
        self.name.setMaxLength(100)
        self.category = QComboBox()
        self.category.setEditable(True)
        self.category.addItems(categories)
        self.category.setCurrentText(sound.category)
        self.hotkey = QLineEdit(sound.hotkey)
        self.hotkey.setPlaceholderText("Ctrl+Alt+1 — vazio para remover")
        self.favorite = QCheckBox("Adicionar aos favoritos")
        self.favorite.setChecked(sound.favorite)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(round(sound.volume * 100))
        form.addRow("Nome", self.name)
        form.addRow("Categoria", self.category)
        form.addRow("Atalho global", self.hotkey)
        form.addRow("Volume", self.volume)
        form.addRow(self.favorite)
        form.addRow(label("Atalhos precisam de Ctrl ou Alt. Exemplo: Ctrl+Alt+1.", "muted"))
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Salvar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def update_sound(self, sound: Sound):
        sound.name = self.name.text().strip()
        sound.category = self.category.currentText().strip()
        sound.hotkey = self.hotkey.text().strip()
        sound.favorite = self.favorite.isChecked()
        sound.volume = self.volume.value() / 100


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Áudio e preferências")
        self.setMinimumWidth(620)
        self.original = settings
        self.activate_audio = False
        self.device_list = devices()
        form = QFormLayout(self)
        self.monitor = self.device_combo("outputs", settings.monitor)
        self.virtual = self.device_combo("outputs", settings.virtual)
        self.microphone = self.device_combo("inputs", settings.microphone)
        self.mix = QCheckBox("Misturar minha voz na saída virtual")
        self.mix.setChecked(settings.mix_microphone)
        self.mic_gain = QSlider(Qt.Orientation.Horizontal)
        self.mic_gain.setRange(0, 100)
        self.mic_gain.setValue(round(settings.mic_gain * 100))
        self.theme = QComboBox()
        self.theme.addItem("Escuro", "dark")
        self.theme.addItem("Claro", "light")
        self.theme.setCurrentIndex(0 if settings.theme == "dark" else 1)
        self.stop_key = QLineEdit(settings.stop_hotkey)
        self.autostart = QCheckBox("Iniciar com o Windows, na bandeja")
        self.autostart.setChecked(settings.start_with_windows)
        form.addRow(label("ROTEAMENTO DE ÁUDIO", "eyebrow"))
        form.addRow("Meus fones", self.monitor)
        form.addRow("Saída para o cabo virtual", self.virtual)
        form.addRow("Meu microfone real", self.microphone)
        form.addRow(self.mix)
        form.addRow("Volume da minha voz", self.mic_gain)
        hint = label(
            "No Discord/jogo, escolha CABLE Output como microfone.\n"
            "Aqui, a saída virtual deve ser CABLE Input.\n"
            "Sua voz vai só ao cabo, sem retorno nos fones.\n"
            "Aplicar e ativar inicia o áudio e a captura marcada acima.\n"
            "Salvar sem ativar encerra o áudio atual e guarda as preferências.",
            "muted",
        )
        hint.setWordWrap(True)
        form.addRow(hint)
        form.addRow("Tema", self.theme)
        form.addRow("Atalho de parar sons", self.stop_key)
        form.addRow(self.autostart)
        privacy = label(
            "Parar sons mantém sua voz na chamada. Desativar áudio encerra a captura.", "muted"
        )
        privacy.setWordWrap(True)
        form.addRow(privacy)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Salvar sem ativar")
        buttons.button(QDialogButtonBox.StandardButton.Save).clicked.connect(
            lambda: self.finish(False)
        )
        buttons.button(QDialogButtonBox.StandardButton.Apply).setText("Aplicar e ativar áudio")
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            lambda: self.finish(True)
        )
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def finish(self, activate):
        self.activate_audio = activate
        self.accept()

    def device_combo(self, kind: str, selected: str | None):
        combo = QComboBox()
        combo.setMinimumContentsLength(30)
        combo.addItem("Desativado", None)
        for device in self.device_list:
            if device[kind] > 0:
                combo.addItem(device["name"], device["key"])
        index = combo.findData(selected)
        if selected is not None and index < 0:
            combo.addItem(f"Ausente: {selected}", selected)
            index = combo.count() - 1
        combo.setCurrentIndex(max(0, index))
        return combo

    def settings(self) -> Settings:
        result = copy.deepcopy(self.original)
        result.monitor = self.monitor.currentData()
        result.virtual = self.virtual.currentData()
        result.microphone = self.microphone.currentData()
        result.mix_microphone = self.mix.isChecked()
        result.mic_gain = self.mic_gain.value() / 100
        result.theme = self.theme.currentData()
        result.stop_hotkey = self.stop_key.text().strip()
        result.start_with_windows = self.autostart.isChecked()
        return Settings.load(vars(result))


class LoadSignals(QObject):
    finished = Signal(str, object, int, int, str)


class LoadJob(QRunnable):
    def __init__(self, engine, sound, path, epoch, routing):
        super().__init__()
        self.engine, self.sound, self.path = engine, sound, path
        self.epoch, self.routing = epoch, routing
        self.signals = LoadSignals()

    def run(self):
        try:
            samples = self.engine.load(self.sound.id, self.path)
            self.signals.finished.emit(self.sound.id, samples, self.epoch, self.routing, "")
        except Exception as exc:
            self.signals.finished.emit(self.sound.id, None, self.epoch, self.routing, str(exc))


class MainWindow(QMainWindow):
    def __init__(self, store: Store, qa_mode: bool = False):
        super().__init__()
        self.store = store
        self.qa_mode = qa_mode
        self.engine = AudioEngine()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.pending = 0
        self.quitting = False
        self.setWindowTitle("CrashSounds — seu som, na hora certa")
        self.setWindowIcon(app_icon())
        self.resize(1180, 760)
        self.setMinimumSize(980, 620)
        self.hotkeys = Hotkeys(int(self.winId()))
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.build_ui()
        self.build_tray()
        self.apply_theme()
        self.refresh()
        self.register_hotkeys()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_health)
        self.timer.start(1000)

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(22, 24, 22, 16)
        layout.setSpacing(26)
        sidebar = QVBoxLayout()
        sidebar.setSpacing(12)
        sidebar.addWidget(label("◖ CrashSounds", "brand"))
        sidebar.addWidget(label("SEU SOM, NA HORA CERTA", "eyebrow"))
        sidebar.addSpacing(28)
        sidebar.addWidget(label("BIBLIOTECA", "eyebrow"))
        self.categories = QListWidget()
        self.categories.setFixedWidth(190)
        self.categories.currentRowChanged.connect(lambda _: self.render_table())
        sidebar.addWidget(self.categories, 1)
        sidebar.addWidget(button("Áudio e preferências", self.open_settings))
        sidebar.addWidget(button("Sobre o CrashSounds", self.about))
        sidebar.addWidget(label(f"v{__version__} · livre e local", "muted"))
        layout.addLayout(sidebar)
        main = QVBoxLayout()
        main.setSpacing(18)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.addWidget(label("SOUNDBOARD PARA WINDOWS", "eyebrow"))
        heading.addWidget(label("Sua coleção de sons", "title"))
        heading.addWidget(label("Um toque. Dois destinos. Nenhuma assinatura.", "muted"))
        header.addLayout(heading, 1)
        header.addWidget(button("＋ Adicionar sons", self.add_sounds, "accent"))
        main.addLayout(header)
        route_panel = QFrame()
        route_panel.setObjectName("panel")
        route_layout = QHBoxLayout(route_panel)
        route_layout.setContentsMargins(18, 16, 18, 16)
        route_text = QVBoxLayout()
        route_text.addWidget(label("PRONTO PARA ENTRAR NA CONVERSA?", "eyebrow"))
        self.route_label = label(
            "Escolha seus fones e o cabo virtual em Áudio e preferências.", "muted"
        )
        self.route_label.setWordWrap(True)
        route_text.addWidget(self.route_label)
        route_layout.addLayout(route_text, 1)
        self.audio_button = button("Ativar áudio", self.toggle_audio)
        route_layout.addWidget(self.audio_button)
        main.addWidget(route_panel)
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar um som ou categoria…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.render_table)
        search_row.addWidget(self.search, 1)
        search_row.addWidget(button("Editar", self.edit_sound))
        search_row.addWidget(button("Remover", self.remove_sound))
        transfer = QPushButton("Biblioteca ▾")
        menu = QMenu(transfer)
        menu.addAction("Exportar com os sons…", self.export_library)
        menu.addAction("Importar biblioteca…", self.import_library)
        transfer.setMenu(menu)
        search_row.addWidget(transfer)
        main.addLayout(search_row)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["★", "Som", "Categoria", "Atalho", "Volume", ""])
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col, width in ((0, 45), (2, 115), (3, 125), (4, 105), (5, 85)):
            self.table.setColumnWidth(col, width)
        self.table.cellDoubleClicked.connect(lambda row, _: self.play(self.row_id(row)))
        main.addWidget(self.table, 1)
        self.empty = label("Sua próxima reação começa aqui. Adicione seu primeiro som.", "muted")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.empty)
        bottom = QHBoxLayout()
        self.count = label("", "muted")
        bottom.addWidget(self.count)
        bottom.addStretch()
        bottom.addWidget(label("Volume geral", "muted"))
        self.master = QSlider(Qt.Orientation.Horizontal)
        self.master.setRange(0, 100)
        self.master.setValue(round(self.store.state.settings.master * 100))
        self.master.setFixedWidth(140)
        self.master.valueChanged.connect(self.preview_master)
        self.master_timer = QTimer(self)
        self.master_timer.setSingleShot(True)
        self.master_timer.timeout.connect(self.save_master)
        self.master.valueChanged.connect(lambda _: self.master_timer.start(400))
        self.master.sliderReleased.connect(self.save_master)
        self.master.keyReleaseEvent = self.master_key_release
        bottom.addWidget(self.master)
        self.master_value = label(f"{self.master.value()}%", "muted")
        bottom.addWidget(self.master_value)
        self.stop_button = button("■ Parar sons", self.stop_sounds, "stop")
        bottom.addWidget(self.stop_button)
        main.addLayout(bottom)
        self.status = label("Áudio desligado · microfone sem captura", "status")
        main.addWidget(self.status)
        layout.addLayout(main, 1)
        self.statusBar().showMessage(
            "Adicione sons, configure os destinos e ative o áudio para começar."
        )

    def master_key_release(self, event):
        QSlider.keyReleaseEvent(self.master, event)
        self.save_master()

    def build_tray(self):
        menu = QMenu(self)
        menu.addAction("Abrir CrashSounds", self.show_window)
        menu.addAction("Parar sons", self.stop_sounds)
        menu.addAction("Desativar áudio e microfone", self.disable_audio)
        menu.addSeparator()
        menu.addAction("Sair", self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("CrashSounds — áudio desligado")
        self.tray.activated.connect(
            lambda reason: (
                self.show_window()
                if reason == QSystemTrayIcon.ActivationReason.DoubleClick
                else None
            )
        )
        if not self.qa_mode and QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def apply_theme(self):
        QApplication.instance().setStyleSheet(stylesheet(self.store.state.settings.theme))

    def error(self, message):
        QMessageBox.warning(self, "CrashSounds", str(message))

    def save(self, state: State):
        self.store.commit(state)
        self.update_levels()

    def update_levels(self):
        settings = self.store.state.settings
        self.engine.set_levels(
            settings.master, {s.id: s.volume for s in self.store.state.sounds}, settings.mic_gain
        )

    def refresh(self):
        previous = (
            self.categories.currentItem().data(Qt.ItemDataRole.UserRole)
            if self.categories.currentItem()
            else None
        )
        self.categories.blockSignals(True)
        self.categories.clear()
        choices = [("Todos os sons", ("all", "")), ("★ Favoritos", ("favorites", ""))]
        choices += [
            (c, ("category", c))
            for c in sorted({s.category for s in self.store.state.sounds}, key=str.casefold)
        ]
        selected = 0
        for i, (name, value) in enumerate(choices):
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.categories.addItem(item)
            if value == previous:
                selected = i
        self.categories.setCurrentRow(selected)
        self.categories.blockSignals(False)
        self.update_levels()
        self.render_table()

    def row_id(self, row):
        item = self.table.item(row, 1)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def selected_id(self):
        return self.row_id(self.table.currentRow())

    def render_table(self, *_):
        if not hasattr(self, "table"):
            return
        selected_id = self.selected_id()
        query = self.search.text().casefold().strip()
        category = (
            self.categories.currentItem().data(Qt.ItemDataRole.UserRole)
            if self.categories.currentItem()
            else None
        )
        sounds = [
            s
            for s in self.store.state.sounds
            if (
                category is None
                or category[0] == "all"
                or (s.favorite if category[0] == "favorites" else s.category == category[1])
            )
            and (query in s.name.casefold() or query in s.category.casefold())
        ]
        self.table.setRowCount(0)
        for row, sound in enumerate(sounds):
            self.table.insertRow(row)
            self.table.setRowHeight(row, 58)
            favorite = button(
                "★" if sound.favorite else "☆",
                lambda checked=False, ident=sound.id: self.toggle_favorite(ident),
            )
            favorite.setStyleSheet("padding: 0; margin: 6px; font-size: 18px; color: #a78bfa;")
            favorite.setToolTip("Alternar favorito")
            favorite.setAccessibleName(f"Favoritar {sound.name}")
            self.table.setCellWidget(row, 0, favorite)
            name = QTableWidgetItem(sound.name)
            name.setData(Qt.ItemDataRole.UserRole, sound.id)
            name.setToolTip(sound.name)
            self.table.setItem(row, 1, name)
            self.table.setItem(row, 2, QTableWidgetItem(sound.category))
            self.table.setItem(row, 3, QTableWidgetItem(sound.hotkey or "—"))
            volume = QSlider(Qt.Orientation.Horizontal)
            volume.setRange(0, 100)
            volume.setValue(round(sound.volume * 100))
            volume.setAccessibleName(f"Volume de {sound.name}")
            volume.setToolTip(f"{volume.value()}%")
            volume.valueChanged.connect(
                lambda value, ident=sound.id, slider=volume: self.preview_volume(
                    ident, value, slider
                )
            )
            volume.sliderReleased.connect(
                lambda ident=sound.id, slider=volume: self.save_volume(ident, slider.value())
            )
            # Teclas e roda também persistem; debounce evita escrita por pixel do arraste.
            volume_timer = QTimer(volume)
            volume_timer.setSingleShot(True)
            volume_timer.timeout.connect(
                lambda ident=sound.id, slider=volume: self.save_volume(ident, slider.value())
            )
            volume.valueChanged.connect(lambda _, timer=volume_timer: timer.start(400))
            self.table.setCellWidget(row, 4, volume)
            play = button("▶ Tocar", lambda checked=False, ident=sound.id: self.play(ident))
            play.setStyleSheet("padding: 6px 8px;")
            play.setAccessibleName(f"Tocar {sound.name}")
            self.table.setCellWidget(row, 5, play)
            if selected_id == sound.id:
                self.table.selectRow(row)
        self.count.setText(f"{len(sounds)} de {len(self.store.state.sounds)} sons")
        self.empty.setVisible(not sounds)
        self.empty.setText(
            "Nenhum som encontrado. Tente outra busca."
            if self.store.state.sounds
            else "Sua próxima reação começa aqui. Adicione seu primeiro som."
        )

    def add_sounds(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Adicionar sons", "", "Áudio (*.mp3 *.wav *.ogg *.flac)"
        )
        errors = []
        category = (
            self.categories.currentItem().data(Qt.ItemDataRole.UserRole)
            if self.categories.currentItem()
            else None
        )
        for path in paths:
            try:
                self.store.add(
                    Path(path), category[1] if category and category[0] == "category" else "Geral"
                )
            except Exception as exc:
                errors.append(f"{Path(path).name}: {exc}")
        self.refresh()
        if errors:
            self.error("\n".join(errors[:12]))

    def toggle_favorite(self, ident):
        state = copy.deepcopy(self.store.state)
        for sound in state.sounds:
            if sound.id == ident:
                sound.favorite = not sound.favorite
        try:
            self.save(state)
            self.refresh()
        except Exception as exc:
            self.error(exc)

    def edit_sound(self):
        ident = self.selected_id()
        sound = next((s for s in self.store.state.sounds if s.id == ident), None)
        if sound is None:
            self.statusBar().showMessage("Selecione uma linha para editar.")
            return
        dialog = SoundDialog(
            sound, sorted({"Geral"} | {s.category for s in self.store.state.sounds}), self
        )
        while dialog.exec() == QDialog.DialogCode.Accepted:
            state = copy.deepcopy(self.store.state)
            dialog.update_sound(next(s for s in state.sounds if s.id == ident))
            try:
                self.save(state)
                self.refresh()
                self.register_hotkeys()
                return
            except Exception as exc:
                self.error(exc)

    def remove_sound(self):
        ident = self.selected_id()
        if not ident:
            self.statusBar().showMessage("Selecione uma linha para remover.")
            return
        if (
            QMessageBox.question(
                self,
                "Remover som",
                "Remover este som da biblioteca? O arquivo original não será alterado.",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self.engine.stop_all()
            self.store.remove(ident)
            self.refresh()
            self.register_hotkeys()
        except Exception as exc:
            self.error(exc)

    def preview_master(self, value):
        self.master_value.setText(f"{value}%")
        for mixer in (self.engine.monitor, self.engine.virtual):
            with mixer.lock:
                mixer.master = value / 100

    def save_master(self):
        state = copy.deepcopy(self.store.state)
        state.settings.master = self.master.value() / 100
        try:
            self.save(state)
        except Exception as exc:
            self.error(exc)

    def preview_volume(self, ident, value, slider):
        slider.setToolTip(f"{value}%")
        for mixer in (self.engine.monitor, self.engine.virtual):
            with mixer.lock:
                mixer.volumes[ident] = value / 100

    def save_volume(self, ident, value):
        state = copy.deepcopy(self.store.state)
        for sound in state.sounds:
            if sound.id == ident:
                sound.volume = value / 100
        try:
            self.save(state)
        except Exception as exc:
            self.error(exc)

    def play(self, ident):
        sound = next((s for s in self.store.state.sounds if s.id == ident), None)
        if not sound:
            return
        if not self.engine.running:
            self.statusBar().showMessage(
                "Áudio desligado. Configure os destinos e clique em Ativar áudio."
            )
            return
        if self.pending >= 4:
            self.statusBar().showMessage("Aguarde: há quatro sons na fila de carregamento.")
            return
        job = LoadJob(
            self.engine,
            sound,
            self.store.media / sound.file,
            self.engine.epoch,
            self.engine.routing_epoch,
        )
        job.signals.finished.connect(self.loaded)
        self.pending += 1
        self.pool.start(job)
        self.statusBar().showMessage(f"Carregando {sound.name}…")

    def loaded(self, ident, samples, epoch, routing, error):
        self.pending -= 1
        if self.quitting or epoch != self.engine.epoch or routing != self.engine.routing_epoch:
            return
        if error:
            self.statusBar().showMessage(f"Não foi possível tocar: {error}")
            return
        if any(s.id == ident for s in self.store.state.sounds):
            self.engine.play_loaded(ident, samples, epoch, routing)
            self.statusBar().showMessage(
                "Som disparado · use Parar sons para interromper a reprodução."
            )

    def stop_sounds(self):
        self.engine.stop_all()
        self.statusBar().showMessage(
            "Sons interrompidos. A voz continua ativa se a mixagem estiver ligada."
        )

    def disable_audio(self):
        try:
            self.engine.close()
        except Exception as exc:
            self.error(exc)
        self.update_health()

    def toggle_audio(self):
        if self.engine.running:
            self.disable_audio()
        elif not (self.store.state.settings.monitor or self.store.state.settings.virtual):
            self.open_settings()
        else:
            try:
                self.engine.configure(self.store.state.settings)
                self.update_levels()
            except Exception as exc:
                self.error(f"Áudio não ativado: {exc}\nConfira os dispositivos e a taxa de 48 kHz.")
            self.update_health()

    def open_settings(self):
        try:
            dialog = SettingsDialog(self.store.state.settings, self)
        except Exception as exc:
            self.error(f"Não foi possível listar os dispositivos: {exc}")
            return
        while dialog.exec() == QDialog.DialogCode.Accepted:
            previous = copy.deepcopy(self.store.state)
            try:
                state = copy.deepcopy(previous)
                state.settings = dialog.settings()
                State.load(state.dump())
                if dialog.activate_audio:
                    self.engine.configure(state.settings)
                else:
                    self.engine.close()
                if state.settings.start_with_windows != previous.settings.start_with_windows:
                    startup.set_enabled(state.settings.start_with_windows)
                try:
                    self.save(state)
                except Exception:
                    if state.settings.start_with_windows != previous.settings.start_with_windows:
                        startup.set_enabled(previous.settings.start_with_windows)
                    raise
                self.apply_theme()
                self.register_hotkeys()
                self.update_health()
                return
            except Exception as exc:
                self.engine.close()
                self.update_health()
                self.error(f"Configuração não aplicada: {exc}")

    def update_health(self):
        running = self.engine.running
        mixing = running and self.store.state.settings.mix_microphone
        self.audio_button.setText("Desativar áudio" if running else "Ativar áudio")
        if running:
            destinations = [
                name
                for name, key in (
                    ("fones", self.store.state.settings.monitor),
                    ("cabo virtual", self.store.state.settings.virtual),
                )
                if key
            ]
            state = f"Áudio ativo · {' + '.join(destinations)} · " + (
                "microfone EM CAPTURA" if mixing else "microfone sem captura"
            )
            self.route_label.setText(
                "Sua voz está sendo enviada ao cabo virtual."
                if mixing
                else "Sons prontos para tocar nos destinos selecionados."
            )
            if self.engine.xruns:
                state += f" · alertas de áudio: {self.engine.xruns}"
        else:
            state = "Áudio desligado · microfone sem captura"
            self.route_label.setText("Escolha seus fones e o cabo virtual em Áudio e preferências.")
            if self.engine.streams:
                self.engine.close()
                self.statusBar().showMessage(
                    "Dispositivo interrompido. Confira a conexão e reative o áudio."
                )
        self.status.setText(state)
        self.tray.setToolTip(f"CrashSounds — {state}")

    def register_hotkeys(self):
        if self.qa_mode:
            return []
        bindings = {"__stop__": self.store.state.settings.stop_hotkey}
        bindings.update({s.id: s.hotkey for s in self.store.state.sounds if s.hotkey})
        errors = self.hotkeys.configure(bindings)
        self.stop_button.setToolTip(self.store.state.settings.stop_hotkey)
        if errors:
            self.statusBar().showMessage("Atalho não registrado: " + " | ".join(errors))
        return errors

    def nativeEvent(self, event_type, message):
        if hasattr(self, "hotkeys"):
            action = self.hotkeys.action(int(message))
            if action:
                self.stop_sounds() if action == "__stop__" else self.play(action)
                return True, 0
        return super().nativeEvent(event_type, message)

    def export_library(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar biblioteca portátil",
            "Minha biblioteca.crashsounds.json",
            "CrashSounds (*.crashsounds.json)",
        )
        if path:
            try:
                self.store.export_bundle(Path(path))
                self.statusBar().showMessage("Biblioteca exportada com os arquivos de áudio.")
            except Exception as exc:
                self.error(exc)

    def import_library(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar biblioteca", "", "CrashSounds (*.json)"
        )
        if not path:
            return
        if (
            QMessageBox.question(
                self,
                "Substituir biblioteca?",
                "A importação substitui a lista e as preferências atuais.\nExporte um backup antes. Os destinos e a captura serão desativados.\nContinuar?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self.engine.close()
            self.store.import_bundle(Path(path))
            self.master.setValue(round(self.store.state.settings.master * 100))
            self.refresh()
            self.apply_theme()
            self.register_hotkeys()
            self.update_health()
            self.statusBar().showMessage(
                "Biblioteca importada. Configure os dispositivos antes de ativar o áudio."
            )
        except Exception as exc:
            self.error(exc)

    def about(self):
        QMessageBox.about(
            self,
            "Sobre o CrashSounds",
            f"<h2>CrashSounds {__version__}</h2>"
            "<p>Seu som, na hora certa. Soundboard gratuito, livre e local.</p>"
            "<p>Copyright (c) 2026 Murilo Siqueira Toledo.<br>"
            "Todos os direitos reservados nos termos da licença MIT.<br>GitHub: Toled0o</p>"
            "<p>Sem anúncios, telemetria ou conta. Sem vínculo com o Soundpad.</p>"
            "<p>Créditos: Qt/PySide6 (LGPLv3), NumPy (BSD), sounddevice/PortAudio (MIT), "
            "SoundFile (BSD), libsndfile (LGPL), python-soxr/SoXR (LGPL). "
            "Consulte THIRD_PARTY_NOTICES.md na distribuição.</p>"
            "<p>VB-CABLE é um produto externo da VB-Audio e tem licença própria.</p>",
        )

    def closeEvent(self, event):
        if not self.quitting and self.tray.isVisible():
            self.hide()
            self.tray.showMessage(
                "CrashSounds continua na bandeja",
                "Os atalhos e o áudio permanecem ativos. Use Sair para encerrar.",
            )
            event.ignore()
        else:
            self.shutdown()
            event.accept()
            QApplication.instance().quit()

    def shutdown(self):
        if self.quitting:
            return
        self.quitting = True
        self.timer.stop()
        if self.master_timer.isActive():
            self.master_timer.stop()
            self.save_master()
        self.hotkeys.clear()
        self.engine.close()
        self.pool.waitForDone()
        self.tray.hide()

    def quit_app(self):
        self.shutdown()
        QApplication.instance().quit()
