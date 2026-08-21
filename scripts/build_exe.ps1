<#
Builds a standalone, double-clickable CaseDisplayVisualizer.exe with the
hexagon icon baked in as a proper PE resource -- this is what makes the
taskbar icon correct (a raw pythonw.exe process can't reliably do that;
see PACKAGING.md for why).

Requires pyinstaller in the venv: .venv\Scripts\pip install pyinstaller

Run from anywhere:
    powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1

Output: dist\CaseDisplayVisualizer.exe (self-contained, no Python needed
to run it). config.local.toml/themes.local.toml are read from and written
next to whatever directory the .exe is run from.
#>

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PyInstaller = Join-Path $ProjectRoot ".venv\Scripts\pyinstaller.exe"
$Icon = Join-Path $ProjectRoot "assets\app_icon.ico"
$Entry = Join-Path $ProjectRoot "cdv\__main__.py"
$ConfigToml = Join-Path $ProjectRoot "config.toml"

if (-not (Test-Path $PyInstaller)) {
    Write-Error "pyinstaller not found in the venv -- run: .venv\Scripts\pip install pyinstaller"
    exit 1
}

& $PyInstaller `
    --name "CaseDisplayVisualizer" `
    --onefile `
    --windowed `
    --icon $Icon `
    --add-data "$ConfigToml;." `
    --distpath (Join-Path $ProjectRoot "dist") `
    --workpath (Join-Path $ProjectRoot "build") `
    --specpath (Join-Path $ProjectRoot "build") `
    --noconfirm `
    $Entry

if ($LASTEXITCODE -eq 0) {
    Write-Output ""
    Write-Output "Built: $ProjectRoot\dist\CaseDisplayVisualizer.exe"
}
