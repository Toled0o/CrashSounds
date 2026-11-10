# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Teste instalador/portátil sem gravar no Desktop, Run ou perfil pessoal."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\EcoDeck"


def snapshot_registry():
    import winreg

    result = []
    for key, name in (
        (RUN_KEY, "CrashSounds"),
        (RUN_KEY, "EcoDeck"),
        (UNINSTALL_KEY, "InstallLocation"),
    ):
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            ) as handle:
                result.append(winreg.QueryValueEx(handle, name))
        except FileNotFoundError:
            result.append(None)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    before = snapshot_registry()
    with tempfile.TemporaryDirectory(prefix="ecodeck-installer-qa-") as temporary:
        root = Path(temporary)
        installed = root / "Installed CrashSounds"
        # NSIS exige /D por último e sem aspas, mesmo com espaços. Usar
        # CreateProcess diretamente (shell=False), sem interpretação por shell.
        command = subprocess.list2cmdline([str(args.installer.resolve()), "/S", "/QA"])
        command += f" /D={installed}"
        environment = dict(os.environ, ECODECK_INSTALLER_QA_DIR=str(installed))
        subprocess.run(command, check=True, timeout=120, env=environment)
        assert (installed / "CrashSounds.exe").is_file(), "Extração não gerou o executável."
        assert (installed / "assets" / "CrashSounds.ico").is_file()
        assert (installed / ".ecodeck-installer-qa").is_file()
        subprocess.run([str(installed / "CrashSounds.exe"), "--smoke-test"], check=True, timeout=60)
        sentinel = installed / "arquivo-do-usuario.txt"
        sentinel.write_text("Não apagar na desinstalação.", encoding="utf-8")
        subprocess.run([str(installed / "Desinstalar.exe"), "/S"], check=True, timeout=60)
        deadline = time.monotonic() + 30
        while (installed / "CrashSounds.exe").exists() or (installed / "Desinstalar.exe").exists():
            if time.monotonic() > deadline:
                raise TimeoutError("Desinstalação não concluiu.")
            time.sleep(0.1)
        assert sentinel.read_text(encoding="utf-8") == "Não apagar na desinstalação."
        assert not (installed / "_internal").exists(), "Bibliotecas não removidas."
        desktop = root / "Desktop QA"
        desktop.mkdir()
        package = args.package.resolve()
        subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(package / "criar-atalho.ps1"),
                "-DesktopDirectory",
                str(desktop),
            ],
            check=True,
            timeout=30,
        )
        # Ler o link criado no diretório de QA, sem abrir o aplicativo.
        reader = root / "read-link.ps1"
        reader.write_text(
            "param([string]$Link)\n"
            "$shell = New-Object -ComObject WScript.Shell\n"
            "$shortcut = $shell.CreateShortcut($Link)\n"
            "@{Target=$shortcut.TargetPath; Icon=$shortcut.IconLocation; "
            "WorkingDirectory=$shortcut.WorkingDirectory} | ConvertTo-Json -Compress\n",
            encoding="utf-8-sig",
        )
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(reader),
                str(desktop / "CrashSounds.lnk"),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        shortcut = json.loads(result.stdout)
        assert Path(shortcut["Target"]) == package / "CrashSounds.exe"
        assert Path(shortcut["WorkingDirectory"]) == package
        assert str(package / "assets" / "CrashSounds.ico") in shortcut["Icon"]
    assert snapshot_registry() == before, "QA alterou integração do usuário."
    print("Instalação QA, EXE instalado, desinstalação e atalho portátil: OK.")


if __name__ == "__main__":
    main()
