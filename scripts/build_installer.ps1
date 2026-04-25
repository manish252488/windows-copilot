param(
    [string]$Version = "1.0.0",
    [string]$AppName = "Jarvis-Assistant"
)

if (-not (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue)) {
    throw "Inno Setup compiler (ISCC.exe) not found in PATH."
}

$exeName = "$AppName.exe"
if (-not (Test-Path "dist/$AppName/$exeName")) {
    throw "Build the executable first: ./scripts/build_exe.ps1 -Version $Version"
}

ISCC.exe "/DMyAppVersion=$Version" "/DMyExeName=$exeName" "/DMyBuildDir=$AppName" "installer/jarvis_installer.iss"
Write-Host "Installer created in installer/output"
