@echo off
rem Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
cd /d "%~dp0"
if exist "dist\CrashSounds\CrashSounds.exe" (
    start "" "dist\CrashSounds\CrashSounds.exe"
    exit /b 0
)
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" -m ecodeck
    exit /b 0
)
echo Instale o app seguindo o README.md ou baixe o ZIP em Releases.
pause
exit /b 1
