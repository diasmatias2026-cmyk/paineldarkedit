from pathlib import Path
import json,urllib.request,urllib.error,re,subprocess
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
BASE='https://idsesxzabyswkfmtgjen.supabase.co'
request=urllib.request.Request(BASE+'/functions/v1/darkedit-members',data=json.dumps({'email':'diasmatias2026@gmail.com','action':'installer'}).encode(),headers={'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(request,timeout=30) as response:data=json.load(response)
assert data['filename']=='DarkEdit-Setup-1.2.1-x64.exe'
with urllib.request.urlopen(urllib.request.Request(data['url'],method='HEAD'),timeout=30) as response:assert int(response.headers['Content-Length'])==(ROOT/'releases/windows'/data['filename']).stat().st_size
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
    response=page.goto('https://darkedit-vendas.vercel.app/');assert response.status==200
    for link in page.locator('a[href^="https://wa.me/"]').all():assert link.get_attribute('href').split('?')[0]=='https://wa.me/5534999929764'
    assert page.locator('a[href="/downloads/"]').count()>0
    page.goto('https://darkedit-vendas.vercel.app/obrigado/');assert page.locator('a[href="/downloads/"]').count()==1
    page.goto('https://darkedit-vendas.vercel.app/downloads/');assert page.locator('#access-form').is_visible()
    browser.close()
native=(ROOT/'releases/windows/DarkEdit/_internal/activation.html').read_text(encoding='utf-8')
assert 'https://wa.me/5534999929764' in native and '55349999929764' not in native
installer=ROOT/'releases/windows/DarkEdit-Setup-1.2.1-x64.exe';installed=ROOT/'build/installed-121'
subprocess.run([str(installer),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/TASKS=','/DIR='+str(installed)],timeout=120,check=True)
report=ROOT/'build/installed-121-smoke.json'
subprocess.run([str(installed/'DarkEdit.exe'),'--self-test',str(report)],timeout=90,check=True)
assert json.loads(report.read_text())['ok']
print('PASS: public pages; WhatsApp exact; private signed installer 1.2.1; download size; installed 1.2.1 render')

uninstaller=installed/'unins000.exe'
assert uninstaller.resolve().is_relative_to((ROOT/'build').resolve())
subprocess.run([str(uninstaller),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],check=True,timeout=90)
