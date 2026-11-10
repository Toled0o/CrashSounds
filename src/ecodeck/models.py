# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Modelo local: nenhum caminho vindo de JSON pode escapar da biblioteca."""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field

from ecodeck.hotkeys import parse_hotkey

EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac"}
MAX_FILE = 64 * 1024 * 1024
MAX_BUNDLE = 128 * 1024 * 1024
MAX_DURATION = 120


def text(value: object, label: str, limit: int = 100) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{label}: texto vazio ou maior que {limit} caracteres.")
    return value.strip()


def gain(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("Volume inválido.")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Volume deve estar entre 0 e 1.")
    return float(value)


@dataclass
class Sound:
    id: str
    name: str
    file: str
    category: str = "Geral"
    hotkey: str = ""
    volume: float = 0.8
    favorite: bool = False

    @classmethod
    def load(cls, value: dict) -> Sound:
        sound = cls(**value)
        if not isinstance(sound.id, str) or not re.fullmatch(r"[a-f0-9]{32}", sound.id):
            raise ValueError("Identificador de som inválido.")
        if sound.file not in {sound.id + ext for ext in EXTENSIONS}:
            raise ValueError("Caminho de áudio inválido.")
        sound.name = text(sound.name, "Nome")
        sound.category = text(sound.category, "Categoria", 60)
        sound.volume = gain(sound.volume)
        if type(sound.favorite) is not bool:
            raise ValueError("Favorito inválido.")
        if not isinstance(sound.hotkey, str):
            raise ValueError("Atalho inválido.")
        if sound.hotkey:
            parse_hotkey(sound.hotkey)
        return sound


@dataclass
class Settings:
    monitor: str | None = None
    virtual: str | None = None
    microphone: str | None = None
    mix_microphone: bool = False
    master: float = 0.8
    mic_gain: float = 0.8
    theme: str = "dark"
    stop_hotkey: str = "Ctrl+Alt+Space"
    start_with_windows: bool = False

    @classmethod
    def load(cls, value: dict) -> Settings:
        settings = cls(**value)
        settings.master = gain(settings.master)
        settings.mic_gain = gain(settings.mic_gain)
        for device in (settings.monitor, settings.virtual, settings.microphone):
            if device is not None:
                text(device, "Dispositivo", 500)
        if settings.theme not in {"dark", "light"}:
            raise ValueError("Tema inválido.")
        if (
            type(settings.mix_microphone) is not bool
            or type(settings.start_with_windows) is not bool
        ):
            raise ValueError("Configuração booleana inválida.")
        parse_hotkey(settings.stop_hotkey)
        return settings


@dataclass
class State:
    sounds: list[Sound] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)
    schema: int = 1

    def dump(self) -> dict:
        return asdict(self)

    @classmethod
    def load(cls, value: dict) -> State:
        if not isinstance(value, dict) or set(value) != {"sounds", "settings", "schema"}:
            raise ValueError("Formato de biblioteca inválido.")
        if type(value["schema"]) is not int or value["schema"] != 1:
            raise ValueError("Versão de biblioteca não suportada.")
        if not isinstance(value["sounds"], list) or len(value["sounds"]) > 2000:
            raise ValueError("Biblioteca deve ter no máximo 2.000 sons.")
        sounds = [Sound.load(s) for s in value["sounds"]]
        settings = Settings.load(value["settings"])
        ids = [s.id for s in sounds]
        keys = [parse_hotkey(s.hotkey) for s in sounds if s.hotkey]
        keys.append(parse_hotkey(settings.stop_hotkey))
        if len(ids) != len(set(ids)) or len(keys) != len(set(keys)):
            raise ValueError("Identificador ou atalho repetido na biblioteca.")
        return cls(sounds=sounds, settings=settings)
