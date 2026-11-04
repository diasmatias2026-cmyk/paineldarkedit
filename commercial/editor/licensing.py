"""Email entitlement with Windows DPAPI credentials and server device binding."""
import ctypes,json,secrets,hashlib,os,re,threading,urllib.request,urllib.error,winreg
from pathlib import Path
from urllib.parse import urlparse
import editor
ENDPOINT='https://idsesxzabyswkfmtgjen.supabase.co/functions/v1/darkedit-members'
class Blob(ctypes.Structure):
    _fields_=[('size',ctypes.c_ulong),('data',ctypes.POINTER(ctypes.c_ubyte))]
def protect(data,decode=False):
    buf=ctypes.create_string_buffer(data);source=Blob(len(data),ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
    api=ctypes.WinDLL('crypt32',use_last_error=True)
    fn=api.CryptUnprotectData if decode else api.CryptProtectData
    fn.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(Blob)];fn.restype=ctypes.c_int
    if not fn(ctypes.byref(source),None,None,None,None,1,ctypes.byref(out)):raise OSError('Não foi possível proteger os dados de ativação neste Windows.')
    try:return ctypes.string_at(out.data,out.size)
    finally:
        kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p;kernel.LocalFree(out.data)
def machine_hash():
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\Cryptography',0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:value=winreg.QueryValueEx(key,'MachineGuid')[0]
    return hashlib.sha256(('DarkEdit-v1:'+str(value)).encode()).hexdigest()
class License:
    def __init__(self,directory):
        self.path=Path(directory)/'activation.bin';self.lock=threading.RLock();self.active=False;self.data={'credentials':{},'last_email':''}
        try:
            if self.path.is_file() and self.path.stat().st_size<65536:
                parsed=json.loads(protect(self.path.read_bytes(),True))
                if isinstance(parsed.get('credentials'),dict):self.data=parsed
        except (OSError,ValueError,TypeError):pass
    def restore(self):
        if self.data.get('last_email'):
            try:self.require()
            except ValueError:pass
    def activate(self,email):
        with self.lock:
            email=email.strip().lower()
            if len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):raise ValueError('Informe um e-mail válido.')
            credentials=self.data['credentials']
            if len(credentials)>20 and email not in credentials:raise ValueError('Entre em contato com o suporte para revisar as ativações neste perfil.')
            token=credentials.setdefault(email,secrets.token_hex(32))
            self.data['last_email']=email
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temporary=self.path.with_suffix('.tmp');temporary.write_bytes(protect(json.dumps(self.data).encode()));temporary.replace(self.path)
            payload={'action':'activate','email':email,'device_hash':machine_hash(),'token_hash':hashlib.sha256(token.encode()).hexdigest(),'device_name':os.environ.get('COMPUTERNAME','Computador Windows')}
            request=urllib.request.Request(ENDPOINT,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
            try:
                with urllib.request.urlopen(request,timeout=18) as response:result=json.loads(response.read(4096))
            except urllib.error.HTTPError as error:
                self.active=False
                try:reason=json.loads(error.read(4096)).get('error')
                except (ValueError,OSError):reason=None
                messages={'device_already_bound':'Este e-mail já está ativado em outro aparelho. Solicite a troca pelo WhatsApp.','try_later':'Muitas consultas. Aguarde antes de tentar novamente.','access_not_available':'Nenhuma licença ativa encontrada. Confira o e-mail da compra e a aprovação do pagamento.'}
                raise ValueError(messages.get(reason,'Não foi possível validar sua licença agora. Tente novamente.')) from None
            except (OSError,ValueError):
                self.active=False;raise ValueError('Conecte-se à internet e tente validar sua licença novamente.') from None
            if result.get('allowed') is not True:self.active=False;raise ValueError('A licença não está disponível para este aparelho.')
            self.active=True
    def require(self):
        email=self.data.get('last_email')
        if not email:raise ValueError('Ative o DarkEdit com o e-mail da compra.')
        self.activate(email)
class ActivationHandler(editor.Handler):
    license=None
    def do_GET(self):
        if not self.allowed():return
        if self.license.active:return super().do_GET()
        path=urlparse(self.path).path
        files={'/':('activation.html','text/html; charset=utf-8'),'/activation.js':('activation.js','text/javascript; charset=utf-8'),'/activation.css':('activation.css','text/css; charset=utf-8')}
        if path not in files:return self.response(403,{'error':'Ative sua licença para abrir o editor.'})
        name,kind=files[path];self.response(200,(editor.ROOT/name).read_bytes().replace(b'__SESSION_TOKEN__',editor.TOKEN.encode()),kind)
    def do_POST(self):
        if not self.allowed(post=True):return
        if urlparse(self.path).path=='/activate':
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=2048:raise ValueError('Solicitação inválida.')
                payload=json.loads(self.rfile.read(size))
                if not isinstance(payload,dict):raise ValueError('Solicitação inválida.')
                email=payload.get('email')
                if not isinstance(email,str):raise ValueError('Informe seu e-mail.')
                self.license.activate(email);self.response(200,{'ok':True})
            except (ValueError,OSError) as error:self.response(400,{'error':str(error)[:250]})
            return
        if not self.license.active:return self.response(403,{'error':'Ative sua licença para abrir o editor.'})
        return super().do_POST()
