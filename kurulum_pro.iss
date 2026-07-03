; Muzik Indirici PRO v1.31 - Inno Setup kurulum betigi
[Setup]
AppId={{7E4A2B91-53C8-4F0D-9A61-1A2B3C4D5E6F}
AppName=Muzik Indirici PRO
AppVersion=1.31
AppPublisher=V™
DefaultDirName={localappdata}\MuzikIndirici
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=C:\MuzikIndirici\kurulum
OutputBaseFilename=MuzikIndiriciPro_Kurulum
SetupIconFile=C:\MuzikIndirici\varliklar\logo.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\MuzikIndiriciPro.exe

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; Eski (v1.0) surumden kalanlari temizle
Type: files; Name: "{app}\MuzikIndirici.exe"
Type: files; Name: "{autodesktop}\Muzik Indirici.lnk"
Type: files; Name: "{autoprograms}\Muzik Indirici.lnk"

[Files]
Source: "C:\MuzikIndirici\dist\MuzikIndiriciPro.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\MuzikIndirici\ffmpeg\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe"; DestDir: "{app}\ffmpeg"; Flags: ignoreversion
Source: "C:\MuzikIndirici\ffmpeg\ffmpeg-8.1.2-essentials_build\bin\ffprobe.exe"; DestDir: "{app}\ffmpeg"; Flags: ignoreversion
Source: "C:\MuzikIndirici\sarkilar.txt"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "C:\MuzikIndirici\KULLANIM.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Muzik Indirici PRO"; Filename: "{app}\MuzikIndiriciPro.exe"
Name: "{autodesktop}\Muzik Indirici PRO"; Filename: "{app}\MuzikIndiriciPro.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\MuzikIndiriciPro.exe"; Description: "{cm:LaunchProgram,Muzik Indirici PRO}"; Flags: nowait postinstall skipifsilent
