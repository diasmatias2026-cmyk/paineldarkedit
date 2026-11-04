from pathlib import Path
import hashlib,zipfile
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parent
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page(viewport={'width':390,'height':850});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    response=page.goto('https://darkedit-vendas.vercel.app/obrigado/');assert response.status==200
    assert page.locator('a[href="/downloads/"]').count()==1
    page.locator('a[href="/downloads/"]').click()
    page.locator('#purchase-email').fill('naocomprou@example.invalid');page.locator('#access-button').click()
    expect(page.locator('#access-status')).to_contain_text('Não encontramos',timeout=25000)
    assert page.locator('#downloads-panel').is_hidden()
    page.locator('#purchase-email').fill('qa.darkedit.20261103@example.invalid');page.locator('#access-button').click()
    page.locator('#downloads-panel').wait_for(state='visible',timeout=25000)
    with page.expect_download(timeout=30000) as download:
        page.locator('[data-download="extension"]').click()
    file=ROOT/'build/bonus-browser.zip';download.value.save_as(file)
    assert hashlib.sha256(file.read_bytes()).digest()==hashlib.sha256((ROOT/'releases/bonus/DarkDownload-0.6.0.zip').read_bytes()).digest()
    with zipfile.ZipFile(file) as z:assert 'manifest.json' in z.namelist()
    page.screenshot(path=str(ROOT/'build/public-downloads-mobile.png'),full_page=True)
    assert not errors,errors
    browser.close()
print('PASS: public thank-you -> downloads; real unlicensed denial; approved email; signed ZIP download matches release; no JS errors')
