# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Smoke explícito de interface; nunca usa os dispositivos ou o perfil real."""

import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from PySide6.QtGui import QFontDatabase

from ecodeck.audio import Mixer, decode
from ecodeck.storage import Store
from ecodeck.ui import MainWindow


def run_smoke(app, screenshot: Path | None = None) -> int:
    # O plugin offscreen do Qt no Windows não descobre fontes do sistema sozinho.
    # Apenas carregar localmente: fontes da Microsoft não entram na distribuição.
    for name in ("segoeui.ttf", "segoeuib.ttf", "seguisym.ttf"):
        font = Path("C:/Windows/Fonts") / name
        if font.is_file():
            QFontDatabase.addApplicationFont(str(font))
    with tempfile.TemporaryDirectory(prefix="ecodeck-qa-") as directory:
        root = Path(directory)
        # Exercitar codecs e SoXR dentro do EXE, sem abrir streams PortAudio.
        for ext, format_, subtype in (
            ("wav", "WAV", "PCM_16"),
            ("mp3", "MP3", None),
            ("ogg", "OGG", "VORBIS"),
            ("flac", "FLAC", "PCM_16"),
        ):
            fixture = root / f"codec.{ext}"
            sf.write(
                fixture,
                np.sin(np.arange(2205) * 0.1).astype("float32") * 0.1,
                22050,
                format=format_,
                subtype=subtype,
            )
            samples = decode(fixture)
            assert samples.shape[1] == 2 and abs(len(samples) - 4800) < 10
            mixer = Mixer()
            mixer.play("synthetic", samples)
            assert mixer.render(200).any()
        store = Store(root / "profile")
        # Os nomes são exemplos de organização. O conteúdo é apenas um tom sintético.
        names = [
            ("Aplausos", "Reações"),
            ("Rufar de tambores", "Reações"),
            ("Missão cumprida", "Jogos"),
            ("Cheguei!", "Conversa"),
            ("Pausa para o café", "Conversa"),
        ]
        for i, (name, category) in enumerate(names):
            source = root / f"{name}.wav"
            sf.write(source, np.zeros(2400, dtype="float32"), 48000)
            sound = store.add(source, category)
            sound.hotkey = f"Ctrl+Alt+{i + 1}"
            sound.favorite = i in (0, 2)
            store.state.sounds[-1] = sound
        store.commit(store.state)
        window = MainWindow(store, qa_mode=True)
        try:
            window.show()
            app.processEvents()
            assert window.table.rowCount() == 5
            window.search.setText("missão")
            assert window.table.rowCount() == 1
            window.search.clear()
            window.categories.setCurrentRow(1)
            assert window.table.rowCount() == 2
            window.categories.setCurrentRow(0)
            window.table.selectRow(0)
            window.play(window.selected_id())
            assert not window.engine.streams
            assert not window.hotkeys.actions
            if screenshot:
                screenshot.parent.mkdir(parents=True, exist_ok=True)
                if not window.grab().save(str(screenshot)):
                    raise OSError("Não foi possível salvar screenshot de QA.")
                store.state.settings.theme = "light"
                window.apply_theme()
                app.processEvents()
                if not window.grab().save(str(screenshot.with_stem(screenshot.stem + "-light"))):
                    raise OSError("Não foi possível salvar screenshot claro.")
        finally:
            window.shutdown()
            window.close()
            app.processEvents()
    return 0
