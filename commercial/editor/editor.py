"""Loopback-only editor. Uploads and rendering remain on this computer."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime
import json
import secrets
import threading
import webbrowser
import io
import re
import shutil
import os
from runtime import terminate_all
from media_validation import inspect,normalize_asset
from engine import ROOT, DATA_ROOT, DEFAULT, config, overlay, run, detect_template_window, detect_scene_crop

TOKEN = secrets.token_urlsafe(32)
SESSION = DATA_ROOT / 'sessoes' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
UPLOADS = {}
if (ROOT / 'assets' / 'starter-template.png').is_file():
    UPLOADS['canva-template'] = dict(path=ROOT / 'assets' / 'starter-template.png', name='Modelo de exemplo DarkEdit', kind='asset')
STATE = {'version':'1.2.1', 'busy': False, 'message': 'Adicione mídias para começar.', 'results': [], 'current': 0, 'total': 0}
LOCK = threading.Lock()
CANCEL = threading.Event()
PROCESS = None
ORIGIN = ''

def settings(raw):
    c = config({**DEFAULT, **{k: v for k, v in raw.items() if k in DEFAULT and k not in ['template', 'avatar']}})
    for key in ['template', 'avatar']:
        item = UPLOADS.get(raw.get(key))
        c[key] = str(item['path']) if item and item['kind'] == 'asset' else ''
    return c

def render_batch(ids, c, titles=None, frames=None):
    import time,shutil
    from auto_render import choose_encoder,LABELS
    job=secrets.token_hex(8);work=DATA_ROOT/'jobs'/job;work.mkdir(parents=True,exist_ok=False)
    target=OUTPUT_DIR or DATA_ROOT/'exportados';target.mkdir(parents=True,exist_ok=True)
    report=[];titles=titles or {};frames=frames or {};started=time.monotonic();done_seconds=0
    durations=[c['seconds'] if UPLOADS[i].get('meta',{}).get('image') else UPLOADS[i].get('meta',{}).get('duration',0) for i in ids]
    total_seconds=sum(durations);render_started=None
    try:
        with LOCK:STATE.update(batch_id=job,message='Comparando CPU e GPUs…',progress=0,eta_seconds=None,elapsed_seconds=0,folder=str(target))
        first=config({**c,**frames.get(ids[0],{})});art=work/'benchmark.png';overlay(first).save(art)
        encoder=choose_encoder(UPLOADS[ids[0]]['path'],art,first,work,CANCEL.is_set);c['_encoder']=encoder
        render_started=time.monotonic()
        with LOCK:STATE['renderer']=LABELS[encoder]
        for index,identity in enumerate(ids):
            if CANCEL.is_set():break
            item=UPLOADS[identity];duration=durations[index]
            stem=re.sub(r'[^\w-]','_',Path(item['name']).stem)[:65] or 'video'
            output=target/(stem+'_DarkEdit.mp4');counter=1
            while output.exists():output=target/(stem+f'_DarkEdit_{counter}.mp4');counter+=1
            item_config=config({**c,**frames.get(identity,{}),'title':titles.get(identity,c['title'])})
            artwork=work/f'template_{index}.png';overlay(item_config).save(artwork)
            with LOCK:STATE.update(current=index+1,message=f'Exportando {index+1}/{len(ids)}: {item["name"]}')
            def update(seconds):
                elapsed=time.monotonic()-render_started;processed=done_seconds+min(duration,seconds) if duration else done_seconds
                rate=processed/max(.1,elapsed)
                eta=(total_seconds-processed)/rate if rate>0 and elapsed>1 else None
                with LOCK:STATE.update(progress=round(min(99,processed/max(1,total_seconds)*100),1),eta_seconds=round(max(0,eta)) if eta is not None else None,elapsed_seconds=round(time.monotonic()-started))
            def remember(process):
                global PROCESS
                PROCESS=process
                if CANCEL.is_set():process.terminate()
            try:
                run(item['path'],output,artwork,item_config,work/f'{index}.log',remember,CANCEL.is_set,update)
                report.append({'source':item['name'],'output':str(output),'status':'concluido','render':item_config.get('_render_info',{}),'frame':{k:item_config[k] for k in FRAME_KEYS}})
            except Exception as error:report.append({'source':item['name'],'status':'cancelado' if CANCEL.is_set() else 'falhou','error':str(error)[:200]})
            finally:PROCESS=None
            done_seconds+=duration
            with LOCK:STATE['results']=list(report)
        success=sum(r['status']=='concluido' for r in report)
        with LOCK:STATE.update(message=f'{"Cancelado" if CANCEL.is_set() else "Finalizado"}: {success}/{len(ids)} vídeos exportados.',progress=100 if not CANCEL.is_set() else STATE.get('progress',0),eta_seconds=0,elapsed_seconds=round(time.monotonic()-started),completion_id=job,cancelled=CANCEL.is_set())
    except Exception as error:
        with LOCK:STATE.update(message='Não foi possível concluir: '+str(error)[:180],completion_id=job,cancelled=CANCEL.is_set(),eta_seconds=0)
    finally:
        (work/'relatorio.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        with LOCK:STATE.update(busy=False,results=report)
        if NOTICE and not CANCEL.is_set():
            try:NOTICE()
            except Exception:pass

FRAME_KEYS=['x','y','width','height','radius','zoom','shift_x','shift_y','crop_top','crop_bottom','crop_left','crop_right']
OUTPUT_DIR=None
PICK_FOLDER=None
NOTICE=None
LICENSE_CHECK=None
PREVIEW_SLOTS=threading.BoundedSemaphore(2)
PROJECT_LOCK=threading.Lock()
UPLOAD_GATE=threading.BoundedSemaphore(1)

def save_project(data):
    if not isinstance(data.get('items'),list) or len(data['items'])>200:raise ValueError('Projeto inválido.')
    ids=[item.get('id') for item in data['items'] if isinstance(item,dict)]
    if any(i not in UPLOADS for i in ids):raise ValueError('A mídia não está disponível nesta sessão.')
    snapshot={'data':data,'uploads':{i:{**UPLOADS[i],'path':str(UPLOADS[i]['path'])} for i in UPLOADS if i!='canva-template'}}
    DATA_ROOT.mkdir(parents=True,exist_ok=True)
    with PROJECT_LOCK:
        temporary=DATA_ROOT/'project.tmp';temporary.write_text(json.dumps(snapshot,ensure_ascii=False),encoding='utf-8');temporary.replace(DATA_ROOT/'project.json')

def restore_project():
    try:
        file=DATA_ROOT/'project.json'
        if not file.is_file() or file.stat().st_size>2000000:return None
        snapshot=json.loads(file.read_text(encoding='utf-8'));restored={}
        for identity,item in snapshot.get('uploads',{}).items():
            path=Path(item['path']).resolve()
            if re.fullmatch(r'[a-f0-9]{24}',identity) and path.is_relative_to((DATA_ROOT/'sessoes').resolve()) and path.is_file():restored[identity]={**item,'path':path}
        UPLOADS.update(restored)
        data=snapshot['data'];data['items']=[i for i in data.get('items',[]) if i.get('id') in restored]
        return data
    except (OSError,ValueError,KeyError,TypeError):return None

class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup();self.connection.settimeout(30)

    def log_message(self, *args): pass

    def response(self, status, data, content_type='application/json'):
        payload = json.dumps(data, ensure_ascii=False).encode() if content_type == 'application/json' else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; media-src 'self' blob:; frame-ancestors 'none'")
        if urlparse(self.path).path=='/' and 'html' in content_type:self.send_header('Set-Cookie','DarkEditSession='+TOKEN+'; HttpOnly; SameSite=Strict; Path=/')
        try:self.end_headers();self.wfile.write(payload)
        except (ConnectionError,OSError):pass

    def allowed(self, post=False):
        if self.headers.get('Host') != ORIGIN.removeprefix('http://'):
            self.response(403, {'error': 'Host não permitido.'}); return False
        if self.headers.get('Origin') not in [None, ORIGIN]:
            self.response(403, {'error': 'Origem não permitida.'}); return False
        if post and not secrets.compare_digest(self.headers.get('X-Editor-Token', ''), TOKEN):
            self.response(403, {'error': 'Sessão inválida. Reabra o editor.'}); return False
        return True

    def do_GET(self):
        if not self.allowed(): return
        path = urlparse(self.path).path
        files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'), '/style.css': ('style.css', 'text/css; charset=utf-8'), '/template-default.png':('assets/starter-template.png','image/png')}
        if path.startswith('/media/'):
            from http.cookies import SimpleCookie
            cookie=SimpleCookie(self.headers.get('Cookie',''));value=cookie.get('DarkEditSession')
            if not value or not secrets.compare_digest(value.value,TOKEN):self.response(403,{'error':'Sessão inválida.'});return
            item=UPLOADS.get(path.split('/')[-1])
            if not item:self.response(404,{'error':'Arquivo não disponível.'});return
            file=item['path'];size=file.stat().st_size;start=0;end=size-1
            raw_range=self.headers.get('Range','')
            if raw_range:
                match=re.fullmatch(r'bytes=(\d+)-(\d*)',raw_range)
                if not match:self.response(416,{'error':'Intervalo inválido.'});return
                start=int(match[1]);end=min(size-1,int(match[2]) if match[2] else size-1)
                if start>end:self.response(416,{'error':'Intervalo inválido.'});return
            import mimetypes
            self.send_response(206 if raw_range else 200);self.send_header('Content-Type',mimetypes.guess_type(file.name)[0] or 'application/octet-stream');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
            if raw_range:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
            self.end_headers()
            try:
                with file.open('rb') as stream:
                    stream.seek(start);remaining=end-start+1
                    while remaining:
                        chunk=stream.read(min(remaining,1024**2))
                        if not chunk:break
                        self.wfile.write(chunk);remaining-=len(chunk)
            except (ConnectionError,OSError):pass
            return
        if path in files:
            name, kind = files[path]
            data = (ROOT / name).read_bytes().replace(b'__SESSION_TOKEN__', TOKEN.encode())
            self.response(200, data, kind)
        else: self.response(404, {'error': 'Não encontrado.'})

    def do_POST(self):
        global OUTPUT_DIR
        if not self.allowed(post=True): return
        path = urlparse(self.path).path
        acquired_upload=False
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 0: raise ValueError('Tamanho inválido.')
            if path == '/upload':
                if not UPLOAD_GATE.acquire(blocking=False):raise ValueError('Aguarde a validação do arquivo anterior.')
                acquired_upload=True
                if STATE['busy']:raise ValueError('Aguarde a exportação para alterar o lote.')
                if len([i for i in UPLOADS.values() if i['kind']=='media'])>=200:raise ValueError('Limite de 200 arquivos por projeto. Remova arquivos para adicionar outros.')
                used=sum(i['path'].stat().st_size for i in UPLOADS.values() if i['path'].is_file())
                if used+length>10*1024**3 or shutil.disk_usage(DATA_ROOT if DATA_ROOT.exists() else ROOT).free<length+512*1024**2:raise ValueError('Limite de cache ou espaço livre insuficiente. Remova arquivos do projeto.')
                if not 0 < length <= 2 * 1024**3: raise ValueError('Arquivo deve ter entre 1 byte e 2 GB.')
                name = Path(unquote(self.headers.get('X-File-Name', 'midia'))).name
                suffix = Path(name).suffix.lower()
                if suffix not in ['.mp4', '.mov', '.mkv', '.webm', '.jpg', '.jpeg', '.png', '.webp', '.bmp']: raise ValueError('Formato não suportado.')
                kind = self.headers.get('X-File-Kind', 'media')
                if kind not in ['asset', 'media']: raise ValueError('Tipo inválido.')
                if kind == 'asset' and suffix not in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']: raise ValueError('Template/avatar precisa ser uma imagem.')
                identity = secrets.token_hex(12)
                SESSION.mkdir(parents=True, exist_ok=True)
                destination = SESSION / (identity + suffix)
                remaining = length
                self.connection.settimeout(120)
                try:
                    with destination.open('xb') as stream:
                        while remaining:
                            chunk = self.rfile.read(min(1024**2, remaining))
                            if not chunk: raise ValueError('Arquivo incompleto.')
                            stream.write(chunk); remaining -= len(chunk)
                except Exception:
                    destination.unlink(missing_ok=True); raise
                try:
                    meta=inspect(destination)
                    if kind=='asset':
                        safe=normalize_asset(destination);destination.unlink();destination=safe
                except Exception:
                    destination.unlink(missing_ok=True);raise
                UPLOADS[identity] = dict(path=destination, name=name, kind=kind,meta=meta)
                region = detect_template_window(destination) if kind == 'asset' else None
                self.response(200, {'id': identity, 'name': name, 'window': region, 'meta':meta})
                return
            if length > 100000: raise ValueError('Configuração grande demais.')
            raw = self.rfile.read(length)
            data = json.loads(raw or b'{}')
            if not isinstance(data, dict): raise ValueError('Dados inválidos.')
            if path == '/choose-output':
                if STATE['busy']:raise ValueError('A exportação já está em andamento.')
                selected=PICK_FOLDER() if PICK_FOLDER else str(DATA_ROOT/'exportados')
                if selected:OUTPUT_DIR=Path(selected).resolve();OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
                self.response(200,{'folder':str(OUTPUT_DIR) if selected else None})
            elif path == '/open-output':
                folder=Path(STATE.get('folder') or OUTPUT_DIR or DATA_ROOT/'exportados')
                if not folder.is_dir():raise ValueError('A pasta ainda não está disponível.')
                if os.name=='nt':os.startfile(str(folder))
                self.response(200,{'ok':True})
            elif path == '/project-save':
                if STATE['busy']:self.response(200,{'ok':True});return
                save_project(data);self.response(200,{'ok':True})
            elif path == '/project-load':
                self.response(200,{'project':restore_project()})
            elif path == '/remove-media':
                if STATE['busy']:raise ValueError('Aguarde ou cancele a exportação.')
                identity=data.get('id');item=UPLOADS.get(identity)
                if item and identity!='canva-template':
                    path_to_remove=item['path'].resolve()
                    if path_to_remove.is_relative_to((DATA_ROOT/'sessoes').resolve()):path_to_remove.unlink(missing_ok=True)
                    UPLOADS.pop(identity,None)
                self.response(200,{'ok':True})
            elif path == '/detect-crop':
                item=UPLOADS.get(data.get('id'))
                if not item or item['kind']!='media': raise ValueError('Selecione uma mídia enviada nesta sessão.')
                self.response(200,detect_scene_crop(item['path']))
            elif path == '/preview':
                if not PREVIEW_SLOTS.acquire(timeout=2):raise ValueError('Aguarde o carregamento da prévia.')
                try:image=overlay(settings(data))
                finally:PREVIEW_SLOTS.release()
                from PIL import Image
                canvas = image if data.get('transparent') else Image.new('RGBA', image.size, '#283330')
                if not data.get('transparent'): canvas.alpha_composite(image)
                canvas.thumbnail((432, 768))
                buf = io.BytesIO(); canvas.save(buf, format='PNG')
                self.response(200, buf.getvalue(), 'image/png')
            elif path == '/start':
                if LICENSE_CHECK:LICENSE_CHECK()
                if OUTPUT_DIR is None:raise ValueError('Escolha a pasta para salvar os vídeos.')
                if not isinstance(data.get('config',{}),dict):raise ValueError('Configuração inválida.')
                c = settings(data.get('config', {}))
                overlay(c)  # Validate artwork before starting.
                ids = data.get('ids', [])
                if not isinstance(ids, list) or not 1 <= len(ids) <= 200 or any(i not in UPLOADS or UPLOADS[i]['kind'] != 'media' for i in ids): raise ValueError('Selecione entre 1 e 200 mídias enviadas nesta sessão.')
                raw_titles = data.get('titles', {})
                if not isinstance(raw_titles, dict): raise ValueError('Chamadas individuais inválidas.')
                titles = {identity: str(raw_titles[identity])[:160] for identity in ids if identity in raw_titles and raw_titles[identity]}
                for title in set(titles.values()): overlay({**c, 'title': title})
                raw_frames = data.get('frames', {})
                if not isinstance(raw_frames, dict): raise ValueError('Enquadramentos inválidos.')
                keys = ['x','y','width','height','radius','zoom','shift_x','shift_y','crop_top','crop_bottom','crop_left','crop_right']
                frames = {}
                for identity in ids:
                    if identity in raw_frames:
                        if not isinstance(raw_frames[identity],dict): raise ValueError('Enquadramento inválido.')
                        frame = {k:v for k,v in raw_frames[identity].items() if k in keys}
                        overlay(config({**c, **frame}))
                        frames[identity] = frame
                with LOCK:
                    if STATE['busy']: raise ValueError('Já existe um lote em andamento.')
                    CANCEL.clear(); STATE.update(busy=True,completion_id=None,renderer=None,progress=0,eta_seconds=None,results=[], current=0, total=len(ids), message='Preparando lote…', folder='')
                threading.Thread(target=render_batch, args=(ids, c, titles, frames), daemon=True).start()
                self.response(200, {'ok': True})
            elif path == '/status':
                with LOCK: snapshot = dict(STATE)
                self.response(200, snapshot)
            elif path == '/cancel':
                CANCEL.set();terminate_all()
                self.response(200, {'ok': True})
            else: self.response(404, {'error': 'Ação não encontrada.'})
        except (ValueError,RuntimeError,TimeoutError) as e:self.response(400,{'error':str(e)[:220]})
        except Exception:self.response(400,{'error':'Não foi possível concluir a operação. Verifique o arquivo e tente novamente.'})
        finally:
            if acquired_upload:UPLOAD_GATE.release()

if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    ORIGIN = 'http://127.0.0.1:' + str(server.server_port)
    print('Editor local: ' + ORIGIN, flush=True)
    print('Mantenha esta janela aberta. Ctrl+C encerra o editor.', flush=True)
    webbrowser.open(ORIGIN)
    try: server.serve_forever()
    except KeyboardInterrupt:
        CANCEL.set()
        if PROCESS and PROCESS.poll() is None: PROCESS.terminate()
        server.server_close()

class LocalServer(ThreadingHTTPServer):
    slots=threading.BoundedSemaphore(16)
    def process_request(self,request,address):
        if not self.slots.acquire(blocking=False):self.shutdown_request(request);return
        try:super().process_request(request,address)
        except Exception:self.slots.release();raise
    def process_request_thread(self,request,address):
        try:super().process_request_thread(request,address)
        finally:self.slots.release()
