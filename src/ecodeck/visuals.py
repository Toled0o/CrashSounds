# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap


def icon_pixmap(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 128, size / 128)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#8b5cf6"))
    painter.drawRoundedRect(QRectF(4, 4, 120, 120), 30, 30)
    painter.setBrush(QColor("#ffffff"))
    for x, height in ((30, 26), (46, 52), (62, 76), (78, 42), (94, 20)):
        painter.drawRoundedRect(QRectF(x, 64 - height / 2, 8, height), 4, 4)
    painter.end()
    return pixmap


ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def app_icon() -> QIcon:
    icon = QIcon()
    for size in ICON_SIZES:
        icon.addPixmap(icon_pixmap(size))
    return icon


def write_ico(path):
    """ICO com imagens PNG reais em nove resoluções, sem dependência de Pillow."""
    import struct

    from PySide6.QtCore import QBuffer, QByteArray, QIODevice

    images = []
    for size in ICON_SIZES:
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not icon_pixmap(size).save(buffer, "PNG"):
            raise OSError("Não foi possível gerar imagem do ícone.")
        images.append((size, bytes(data)))
    offset = 6 + 16 * len(images)
    directory = bytearray(struct.pack("<HHH", 0, 1, len(images)))
    for size, data in images:
        dimension = 0 if size == 256 else size
        directory.extend(
            struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(data), offset)
        )
        offset += len(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(directory) + b"".join(data for _, data in images))


def stylesheet(theme: str) -> str:
    dark = theme == "dark"
    bg, panel, foreground, muted, line, selection = (
        ("#101019", "#191925", "#f5f3ff", "#a9a7bf", "#303044", "#322852")
        if dark
        else ("#f4f3fa", "#ffffff", "#242136", "#625c78", "#dedbea", "#ece5fc")
    )
    return f"""
    QWidget {{ color: {foreground}; font-family: 'Segoe UI'; font-size: 13px; }}
    QMainWindow, QDialog {{ background: {bg}; }}
    QLabel {{ background: transparent; }}
    QLabel#title {{ font-size: 30px; font-weight: 700; }}
    QLabel#brand {{ font-size: 25px; font-weight: 700; }}
    QLabel#eyebrow {{ color: #a78bfa; font-size: 10px; font-weight: 700; }}
    QLabel#muted {{ color: {muted}; }}
    QLabel#status {{ border: 1px solid {line}; border-radius: 12px; padding: 8px 12px; color: {muted}; }}
    QFrame#panel {{ background: {panel}; border: 1px solid {line}; border-radius: 14px; }}
    QPushButton {{ background: {panel}; border: 1px solid {line}; border-radius: 8px; padding: 9px 14px; }}
    QPushButton:hover {{ border-color: #a78bfa; background: {selection}; }}
    QPushButton:disabled {{ color: {muted}; }}
    QPushButton#accent {{ background: #7c3aed; color: white; border-color: #8b5cf6; font-weight: 600; }}
    QPushButton#accent:hover {{ background: #8b5cf6; }}
    QPushButton#stop {{ color: #fb7185; border-color: #7f3445; }}
    QLineEdit, QComboBox, QSpinBox {{ background: {panel}; border: 1px solid {line}; border-radius: 8px; padding: 9px; selection-background-color: #7c3aed; }}
    QLineEdit:focus, QComboBox:focus {{ border-color: #a78bfa; }}
    QComboBox QAbstractItemView {{ background: {panel}; selection-background-color: {selection}; }}
    QListWidget {{ background: transparent; border: 0; outline: 0; }}
    QListWidget::item {{ padding: 12px; border-radius: 8px; margin: 2px; }}
    QListWidget::item:selected {{ background: {selection}; color: {foreground}; }}
    QTableWidget {{ background: {panel}; alternate-background-color: {bg}; border: 0; gridline-color: {line}; outline: 0; selection-background-color: {selection}; selection-color: {foreground}; }}
    QTableWidget::item {{ padding: 8px; border-bottom: 1px solid {line}; }}
    QHeaderView::section {{ background: {panel}; color: {muted}; border: 0; border-bottom: 1px solid {line}; padding: 12px 8px; font-weight: 600; }}
    QSlider::groove:horizontal {{ background: {line}; height: 5px; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: #8b5cf6; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: #c4b5fd; width: 13px; margin: -4px 0; border-radius: 6px; }}
    QProgressBar {{ background: {panel}; color: {foreground}; border: 1px solid {line}; border-radius: 6px; text-align: center; min-height: 20px; }}
    QProgressBar::chunk {{ background: #7c3aed; border-radius: 5px; }}
    QCheckBox {{ spacing: 8px; padding: 6px 0; }}
    QMenu {{ background: {panel}; border: 1px solid {line}; padding: 5px; }}
    QMenu::item {{ padding: 8px 20px; }}
    QMenu::item:selected {{ background: {selection}; }}
    QToolTip {{ background: {panel}; color: {foreground}; border: 1px solid {line}; }}
    QStatusBar {{ color: {muted}; background: {bg}; }}
    """
