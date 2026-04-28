#define MyAppName "VmPOS"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "VmPOS"
#define MyAppExeName "VmPOS.exe"

[Setup]
AppId={{C1A4A34E-0E4D-4C4D-B0FA-6AC12A427C1E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\VmPOS
DefaultGroupName=VmPOS
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist_installer
OutputBaseFilename=VmPOS_instalador
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\VmPOS\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion createallsubdirs
Source: "..\database\license_remote.example.json"; DestDir: "{app}\database"; DestName: "license_remote.json"; Flags: onlyifdoesntexist
Source: "..\reset_datos_cliente.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\VmPOS"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\VmPOS"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir VmPOS"; Flags: nowait postinstall skipifsilent
