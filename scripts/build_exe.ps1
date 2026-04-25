param(
    [string]$AppName = "Jarvis-Assistant",
    [string]$Version = "1.0.0"
)

python -m PyInstaller `
  --noconfirm `
  --windowed `
  --name "$AppName" `
  --add-data ".env.example;." `
  main.py

Write-Host "Executable created in dist/$AppName"
