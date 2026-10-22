#ifndef AppVersion
  #error AppVersion is required
#endif
[Setup]
AppId={{59E3AE12-9564-4E1D-A4ED-BE83778BC120}
AppName=Folio
AppVersion={#AppVersion}
AppPublisher=Folio
AppPublisherURL=https://github.com/antoniorasulo89/folio
AppSupportURL=https://github.com/antoniorasulo89/folio/issues
DefaultDirName={localappdata}\Programs\Folio
DefaultGroupName=Folio
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename=Folio-Windows-Setup
SetupIconFile={#RepoRoot}\assets\folio.ico
UninstallDisplayIcon={app}\Folio.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "Crea un collegamento sul desktop"; Flags: unchecked
[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Folio"; Filename: "{app}\Folio.exe"
Name: "{autodesktop}\Folio"; Filename: "{app}\Folio.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\Folio.exe"; Description: "Avvia Folio"; Flags: nowait postinstall skipifsilent
