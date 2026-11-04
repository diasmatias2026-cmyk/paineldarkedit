from pathlib import Path
import os,subprocess,sys
ROOT=Path(__file__).resolve().parent
OLD=Path('D:/DOC 3.11/Codex/2026-11-02/vam/work')
SOURCE=ROOT/'commercial/editor';DIST=ROOT/'releases/windows'
for name in ['index.html']:
    f=SOURCE/name;f.write_text(f.read_text(encoding='utf-8').replace('1.1.1','1.2.1'),encoding='utf-8')
env=os.environ.copy();env['PYTHONPATH']=str(OLD/'darkedit-build314/Lib/site-packages');env['PYINSTALLER_CONFIG_DIR']=str(ROOT/'build/cache')
args=[str(OLD/'python314/python.exe'),'-m','PyInstaller','--noconfirm','--onedir','--windowed','--name','DarkEdit','--exclude-module','numpy','--exclude-module','cryptography','--distpath',str(DIST),'--workpath',str(ROOT/'build/pyinstaller'),'--specpath',str(ROOT/'build'),'--paths',str(SOURCE),'--collect-all','webview','--icon',str(SOURCE/'assets/darkedit.ico')]
for f in SOURCE.iterdir():
    if f.is_file() and f.suffix in ['.html','.js','.css','.txt']:args+=['--add-data',str(f)+';.']
args+=['--add-data',str(SOURCE/'assets')+';assets','--add-binary',str(SOURCE/'tools/ffmpeg.exe')+';tools',str(SOURCE/'desktop.py')]
(ROOT/'build').mkdir(exist_ok=True)
with (ROOT/'build/pyinstaller.log').open('w',encoding='utf-8') as log:r=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT)
if r.returncode:
    print((ROOT/'build/pyinstaller.log').read_text(encoding='utf-8')[-2500:]);sys.exit(r.returncode)
iss='''[Setup]
AppId={{9A09CE90-86D4-48A0-BF8D-6F7AB7C3C865}
AppName=DarkEdit
AppVersion=1.2.1
AppPublisher=DarkEdit
DefaultDirName={localappdata}\\Programs\\DarkEdit
DefaultGroupName=DarkEdit
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=OUTPUT
OutputBaseFilename=DarkEdit-Setup-1.2.1-x64
SetupIconFile=ICON
UninstallDisplayIcon={app}\\DarkEdit.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
AppMutex=Local\\DarkEditCommercialInstalled
[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\\BrazilianPortuguese.isl"
[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"
[Files]
Source: "BUNDLE\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\\DarkEdit"; Filename: "{app}\\DarkEdit.exe"
Name: "{autodesktop}\\DarkEdit"; Filename: "{app}\\DarkEdit.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\\DarkEdit.exe"; Description: "Abrir DarkEdit"; Flags: nowait postinstall skipifsilent
'''.replace('OUTPUT',str(DIST)).replace('ICON',str(SOURCE/'assets/darkedit.ico')).replace('BUNDLE',str(DIST/'DarkEdit'))
file=ROOT/'build/DarkEdit.iss';file.write_text(iss,encoding='utf-8-sig')
with (ROOT/'build/installer.log').open('w',encoding='utf-8') as log:r=subprocess.run([str(OLD/'inno-compiler/ISCC.exe'),str(file)],stdout=log,stderr=subprocess.STDOUT)
if r.returncode:print((ROOT/'build/installer.log').read_text(encoding='utf-8')[-1800:]);sys.exit(r.returncode)
file=DIST/'DarkEdit-Setup-1.2.1-x64.exe';print('Installer:',file.stat().st_size,'bytes');assert file.stat().st_size<52428800,'Installer exceeds free Storage limit'
