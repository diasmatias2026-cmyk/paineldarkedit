"""Upload private releases using a short-lived administrator session."""
import getpass,json,urllib.request,urllib.error,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE='https://idsesxzabyswkfmtgjen.supabase.co'
KEY='sb_publishable_naugzCz2j0cCJQTN09j7Qg_F2Z26QGr'
def request(path,method='GET',data=None,token=None,mime='application/json'):
    headers={'apikey':KEY,'Content-Type':mime}
    if token:headers['Authorization']='Bearer '+token
    with urllib.request.urlopen(urllib.request.Request(BASE+path,data=data,headers=headers,method=method),timeout=180) as r:return r.read()
password=getpass.getpass('Senha administrativa (nao sera salva): ')
try:auth=json.loads(request('/auth/v1/token?grant_type=password','POST',json.dumps({'email':'diasmatias2026@gmail.com','password':password}).encode()))
except urllib.error.HTTPError as e:raise SystemExit('Falha no login administrativo: HTTP '+str(e.code))
password=None;token=auth['access_token'];auth=None
manifest={}
try:
    for kind,path,mime in [('windows',ROOT/'releases/windows/DarkEdit-Setup-1.2.1-x64.exe','application/octet-stream'),('bonus',ROOT/'releases/bonus/DarkDownload-0.6.0.zip','application/zip')]:
        data=path.read_bytes();assert len(data)<52428800
        object_path=kind+'/'+path.name
        try:request('/storage/v1/object/darkedit-downloads/'+object_path,'POST',data,token,mime)
        except urllib.error.HTTPError as e:
            if e.code not in [400,409]:raise
            existing=request('/storage/v1/object/authenticated/darkedit-downloads/'+object_path,token=token)
            if hashlib.sha256(existing).digest()!=hashlib.sha256(data).digest():raise RuntimeError('A versao publicada tem conteudo diferente; publique nova versao.')
        manifest[object_path]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        print('Publicado em bucket privado:',path.name,flush=True)
    (ROOT/'releases/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
finally:
    try:request('/auth/v1/logout','POST',b'{}',token)
    except OSError:pass
    token=None
print('Upload concluido; sessao administrativa encerrada.')
