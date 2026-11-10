# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
import pytest

from ecodeck.hotkeys import parse_hotkey


def test_normalized_hotkey_and_norepeat():
    assert parse_hotkey("Ctrl+Alt+1") == parse_hotkey("alt + CTRL + 1") == (0x4003, 49)
    assert parse_hotkey("Ctrl+Alt+Space") == (0x4003, 0x20)


@pytest.mark.parametrize(
    "sequence",
    ["", "A", "Shift+A", "Ctrl+Ctrl+A", "Ctrl+F12", "Ctrl+á", "Ctrl+Alt", "Ctrl+A,B", "Ctrl++"],
)
def test_reject_unsupported_keys(sequence):
    with pytest.raises(ValueError):
        parse_hotkey(sequence)
