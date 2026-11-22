[Setup]
AppName=CORE Browser
AppVersion=1.1
AppPublisher=CORE
DefaultDirName={autopf}\CORE Browser
DefaultGroupName=CORE Browser
OutputDir=dist
OutputBaseFilename=CORE-Browser-Win11-Setup
SetupIconFile=core_icon.ico
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\CORE-Browser-Win11\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CORE Browser"; Filename: "{app}\CORE-Browser-Win11.exe"; IconFilename: "{app}\core_icon.ico"
Name: "{autodesktop}\CORE Browser"; Filename: "{app}\CORE-Browser-Win11.exe"; IconFilename: "{app}\core_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\CORE-Browser-Win11.exe"; Description: "Launch CORE Browser"; Flags: nowait postinstall skipifsilent
