import json,threading,functools
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',5190),functools.partial(Quiet,directory=str(ROOT/'vendas')))
threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        endpoint='**/functions/v1/darkedit-members'
        def denied(route):route.fulfill(status=403,json={'error':'access_not_available'},headers={'Access-Control-Allow-Origin':'*'})
        page.route(endpoint,denied)
        page.goto('http://127.0.0.1:5190/downloads/');page.locator('#purchase-email').fill('semcompra@example.invalid');page.locator('#access-button').click()
        page.wait_for_function("document.querySelector('#access-status').textContent.includes('Não encontramos')")
        assert page.locator('#downloads-panel').is_hidden()
        page.unroute(endpoint)
        def allowed(route):
            data=route.request.post_data_json
            if data['action']=='list':route.fulfill(json={'allowed':True,'downloads':[]},headers={'Access-Control-Allow-Origin':'*'})
            else:route.fulfill(json={'url':'https://evil.example/download','filename':'bad.exe'},headers={'Access-Control-Allow-Origin':'*'})
        page.route(endpoint,allowed);page.locator('#access-button').click();page.locator('#downloads-panel').wait_for(state='visible')
        page.locator('[data-download="installer"]').click()
        page.wait_for_function("document.querySelector('#access-status').textContent.includes('não é válido')")
        page.locator('#change-email').click();assert page.locator('#access-form-panel').is_visible()
        for width in [1440,768,390]:
            page.set_viewport_size({'width':width,'height':900});page.reload();page.wait_for_timeout(250)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.screenshot(path=str(ROOT/f'members-{width}.png'),full_page=True)
        page.emulate_media(reduced_motion='reduce');assert not errors,errors
        browser.close()
    print('PASS: email denied; permitted view; unsafe URL blocked; change email; responsive 1440/768/390; no JS errors')
finally:server.shutdown()
