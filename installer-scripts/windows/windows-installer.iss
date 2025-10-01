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
UninstallDisplayName=Koncentro
AppVersion={#GetEnv('KONCENTRO_VERSION')}
AppPublisher=Bishwa Saha
AppPublisherURL=https://github.com/kun-codes/Koncentro/
AppSupportURL=https://github.com/kun-codes/Koncentro/discussions
AppUpdatesURL=https://github.com/kun-codes/Koncentro/releases
DefaultDirName={userpf}\Koncentro
DefaultGroupName=Koncentro
SetupIconFile=assets\logo.ico
UninstallDisplayIcon={app}\koncentro.exe
PrivilegesRequired=lowest
LicenseFile=.\artifacts\LICENSE.txt
SourceDir=..\..
OutputDir=dist
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"
Name: "autostart"; Description: "Launch Flowkeeper when the system boots"; GroupDescription: "Additional icons:"

[Files]
Source: ".\artifacts\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Koncentro"; Filename: "{app}\koncentro.exe"
Name: "{userdesktop}\Koncentro"; Filename: "{app}\koncentro.exe"; Tasks: desktopicon
Name: "{userstartup}\Koncentro"; Parameters: "--autostart"; Filename: "{app}\koncentro.exe"; Tasks: autostart

[Run]
Filename: "{app}\koncentro.exe"; Description: "Launch Koncentro"; Flags: nowait postinstall skipifsilent

; delete __pycache__ directories on uninstall to not leave Koncentro folder in install location
[Code]
procedure DeletePycacheFolders(const Directory: string);
var
  FindRec: TFindRec;
  SearchPath: string;
begin
  SearchPath := AddBackslash(Directory) + '*';

  if FindFirst(SearchPath, FindRec) then
  begin
    try
      repeat
        if (FindRec.Name <> '.') and (FindRec.Name <> '..') then
        begin
          if (FindRec.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0 then
          begin
            if CompareText(FindRec.Name, '__pycache__') = 0 then
            begin
              // Delete the __pycache__ folder recursively
              DelTree(AddBackslash(Directory) + FindRec.Name, True, True, True);
            end
            else
            begin
              // Recursively search in subdirectories
              DeletePycacheFolders(AddBackslash(Directory) + FindRec.Name);
            end;
          end;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;

  // Delete all __pycache__ folders recursively before uninstallation
  try
    DeletePycacheFolders(ExpandConstant('{app}'));
  except
    // If deletion fails, continue with uninstallation anyway
    Log('Warning: Failed to delete some __pycache__ folders');
  end;
end;