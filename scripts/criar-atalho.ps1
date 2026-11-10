# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
param(
    [string]$DesktopDirectory = [Environment]::GetFolderPath('DesktopDirectory')
)
$ErrorActionPreference = 'Stop'
$applicationPath = Join-Path $PSScriptRoot 'CrashSounds.exe'
$iconPath = Join-Path $PSScriptRoot 'assets\CrashSounds.ico'
if (-not (Test-Path -LiteralPath $applicationPath -PathType Leaf)) {
    throw 'Extraia toda a pasta do ZIP e mantenha este script junto de CrashSounds.exe.'
}
if (-not (Test-Path -LiteralPath $iconPath -PathType Leaf)) {
    throw 'Icone ausente. Extraia novamente o pacote completo.'
}
if (-not (Test-Path -LiteralPath $DesktopDirectory -PathType Container)) {
    throw 'Pasta da Area de Trabalho nao encontrada.'
}
$shortcutPath = Join-Path $DesktopDirectory 'CrashSounds.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $applicationPath
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = 'CrashSounds - seu som, na hora certa'
$shortcut.Save()
Write-Host "Atalho criado: $shortcutPath"
Write-Host 'Mantenha a pasta do aplicativo no mesmo lugar para o atalho continuar funcionando.'
