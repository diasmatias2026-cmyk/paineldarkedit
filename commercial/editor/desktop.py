"""DarkEdit desktop entry point, including an offline packaged smoke test."""
import sys,os,json,threading,traceback,ctypes
from pathlib import Path
import editor
from engine import DATA_ROOT,ROOT,DEFAULT,overlay,run

def self_test(report_path):
    from PIL import Image
    from auto_render import choose_encoder
    directory=Path(report_path).resolve().parent/'darkedit-smoke'
    directory.mkdir(parents=True,exist_ok=True)
    source=directory/'source.png';Image.new('RGB',(480,640),'#399568').save(source)
    c={**DEFAULT,'seconds':1,'template':str(ROOT/'assets'/'starter-template.png'),'erase_placeholder':True}
    art=directory/'art.png';overlay(c).save(art)
    encoder=choose_encoder(source,art,c,directory);c['_encoder']=encoder
    output=directory/'export.mp4';output.unlink(missing_ok=True)
    run(source,output,art,c,directory/'render.log')
    result={'ok':output.is_file(),'selected':encoder,'render':c['_render_info'],'output':str(output),'resources':str(ROOT),'data':str(DATA_ROOT)}
    Path(report_path).write_text(json.dumps(result,indent=2),encoding='utf-8')

if __name__=='__main__':
    try:
        DATA_ROOT.mkdir(parents=True,exist_ok=True)
        if '--self-test' in sys.argv:
            self_test(sys.argv[sys.argv.index('--self-test')+1]);sys.exit(0)
        mutex=ctypes.windll.kernel32.CreateMutexW(None,False,'Local\\DarkEditCommercialInstalled')
        if ctypes.windll.kernel32.GetLastError()==183:
            hwnd=ctypes.windll.user32.FindWindowW(None,'DarkEdit')
            if hwnd:ctypes.windll.user32.ShowWindow(hwnd,9);ctypes.windll.user32.SetForegroundWindow(hwnd)
            sys.exit(0)
        import webview
        from runtime import install_job_guard,terminate_all
        install_job_guard()
        from licensing import License, ActivationHandler
        license=License(DATA_ROOT)
        license.restore()
        editor.LICENSE_CHECK=license.require
        ActivationHandler.license=license
        server=editor.LocalServer(('127.0.0.1',0),ActivationHandler)
        editor.ORIGIN='http://127.0.0.1:'+str(server.server_port)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        log=DATA_ROOT/'desktop.log'
        log.write_text('Starting '+editor.ORIGIN+'\n',encoding='utf-8')
        window=webview.create_window('DarkEdit',editor.ORIGIN,width=1420,height=900,min_size=(1024,700),background_color='#0b0f14')
        def pick_folder():
            selected=window.create_file_dialog(webview.FileDialog.FOLDER)
            return selected[0] if selected else None
        def completed():
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            window.restore()
        editor.PICK_FOLDER=pick_folder;editor.NOTICE=completed
        def loaded():
            with log.open('a',encoding='utf-8') as stream:stream.write('WebView loaded\n')
        window.events.loaded+=loaded
        try:webview.start(gui='edgechromium',debug=False,storage_path=str(DATA_ROOT/'WebView'))
        finally:
            editor.CANCEL.set()
            terminate_all()
            server.shutdown();server.server_close()
            ctypes.windll.kernel32.CloseHandle(mutex)
    except Exception:
        error=traceback.format_exc()
        try:(DATA_ROOT/'error.log').write_text(error,encoding='utf-8')
        except OSError:pass
        if '--self-test' not in sys.argv:ctypes.windll.user32.MessageBoxW(None,'Não foi possível abrir o DarkEdit. Consulte '+str(DATA_ROOT/'error.log'),'DarkEdit',16)
        sys.exit(1)
