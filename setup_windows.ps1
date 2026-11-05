# Installs the Knight's Fusion script and tests the check scripts. Safe to run again.
# Written for Windows PowerShell 5.1, which every supported Windows includes. Start it with setup_windows.cmd.

foreach ($candidate in "py -3", "python3", "python") {
    $parts = $candidate -split " "
    $executable = $parts[0]
    $launcherArgs = @($parts | Select-Object -Skip 1)
    if (-not (Get-Command $executable -ErrorAction SilentlyContinue)) { continue }

    # The Microsoft Store's python.exe placeholder is found above, but it fails here.
    & $executable @launcherArgs --version *> $null
    if ($LASTEXITCODE -ne 0) { continue }

    & $executable @launcherArgs -B (Join-Path $PSScriptRoot "setup_fusion.py")
    exit $LASTEXITCODE
}

Write-Host "Python 3 is required. Install it from https://www.python.org/downloads/ and run this again."
exit 1
