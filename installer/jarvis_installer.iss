#define MyAppName "Jarvis Assistant"
#define MyAppPublisher "Manish Singh"
#define MyStableExeName "Jarvis-Assistant.exe"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#ifndef MyExeName
  #define MyExeName MyStableExeName
#endif
#ifndef MyBuildDir
  #define MyBuildDir "Jarvis-Assistant"
#endif

[Setup]
AppId={{18D3F35A-0E5C-4D35-B918-C44A4A019908}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=output
OutputBaseFilename=Jarvis-Assistant-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyExeName}
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\dist\{#MyBuildDir}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
