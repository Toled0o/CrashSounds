# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Regenera o asset ICO versionado com o mesmo desenho da bandeja."""

from pathlib import Path

from PySide6.QtWidgets import QApplication

from ecodeck.visuals import write_ico

if __name__ == "__main__":
    app = QApplication([])
    write_ico(Path(__file__).resolve().parents[1] / "assets" / "EcoDeck.ico")
