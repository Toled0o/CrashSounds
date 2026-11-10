# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from __future__ import annotations

import base64
import binascii
import copy
import json
import os
import tempfile
import uuid
from pathlib import Path

import soundfile as sf

from ecodeck.models import EXTENSIONS, MAX_BUNDLE, MAX_DURATION, MAX_FILE, Sound, State


def atomic_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".ecodeck-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def validate_audio(path: Path):
    if path.suffix.lower() not in EXTENSIONS or not 0 < path.stat().st_size <= MAX_FILE:
        raise ValueError("Use MP3, WAV, OGG ou FLAC com até 64 MiB.")
    info = sf.info(path)
    if not 0 < info.duration <= MAX_DURATION or info.channels not in (1, 2):
        raise ValueError("Use áudio mono/estéreo com duração de até 120 segundos.")


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.media = root / "sounds"
        self.media.mkdir(parents=True, exist_ok=True)
        self.path = root / "library.json"
        self.state = State()
        if self.path.exists():
            # Falhar visivelmente: nunca sobrescrever biblioteca corrompida com estado vazio.
            if self.path.stat().st_size > 8 * 1024 * 1024:
                raise ValueError("library.json excede o limite de 8 MiB.")
            self.state = State.load(json.loads(self.path.read_text(encoding="utf-8")))

    def commit(self, state: State):
        validated = State.load(state.dump())
        atomic_json(self.path, validated.dump())
        self.state = validated

    def add(self, path: Path, category: str = "Geral") -> Sound:
        validate_audio(path)
        ident = uuid.uuid4().hex
        sound = Sound(ident, path.stem[:100], ident + path.suffix.lower(), category=category)
        target = self.media / sound.file
        try:
            # Exclusivo: não sobrescreve outro som, mesmo em caso de colisão.
            with path.open("rb") as source, target.open("xb") as dest:
                import shutil

                shutil.copyfileobj(source, dest)
            state = copy.deepcopy(self.state)
            state.sounds.append(sound)
            self.commit(state)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        return sound

    def remove(self, ident: str):
        state = copy.deepcopy(self.state)
        state.sounds = [s for s in state.sounds if s.id != ident]
        # Arquivos órfãos ficam locais para permitir recuperar exclusões acidentais.
        self.commit(state)

    def export_bundle(self, destination: Path):
        state = self.state.dump()
        # O pacote nunca pode ativar captura nem inicialização em outra máquina.
        state["settings"]["mix_microphone"] = False
        state["settings"]["start_with_windows"] = False
        if sum((self.media / s.file).stat().st_size for s in self.state.sounds) > MAX_BUNDLE:
            raise ValueError("Exportação limitada a 128 MiB de arquivos originais.")
        files = {
            s.file: base64.b64encode((self.media / s.file).read_bytes()).decode("ascii")
            for s in self.state.sounds
        }
        atomic_json(destination, {"format": "ecodeck-bundle-1", "library": state, "files": files})

    def import_bundle(self, source: Path):
        if source.stat().st_size > MAX_BUNDLE * 1.4 + 8 * 1024 * 1024:
            raise ValueError("Pacote muito grande.")
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("format") != "ecodeck-bundle-1":
            raise ValueError("Arquivo não é uma exportação EcoDeck.")
        state = State.load(payload["library"])
        files = payload["files"]
        if not isinstance(files, dict) or set(files) != {s.file for s in state.sounds}:
            raise ValueError("Pacote incompleto ou com arquivos inesperados.")
        prepared = []
        total = 0
        try:
            for sound in state.sounds:
                encoded = files[sound.file]
                if not isinstance(encoded, str) or len(encoded) > MAX_FILE * 1.34 + 4:
                    raise ValueError("Arquivo de áudio excede o limite.")
                try:
                    data = base64.b64decode(encoded, validate=True)
                except (binascii.Error, ValueError) as exc:
                    raise ValueError("Áudio base64 inválido.") from exc
                total += len(data)
                if total > MAX_BUNDLE or len(data) > MAX_FILE:
                    raise ValueError("Pacote excede os limites de áudio.")
                sound.id = uuid.uuid4().hex
                sound.file = sound.id + Path(sound.file).suffix
                target = self.media / sound.file
                prepared.append(target)
                with target.open("xb") as handle:
                    handle.write(data)
                validate_audio(target)
            state.settings.mix_microphone = False
            state.settings.start_with_windows = self.state.settings.start_with_windows
            state.settings.monitor = None
            state.settings.virtual = None
            state.settings.microphone = None
            self.commit(state)
        except Exception:
            for target in prepared:
                target.unlink(missing_ok=True)
            raise
