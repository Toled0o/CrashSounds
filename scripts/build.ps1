# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Crie .venv e instale .[dev] antes de gerar o executável. Veja README.md.'
}
& $projectPython (Join-Path $PSScriptRoot 'build.py')
exit $LASTEXITCODE
