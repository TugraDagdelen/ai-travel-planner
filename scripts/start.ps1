$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendRoot = Join-Path $projectRoot 'backend'
$frontendRoot = Join-Path $projectRoot 'frontend'
$pythonPath = Join-Path $backendRoot '.venv\Scripts\python.exe'
$vitePath = Join-Path $frontendRoot 'node_modules\vite\bin\vite.js'

if (-not (Test-Path -LiteralPath $pythonPath) -or -not (Test-Path -LiteralPath $vitePath)) {
    throw 'Install dependencies using README.tr.md before starting the application.'
}

foreach ($port in @(8000, 5173)) {
    $portProbe = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
    try { $portProbe.Start() }
    catch { throw "Port $port is already in use. Stop the existing application first." }
    finally { $portProbe.Stop() }
}

$backendProcess = $null
$frontendProcess = $null
try {
    $backendProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru
    $nodePath = (Get-Command node -ErrorAction Stop).Source
    $frontendProcess = Start-Process -FilePath $nodePath -ArgumentList @(('"' + $vitePath + '"'), '--configLoader', 'native', '--host', '127.0.0.1', '--port', '5173', '--strictPort') -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru
    Write-Host 'Rota: http://127.0.0.1:5173/'
    Write-Host 'API:  http://127.0.0.1:8000/docs'
    Write-Host 'Stop both services with Ctrl+C. / Durdurmak icin Ctrl+C.'
    while (-not $backendProcess.HasExited -and -not $frontendProcess.HasExited) {
        Start-Sleep -Seconds 1
        $backendProcess.Refresh()
        $frontendProcess.Refresh()
    }
    throw 'A service stopped. Use the manual README commands to see its error output.'
}
finally {
    foreach ($ownedProcess in @($backendProcess, $frontendProcess)) {
        if ($null -ne $ownedProcess -and -not $ownedProcess.HasExited) {
            $ownedProcess.Kill()
            $ownedProcess.WaitForExit()
        }
    }
}
