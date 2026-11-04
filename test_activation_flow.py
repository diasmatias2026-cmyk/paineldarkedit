import sys,tempfile,threading,json,os
from pathlib import Path
from unittest.mock import patch
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'commercial/editor'))
import editor
from licensing import License,ActivationHandler
with tempfile.TemporaryDirectory() as d:
    license=License(d);ActivationHandler.license=license
    server=editor.LocalServer(('127.0.0.1',0),ActivationHandler);editor.ORIGIN='http://127.0.0.1:'+str(server.server_port)
    editor.LICENSE_CHECK=license.require
    threading.Thread(target=server.serve_forever,daemon=True).start()
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,*args):return b'{"allowed":true}'
    try:
        with sync_playwright() as p,patch('urllib.request.urlopen',return_value=Response()):
            browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(editor.ORIGIN)
            assert page.locator('#activation').is_visible()
            blocked=page.request.post(editor.ORIGIN+'/start',data={},headers={'X-Editor-Token':editor.TOKEN})
            assert blocked.status==403
            csrf=page.request.post(editor.ORIGIN+'/activate',data={'email':'test@example.invalid'})
            assert csrf.status==403
            malformed=page.request.post(editor.ORIGIN+'/activate',data=[],headers={'X-Editor-Token':editor.TOKEN})
            assert malformed.status==400
            page.locator('#email').fill('test@example.invalid');page.locator('#activate').click()
            page.locator('#files').wait_for(state='visible');assert license.active
            assert page.request.post(editor.ORIGIN+'/status',data={},headers={'X-Editor-Token':editor.TOKEN}).json()['version']=='1.2.1'
            def revoked():raise ValueError('Licença revogada no teste.')
            editor.LICENSE_CHECK=revoked
            blocked=page.request.post(editor.ORIGIN+'/start',data={},headers={'X-Editor-Token':editor.TOKEN})
            assert blocked.status==400 and 'revogada' in blocked.json()['error']
            assert not errors,errors
            page.screenshot(path=str(root/'activation-editor.png'),full_page=True)
            browser.close()
        print('PASS: activation UI; blocked editor before activation; CSRF; malformed request; licensed editor; revoked export denied')
    finally:server.shutdown();server.server_close()
