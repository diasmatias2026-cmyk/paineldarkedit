from pathlib import Path
import os,subprocess,time,json,urllib.request,urllib.error,hashlib,zipfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
EMAIL='qa.darkedit.20261103@example.invalid'
BASE='https://idsesxzabyswkfmtgjen.supabase.co'
ENDPOINT=BASE+'/functions/v1/darkedit-members'
def api(action,email=EMAIL):
    r=urllib.request.Request(ENDPOINT,data=json.dumps({'email':email,'action':action}).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(r,timeout=30) as result:return json.load(result)
assert api('list')['allowed']
for action in ['installer','extension']:
    data=api(action);assert data['url'].startswith(BASE+'/storage/v1/object/sign/darkedit-downloads/')
    with urllib.request.urlopen(urllib.request.Request(data['url'],method='HEAD'),timeout=30) as response:assert int(response.headers['Content-Length'])>1000
try:urllib.request.urlopen(BASE+'/storage/v1/object/public/darkedit-downloads/windows/DarkEdit-Setup-1.2.1-x64.exe');raise AssertionError('public bucket')
except urllib.error.HTTPError as e:assert e.code in [400,403,404]
installer=ROOT/'releases/windows/DarkEdit-Setup-1.2.1-x64.exe'
installed=ROOT/'build/installed'
r=subprocess.run([str(installer),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/TASKS=','/DIR='+str(installed),'/LOG='+str(ROOT/'build/install-test.log')],timeout=180)
assert r.returncode==0
env=os.environ.copy();data=ROOT/'build/native-user';env['DARKEDIT_DATA_DIR']=str(data)
exe=installed/'DarkEdit.exe';report=ROOT/'build/installed-smoke.json'
subprocess.run([str(exe),'--self-test',str(report)],env=env,check=True,timeout=90)
assert json.loads(report.read_text())['ok']
log=data/'desktop.log';log.unlink(missing_ok=True)
process=subprocess.Popen([str(exe)],env=env,creationflags=subprocess.CREATE_NO_WINDOW)
try:
    for i in range(80):
        if log.exists() and 'Starting http://' in log.read_text():break
        time.sleep(.25)
    url=log.read_text().splitlines()[0].replace('Starting ','')
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page()
        page.goto(url)
        if page.locator('#email').count():page.locator('#email').fill(EMAIL);page.locator('#activate').click()
        page.locator('#files').wait_for(state='visible',timeout=35000)
        page.locator('#media').set_input_files(str(ROOT/'build/darkedit-smoke/source.png'))
        page.get_by_text('source.png',exact=False).first.wait_for(state='visible',timeout=20000)
        page.screenshot(path=str(ROOT/'activation-native.png'),full_page=True)
        browser.close()
    assert 'WebView loaded' in log.read_text(), 'Native webview failed'
    print('PASS: signed download links; private bucket; silent installer; installed render; real HTTPS activation; native WebView loaded; media imported')
finally:
    process.terminate();process.wait(timeout=20)
