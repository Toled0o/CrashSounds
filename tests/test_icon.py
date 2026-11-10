# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
import struct

from PySide6.QtWidgets import QApplication

from ecodeck.visuals import ICON_SIZES, app_icon, write_ico


def test_ico_directory_contains_real_sizes_and_png_data(tmp_path):
    app = QApplication.instance() or QApplication([])
    icon = tmp_path / "EcoDeck.ico"
    write_ico(icon)
    data = icon.read_bytes()
    assert struct.unpack_from("<HHH", data) == (0, 1, len(ICON_SIZES))
    for i, expected_size in enumerate(ICON_SIZES):
        width, height, _, _, planes, bits, length, offset = struct.unpack_from(
            "<BBBBHHII", data, 6 + i * 16
        )
        assert (width or 256) == (height or 256) == expected_size
        assert planes == 1 and bits == 32
        assert data[offset : offset + 8] == b"\x89PNG\r\n\x1a\n"
        png_width, png_height = struct.unpack_from(">II", data, offset + 16)
        assert png_width == png_height == expected_size
        assert offset + length <= len(data)
    assert len(app_icon().availableSizes()) == len(ICON_SIZES)
    assert app is not None
