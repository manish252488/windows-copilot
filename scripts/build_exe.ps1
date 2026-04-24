param(
    [string]$AppName = "Jarvis",
    [string]$Version = "0.1.0"
)

python -m PyInstaller `
  --noconfirm `
  --windowed `
  --name "$AppName-$Version" `
  --add-data ".env.example;." `
  main.py

Write-Host "Executable created in dist/$AppName-$Version"
