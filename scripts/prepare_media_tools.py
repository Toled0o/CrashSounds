# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Ferramentas de vídeo em .tools, com origem e SHA-256 fixados."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def archive_for(name: str, spec: dict) -> Path:
    cache = ROOT / ".tools" / "media-archives"
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / f"{name}.zip"
    if (
        target.exists()
        and hashlib.file_digest(target.open("rb"), "sha256").hexdigest() == spec["sha256"]
    ):
        return target
    fd, temporary = tempfile.mkstemp(dir=cache, suffix=".part")
    import os

    try:
        digest = hashlib.sha256()
        total = 0
        with os.fdopen(fd, "wb") as dest, urllib.request.urlopen(spec["url"], timeout=60) as source:
            while chunk := source.read(1024 * 1024):
                total += len(chunk)
                if total > 256 * 1024 * 1024:
                    raise ValueError("Arquivo de ferramenta excede o limite.")
                digest.update(chunk)
                dest.write(chunk)
        if digest.hexdigest() != spec["sha256"]:
            raise ValueError(f"SHA-256 de {name} não confere.")
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


def prepare() -> Path:
    specs = json.loads((ROOT / "scripts" / "media-tools.json").read_text(encoding="utf-8"))
    destination = ROOT / ".tools" / "media"
    for name, spec in specs.items():
        archive = archive_for(name, spec)
        target = destination / name
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as bundle:
            for entry in bundle.infolist():
                path = Path(entry.filename)
                leaf = path.name
                if name == "node":
                    keep = leaf in {"node.exe", "LICENSE"} and len(path.parts) == 2
                else:
                    keep = path.parent.name == "bin" and (
                        leaf in {"ffmpeg.exe", "ffprobe.exe"} or path.suffix == ".dll"
                    )
                    keep = keep or leaf.lower().startswith(("license", "copying", "readme"))
                if not keep or entry.is_dir():
                    continue
                if entry.file_size > 300 * 1024 * 1024 or leaf in {"", ".", ".."}:
                    raise ValueError("Entrada inválida no pacote de ferramentas.")
                # Só o nome final validado; nunca extrair um caminho do ZIP.
                with bundle.open(entry) as source, (target / leaf).open("wb") as dest:
                    shutil.copyfileobj(source, dest)
        print(f"{name}: {spec['version']} preparado")
    shutil.copy2(ROOT / "scripts" / "media-tools.json", destination / "SOURCES.json")
    return destination


if __name__ == "__main__":
    print(prepare())
