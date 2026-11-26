# scripts/runTests.ps1
<#
.SYNOPSIS
    Run the Riah Code test suite with the CUDA-enabled virtual environment.

.DESCRIPTION
    The project keeps a dedicated `.venv` with a CUDA build of PyTorch. The
    global Python interpreter is CPU-only, so running `pytest` directly skips
    every GPU test. This script always prefers `.venv` and lets you select the
    suite to execute.

.PARAMETER Suite
    all (default), unit, integration, gpu or fast.

.PARAMETER RequireGpu
    Turn skipped GPU tests into a hard failure when CUDA is unavailable.

.EXAMPLE
    ./scripts/runTests.ps1 -Suite unit
    ./scripts/runTests.ps1 -Suite integration -RequireGpu
#>
param(
    [ValidateSet("all", "unit", "integration", "gpu", "fast")]
    [string]$Suite = "all",
    [switch]$RequireGpu
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $python = $venvPython
}
else {
    Write-Warning ".venv not found; falling back to the global python (GPU tests will be skipped)."
    $python = "python"
}

$pytestArgs = @("-m", "pytest")

switch ($Suite) {
    "all" { $pytestArgs += @("tests") }
    "unit" { $pytestArgs += @("tests/unit") }
    "integration" { $pytestArgs += @("tests/integration") }
    "gpu" { $pytestArgs += @("tests", "-m", "gpu") }
    "fast" { $pytestArgs += @("tests", "-m", "not slow and not gpu") }
}

if ($RequireGpu) {
    $pytestArgs += "--require-gpu"
}

Write-Host "Running suite '$Suite' with $python" -ForegroundColor Cyan
& $python @pytestArgs
exit $LASTEXITCODE
