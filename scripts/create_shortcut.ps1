<#
Creates a desktop shortcut to launch the visualizer with no console window
and the app's hexagon icon.

Prefers dist\CaseDisplayVisualizer.exe (built via scripts\build_exe.ps1) --
a real standalone .exe whose icon is correct everywhere (taskbar, Alt-Tab,
Explorer, Start menu) because it's baked into the .exe itself. Falls back
to launching from source via the venv's pythonw.exe if the .exe hasn't
been built yet -- that works too, but Windows will show the taskbar icon
for the running window as a generic Python icon (a Windows/Explorer
limitation for un-compiled Python GUI apps, not something the app can fix
at runtime).

Run from anywhere:
    powershell -ExecutionPolicy Bypass -File scripts\create_shortcut.ps1

Re-run any time (e.g. after moving the project folder, or after building
the .exe for the first time) to refresh the shortcut's target.
#>

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ExePath = Join-Path $ProjectRoot "dist\CaseDisplayVisualizer.exe"
$PythonwExe = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$IconPath = Join-Path $ProjectRoot "assets\app_icon.ico"
$ShortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Case Display Visualizer.lnk"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)

if (Test-Path $ExePath) {
    Write-Output "Using standalone exe: $ExePath"
    $Shortcut.TargetPath = $ExePath
    $Shortcut.Arguments = ""
    $Shortcut.WorkingDirectory = Split-Path -Parent $ExePath
    $Shortcut.IconLocation = $ExePath
} else {
    if (-not (Test-Path $PythonwExe)) {
        Write-Error "Neither dist\CaseDisplayVisualizer.exe nor the venv's pythonw.exe were found. Build the exe (scripts\build_exe.ps1) or create the venv first (see README Setup)."
        exit 1
    }
    if (-not (Test-Path $IconPath)) {
        Write-Error "Icon not found at $IconPath -- run scripts\generate_icon.py first."
        exit 1
    }
    Write-Output "dist\CaseDisplayVisualizer.exe not built yet -- falling back to source + pythonw.exe."
    Write-Output "(Taskbar icon will show as generic Python; build the exe for a correct one.)"
    $Shortcut.TargetPath = $PythonwExe
    $Shortcut.Arguments = "-m case_display_visualizer"
    $Shortcut.WorkingDirectory = $ProjectRoot
    $Shortcut.IconLocation = $IconPath
}

$Shortcut.Description = "Case Display Visualizer"
$Shortcut.Save()

Write-Output "Created shortcut: $ShortcutPath"
