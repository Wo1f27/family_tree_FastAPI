; Inno Setup script for Family Tree - Updated

[Setup]
AppName=Family Tree
AppVersion={{VERSION}}
DefaultDirName={pf}\FamilyTree
DefaultGroupName=Family Tree
OutputDir=installer-output
OutputBaseFilename=family_tree_setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "family_tree.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "family_tree_web.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Family Tree"; Filename: "{app}\family_tree.exe"
Name: "{group}\Open Web Interface"; Filename: "{app}\family_tree_web.exe"
Name: "{userdesktop}\Family Tree"; Filename: "{app}\family_tree.exe"
Name: "{userdesktop}\Open Web Interface"; Filename: "{app}\family_tree_web.exe"

[Run]
Filename: "{app}\family_tree.exe"; Description: "Launch Family Tree"; Flags: nowait postinstall skipifsilent
