# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import numpy as np
import pytest
import soundfile as sf


@pytest.fixture
def wav(tmp_path):
    path = tmp_path / "Reação.wav"
    time = np.arange(4800) / 48000
    sf.write(path, (0.1 * np.sin(2 * np.pi * 440 * time)).astype("float32"), 48000)
    return path
