; Inno Setup Script for Contracto v4.5.18
; Professional Windows Installer (ADR 0008)

[Setup]
AppName=Contracto
AppVersion=4.5.18
AppPublisher=Nickolas-Costa
AppPublisherURL=https://github.com/Nickolas-Costa/Contracto
AppSupportURL=https://github.com/Nickolas-Costa/Contracto/issues
AppUpdatesURL=https://github.com/Nickolas-Costa/Contracto/issues
DefaultDirName={autopf}\Contracto
DefaultGroupName=Contracto
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Contracto_Installer_v4.5.18
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\app\dist\Contracto_v4.5.18.exe"; DestDir: "{app}"; DestName: "Contracto.exe"; Flags: ignoreversion
Source: "..\app\assets\gs\*"; DestDir: "{app}\assets\gs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\app\assets\config\*"; DestDir: "{app}\assets\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\app\assets\templates\*"; DestDir: "{app}\assets\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\app\assets\icons\*"; DestDir: "{app}\assets\icons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\frontend\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Contracto"; Filename: "{app}\Contracto.exe"; IconFilename: "{app}\assets\icons\app_icon.ico"
Name: "{group}\{cm:UninstallProgram,Contracto}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Contracto"; Filename: "{app}\Contracto.exe"; IconFilename: "{app}\assets\icons\app_icon.ico"; Tasks: desktopicon

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
