; Inno Setup Script for Contracto
; Professional Windows Installer (ADR 0008)

#define MyAppName "Contracto"
#define MyAppVersion GetFileVersion("..\app\dist\Contracto_v" + GetVersionString("..\app\version.py") + ".exe")

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Nickolas-Costa
AppPublisherURL=https://github.com/Nickolas-Costa/Contracto
AppSupportURL=https://github.com/Nickolas-Costa/Contracto/issues
AppUpdatesURL=https://github.com/Nickolas-Costa/Contracto/issues
DefaultDirName={autopf}\Contracto
DefaultGroupName=Contracto
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Contracto_Installer_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
AppId=Contracto
AppMutex=ContractoMutex
CreateAppDir=yes
UninstallDisplayName={#MyAppName}

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\app\dist\Contracto_v{#MyAppVersion}.exe"; DestDir: "{app}"; DestName: "Contracto.exe"; Flags: ignoreversion
Source: "..\app\assets\gs\*"; DestDir: "{app}\assets\gs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\app\assets\config\*"; DestDir: "{app}\assets\config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\app\assets\templates\*"; DestDir: "{app}\assets\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\app\assets\icons\*"; DestDir: "{app}\assets\icons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\frontend\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Contracto"; Filename: "{app}\Contracto.exe"; IconFilename: "{app}\assets\icons\app_icon.ico"
Name: "{group}\{cm:UninstallProgram,Contracto}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Contracto"; Filename: "{app}\Contracto.exe"; IconFilename: "{app}\assets\icons\app_icon.ico"; Tasks: desktopicon

[Run]
Filename: "{sys}\cmd.exe"; Parameters: "/c reg query HKLM\\SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5} /v pv"; Flags: skipifdoesntexist unchecked waituntilterminated hidden; Check: not IsWebView2Installed

[Code]
function IsWebView2Installed(): Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    // O shell do app exige WebView2 no Windows. O instalador apenas orienta;
    // a validação final de runtime segue feita pelo próprio aplicativo.
  end;
end;
