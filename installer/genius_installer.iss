; Inno Setup script to package the Genius Windows tray assistant

#define DefaultAppDir "..\\dist\\app\\Genius"
#ifndef AppDir
#define AppDir DefaultAppDir
#endif

#define DefaultOutputDir "..\\dist\\installer"
#ifndef InstallerOutputDir
#define InstallerOutputDir DefaultOutputDir
#endif

#ifndef AppVersion
#define AppVersion "1.0.0"
#endif

[Setup]
AppId={{A8D17218-1E50-4787-9B03-52AA337A6F5C}}
AppName=Genius
AppVersion={#AppVersion}
AppPublisher=Don-Quixote De La Mancha 2025 3LL3 LLC
AppPublisherURL=https://3ll3.example.com
DefaultDirName={autopf}\\Genius
DefaultGroupName=Genius
DisableDirPage=no
DisableProgramGroupPage=no
AllowNoIcons=yes
OutputBaseFilename=GeniusSetup-{#AppVersion}
OutputDir={#InstallerOutputDir}
SetupIconFile={#AppDir}\\genius.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
LicenseFile={#AppDir}\\docs\\LICENSE.txt
InfoBeforeFile={#AppDir}\\docs\\README.md

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "runatstartup"; Description: "Launch Genius automatically when I sign in"

[Files]
Source: "{#AppDir}\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#AppDir}\\config\\genius_config.yaml"; DestDir: "{userappdata}\\Genius"; DestName: "genius_config.yaml"; Flags: onlyifdestfilemissing uninsneveruninstall

[Dirs]
Name: "{userappdata}\\Genius"; Flags: uninsalwaysuninstall

[Icons]
Name: "{group}\\Genius"; Filename: "{app}\\Genius.exe"; WorkingDir: "{app}"
Name: "{commondesktop}\\Genius"; Filename: "{app}\\Genius.exe"; Tasks: desktopicon; WorkingDir: "{app}"
Name: "{userstartup}\\Genius"; Filename: "{app}\\Genius.exe"; Tasks: runatstartup; WorkingDir: "{app}"

[Run]
Filename: "{app}\\Genius.exe"; Description: "Launch Genius"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\\Genius"
