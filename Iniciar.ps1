$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$candidates = @(
    (Join-Path $PSScriptRoot ".venv\Scripts\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python314\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe")
)
$taskPython = $null
foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate) { $taskPython = $candidate; break }
}
if (-not $taskPython) {
    Write-Host "Python não localizado. Instale Python 3.11 ou superior e execute novamente."
    exit 1
}
Write-Host "Interpretador: $taskPython"
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot ".venv\Scripts\python.exe"))) {
    & $taskPython -m venv (Join-Path $PSScriptRoot ".venv")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
$taskPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Write-Host "Abra http://127.0.0.1:8000 após a mensagem do servidor."
& $taskPython -X utf8 main.py serve
exit $LASTEXITCODE
