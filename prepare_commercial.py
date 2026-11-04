from pathlib import Path
import shutil
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parent
source=Path('D:/DOC 3.11/Codex/2026-11-02/vam/outputs/sistema-local-unificado/editor')
target=root/'commercial/editor';target.mkdir(parents=True,exist_ok=True)
for f in source.iterdir():
    if f.is_file() and f.suffix in ['.py','.js','.html','.css','.txt']:
        text=f.read_text(encoding='utf-8-sig').replace('momento-novela.png','starter-template.png').replace('Momento Novela — Canva','Modelo de exemplo DarkEdit').replace('Restaurar template Canva','Restaurar modelo de exemplo').replace("'1.1.1'","'1.2.1'").replace('DarkEditLocalInstalled','DarkEditCommercialInstalled').replace("/'DarkEditLocal'","/'DarkEditCommercial'")
        (target/f.name).write_text(text,encoding='utf-8')
for directory in ['assets','tools']:(target/directory).mkdir(exist_ok=True)
shutil.copy2(source/'tools/ffmpeg.exe',target/'tools/ffmpeg.exe')
shutil.copy2(source/'assets/darkedit.ico',target/'assets/darkedit.ico')
art=Image.new('RGB',(1080,1920),'white');draw=ImageDraw.Draw(art)
font=lambda size:ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',size)
draw.rounded_rectangle((70,290,200,420),30,fill='#101714');draw.text((103,318),'D.',font=font(63),fill='#63e4ad')
draw.text((230,310),'Seu perfil',font=font(52),fill='#101714');draw.text((230,378),'@suamarca',font=font(36),fill='#677568')
draw.text((70,500),'Seu conteúdo.',font=font(64),fill='#101714');draw.text((70,582),'Sua identidade.',font=font(64),fill='#101714')
draw.rounded_rectangle((70,750,1010,1520),48,fill=(241,241,244))
draw.text((220,1090),'SUA CENA AQUI',font=font(62),fill='#9aa49b')
draw.text((300,1710),'CRIADO COM DARKEDIT',font=font(34),fill='#21865f')
art.save(target/'assets/starter-template.png')
f=target/'editor.py';s=f.read_text(encoding='utf-8');s=s.replace('NOTICE=None','NOTICE=None\nLICENSE_CHECK=None');s=s.replace("elif path == '/start':","elif path == '/start':\n                if LICENSE_CHECK:LICENSE_CHECK()")
f.write_text(s,encoding='utf-8')
f=target/'desktop.py';s=f.read_text(encoding='utf-8');s=s.replace('server=editor.LocalServer',"from licensing import License, ActivationHandler\n        license=License(DATA_ROOT)\n        license.restore()\n        editor.LICENSE_CHECK=license.require\n        ActivationHandler.license=license\n        server=editor.LocalServer").replace("('127.0.0.1',0),editor.Handler)","('127.0.0.1',0),ActivationHandler)")
f.write_text(s,encoding='utf-8')
print('Fonte comercial isolada e template genérico preparados.')
