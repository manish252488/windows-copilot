param(
    [string]$Version = "0.1.0",
    [string]$AppName = "Jarvis"
)

if (-not (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue)) {
    throw "Inno Setup compiler (ISCC.exe) not found in PATH."
}

$exeName = "$AppName-$Version"
if (-not (Test-Path "dist/$exeName/$exeName.exe")) {
    throw "Build the executable first: ./scripts/build_exe.ps1 -Version $Version"
}

ISCC.exe "/DMyAppVersion=$Version" "/DMyExeName=$exeName.exe" "installer/jarvis_installer.iss"
Write-Host "Installer created in installer/output"
