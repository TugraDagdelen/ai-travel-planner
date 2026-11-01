$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot 'backend'
$frontendRoot = Join-Path $projectRoot 'frontend'
$pythonPath = Join-Path $backendRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Backend virtual environment is missing. Follow README.tr.md setup first.'
}
if (-not (Test-Path -LiteralPath (Join-Path $frontendRoot 'node_modules'))) {
    throw 'Frontend dependencies are missing. Run npm ci in frontend first.'
}

& $pythonPath (Join-Path $PSScriptRoot 'check_repository.py')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location $backendRoot
try {
    & $pythonPath -m ruff check app tests
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $pythonPath -m pytest -q -p no:cacheprovider
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $pythonPath -m pip check
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally { Pop-Location }

Push-Location $frontendRoot
try {
    foreach ($script in @('typecheck', 'lint', 'test', 'build')) {
        & npm.cmd run $script
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}
finally { Pop-Location }

Write-Host 'All offline application checks passed.' -ForegroundColor Green
