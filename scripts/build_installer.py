# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Compilador NSIS local e verificável, sem instalação global."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NSIS_VERSION = "3.11"
NSIS_SHA256 = "c7d27f780ddb6cffb4730138cd1591e841f4b7edb155856901cdf5f214394fa1"
NSIS_URL = "https://master.dl.sourceforge.net/project/nsis/NSIS%203/3.11/nsis-3.11.zip?viasf=1"


def ensure_nsis() -> Path:
    tools = ROOT / ".tools"
    archive = tools / f"nsis-{NSIS_VERSION}.zip"
    tools.mkdir(exist_ok=True)
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != NSIS_SHA256:
        with urllib.request.urlopen(NSIS_URL, timeout=60) as response:
            data = response.read(10 * 1024 * 1024)
        if hashlib.sha256(data).hexdigest() != NSIS_SHA256:
            raise ValueError("SHA-256 do compilador NSIS não confere; download não executado.")
        archive.write_bytes(data)
    compiler = tools / f"nsis-{NSIS_VERSION}" / "makensis.exe"
    if not compiler.exists():
        with zipfile.ZipFile(archive) as bundle:
            for member in bundle.infolist():
                target = (tools / member.filename).resolve()
                if tools.resolve() not in target.parents or member.file_size > 32 * 1024 * 1024:
                    raise ValueError("Caminho/tamanho inesperado no ZIP NSIS.")
            bundle.extractall(tools)
    return compiler


def nsis_quote(value: str) -> str:
    return value.replace("$", "$$").replace('"', '$\\"')


def uninstall_manifest(package: Path) -> str:
    lines = [
        "; Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT."
    ]
    for item in sorted(package.rglob("*")):
        if item.is_file():
            relative = nsis_quote(str(item.relative_to(package)).replace("/", chr(92)))
            lines.append(f'  Delete "$INSTDIR{chr(92)}{relative}"')
    directories = sorted(
        (p for p in package.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True
    )
    for item in directories:
        relative = nsis_quote(str(item.relative_to(package)).replace("/", chr(92)))
        lines.append(f'  RMDir "$INSTDIR{chr(92)}{relative}"')
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from ecodeck import __version__

    package = args.package.resolve()
    output = args.output.resolve()
    if not (package / "EcoDeck.exe").is_file():
        raise ValueError("Pacote EcoDeck.exe ausente.")
    output.mkdir(parents=True, exist_ok=True)
    manifest = output.parent / "build" / "uninstall-files.nsh"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(uninstall_manifest(package), encoding="utf-8-sig")
    compiler = ensure_nsis()
    subprocess.run(
        [
            str(compiler),
            "/V2",
            f"/DAPP_VERSION={__version__}",
            f"/DPACKAGE_DIR={package}",
            f"/DOUTPUT_DIR={output}",
            f"/DREPO_DIR={ROOT}",
            f"/DUNINSTALL_INCLUDE={manifest}",
            str(ROOT / "installer" / "ecodeck.nsi"),
        ],
        check=True,
    )
    (output / "BUILD_TOOLS.json").write_text(
        json.dumps({"NSIS": NSIS_VERSION, "source": NSIS_URL, "sha256": NSIS_SHA256}, indent=2),
        encoding="utf-8",
    )
    print(f"Instalador gerado: {output / ('EcoDeck-' + __version__ + '-setup.exe')}")


if __name__ == "__main__":
    main()
