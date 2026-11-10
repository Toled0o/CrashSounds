# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Contratos de download; não importam Qt nem abrem rede."""

from __future__ import annotations

import ipaddress
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

MAX_VIDEO_BYTES = 1024 * 1024 * 1024
MAX_AUDIO_SOURCE_BYTES = 256 * 1024 * 1024
MAX_SOURCE_SECONDS = 3600
MAX_CLIP_SECONDS = 120
MAX_JOB_SECONDS = 15 * 60


class DownloadCancelled(Exception):
    pass


class DownloadFailure(Exception):
    pass


def validate_url(value: str, *, fixture: bool = False) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 4096
        or any(ord(c) < 32 for c in value)
    ):
        raise ValueError("Cole um único link HTTPS válido.")
    url = value.strip()
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if fixture and parsed.scheme == "http" and host == "127.0.0.1":
        return url
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise ValueError("Use um link HTTPS público, sem usuário ou senha na URL.")
    if parsed.port not in (None, 443):
        raise ValueError("Use a porta HTTPS padrão.")
    if "." not in host or host.casefold().endswith((".local", ".localhost", ".internal")):
        raise ValueError("Use um endereço público de vídeo.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError("Endereços locais não são aceitos.")
    return url


@dataclass(frozen=True)
class DownloadRequest:
    url: str
    mode: str = "video"
    height: int = 720
    start: float = 0
    duration: float = 30

    def validate(self, *, fixture: bool = False):
        validate_url(self.url, fixture=fixture)
        if self.mode not in {"video", "audio"} or self.height not in {360, 720, 1080}:
            raise ValueError("Modo ou resolução inválidos.")
        for value in (self.start, self.duration):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError("Informe início e duração válidos.")
        if not 0 <= self.start < MAX_SOURCE_SECONDS or not 1 <= self.duration <= MAX_CLIP_SECONDS:
            raise ValueError("O trecho deve ter de 1 a 120 segundos.")
        return self


def media_tools() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "tools" / "media"
    return Path(__file__).resolve().parents[2] / ".tools" / "media"


def require_tools() -> Path:
    root = media_tools()
    for relative in ("ffmpeg/ffmpeg.exe", "ffmpeg/ffprobe.exe", "node/node.exe"):
        if not (root / relative).is_file():
            raise DownloadFailure(
                "Ferramentas de download ausentes. Reinstale o pacote completo do CrashSounds."
            )
    return root


def check_metadata(info: dict, request: DownloadRequest):
    if not isinstance(info, dict) or info.get("_type", "video") not in {"video", "url_transparent"}:
        raise DownloadFailure("Cole o link de um vídeo individual; playlists não são baixadas.")
    if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
        raise DownloadFailure("Transmissões ao vivo e agendadas não são aceitas.")
    duration = info.get("duration")
    if duration is not None:
        if (
            not isinstance(duration, (int, float))
            or not math.isfinite(duration)
            or not 0 < duration <= MAX_SOURCE_SECONDS
        ):
            raise DownloadFailure("Use um vídeo com duração de até uma hora.")
        if request.mode == "audio" and request.start >= duration:
            raise DownloadFailure("O início do trecho está depois do fim do vídeo.")
    maximum = MAX_VIDEO_BYTES if request.mode == "video" else MAX_AUDIO_SOURCE_BYTES
    size = info.get("filesize") or info.get("filesize_approx")
    if isinstance(size, (int, float)) and size > maximum:
        raise DownloadFailure("O vídeo excede o limite de tamanho deste modo.")
