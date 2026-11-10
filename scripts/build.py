# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Build Windows onedir: DLLs substituíveis e avisos de terceiros preservados."""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    if sys.platform != "win32":
        raise SystemExit("Execute o build em Windows x64 com Python 3.11–3.13.")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    output = args.output.resolve()
    build = output.parent / "build"
    build.mkdir(parents=True, exist_ok=True)
    # Não limpa diretórios informados pelo usuário; PyInstaller atualiza apenas seu pacote.
    from PySide6.QtWidgets import QApplication

    from ecodeck.visuals import app_icon

    app = QApplication.instance() or QApplication([])
    icon = build / "EcoDeck.ico"
    if not app_icon().pixmap(128, 128).save(str(icon), "ICO"):
        raise OSError("Falha ao criar ícone.")
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--onedir",
            "--windowed",
            "--name",
            "EcoDeck",
            "--icon",
            str(icon),
            "--distpath",
            str(output),
            "--workpath",
            str(build / "pyinstaller"),
            "--specpath",
            str(build),
            "--paths",
            str(ROOT / "src"),
            "--collect-all",
            "sounddevice",
            "--collect-all",
            "soundfile",
            "--collect-all",
            "soxr",
            str(ROOT / "src" / "ecodeck" / "__main__.py"),
        ]
    )
    package = output / "EcoDeck"
    for name in ("LICENSE", "README.md", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md"):
        shutil.copy2(ROOT / name, package / name)
    shutil.copytree(ROOT / "docs", package / "docs", dirs_exist_ok=True)
    shutil.copytree(ROOT / "assets", package / "assets", dirs_exist_ok=True)
    shutil.copytree(ROOT / "licenses", package / "licenses", dirs_exist_ok=True)
    versions = {}
    # Copiar avisos inclusive de dependências transitivas e do runtime.
    names = (
        "PySide6-Essentials",
        "shiboken6",
        "numpy",
        "sounddevice",
        "soundfile",
        "soxr",
        "cffi",
        "pycparser",
        "pyinstaller",
    )
    for name in names:
        distribution = metadata.distribution(name)
        versions[name] = distribution.version
        for file in distribution.files or []:
            lower = str(file).lower()
            if any(token in lower for token in ("license", "copying", "copyright", "notice")):
                source = Path(distribution.locate_file(file))
                if source.is_file():
                    # Caminho achatado e prefixado; não permitir ../ da metadata.
                    target = (
                        package
                        / "licenses"
                        / name
                        / str(file).replace("..", "_").replace("/", "__").replace("\\", "__")
                    )
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    import soundfile as sf

    versions["libsndfile"] = sf.__libsndfile_version__
    versions["python"] = sys.version
    for name in ("LICENSE.txt", "LICENSE"):
        python_license = Path(sys.base_prefix) / name
        if python_license.is_file():
            shutil.copy2(python_license, package / "licenses" / "PYTHON-LICENSE.txt")
    (package / "DEPENDENCIES.json").write_text(json.dumps(versions, indent=2), encoding="utf-8")
    # O subprocesso só usa QA: sem biblioteca real, captura, reprodução ou atalhos.
    run([str(package / "EcoDeck.exe"), "--smoke-test"])
    archive = shutil.make_archive(str(output / "EcoDeck-windows-x64"), "zip", output, "EcoDeck")
    print(f"Build e smoke concluídos: {archive}")
    # Manter QApplication vivo até o fim da criação do ícone.
    del app


if __name__ == "__main__":
    main()
