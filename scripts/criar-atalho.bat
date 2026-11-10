@echo off
rem Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0criar-atalho.ps1"
if errorlevel 1 (
    echo Nao foi possivel criar o atalho. Confira a mensagem acima.
    pause
    exit /b 1
)
echo Pronto. Abra o EcoDeck pelo atalho na Area de Trabalho.
pause
