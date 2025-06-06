;
; Inno Setup Installer Script for Koncentro
; Based on original installer script from Flowkeeper by Constantine Kulak
; https://github.com/kulakowka/flowkeeper
;
; Copyright (c) 2023 Constantine Kulak
; Modifications Copyright (c) 2025 Bishwa Saha
;
; This file is part of Koncentro.
;
; This program is free software: you can redistribute it and/or modify
; it under the terms of the GNU General Public License as published by
; the Free Software Foundation; either version 3 of the License, or
; (at your option) any later version.
;
; This program is distributed in the hope that it will be useful,
; but WITHOUT ANY WARRANTY; without even the implied warranty of
; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
; GNU General Public License for more details.
;
; You should have received a copy of the GNU General Public License
; along with this program.  If not, see <https://www.gnu.org/licenses/>.
;

[Setup]
AppName=Koncentro
AppVersion={#GetEnv('KONCENTRO_VERSION')}
AppPublisher=Bishwa Saha
AppPublisherURL=https://github.com/kun-codes/Koncentro/
AppSupportURL=https://github.com/kun-codes/Koncentro/discussions
AppUpdatesURL=https://github.com/kun-codes/Koncentro/releases
DefaultDirName={userpf}\Koncentro
DefaultGroupName=Koncentro
SetupIconFile=assets\logo.ico
PrivilegesRequired=lowest
SourceDir=..\..
OutputDir=dist

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"
Name: "autostart"; Description: "Launch Flowkeeper when the system boots"; GroupDescription: "Additional icons:"

[Files]
Source: "artifacts\"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Koncentro"; Filename: "{app}\koncentro.exe"
Name: "{userdesktop}\Koncentro"; Filename: "{app}\koncentro.exe"; Tasks: desktopicon
Name: "{userstartup}\Koncentro"; Parameters: "--autostart"; Filename: "{app}\koncentro.exe"; Tasks: autostart

[Run]
Filename: "{app}\koncentro.exe"; Description: "Launch Koncentro"; Flags: nowait postinstall skipifsilent