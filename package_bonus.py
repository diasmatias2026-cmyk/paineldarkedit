from pathlib import Path
import zipfile,json,shutil
root=Path(__file__).resolve().parent
old=Path('D:/DOC 3.11/Codex/2026-11-02/vam/outputs')
source=old/'sistema-local-unificado/extensao';out=root/'releases/bonus';out.mkdir(parents=True,exist_ok=True)
manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8-sig'));assert manifest['version']=='0.6.0'
with zipfile.ZipFile(out/'DarkDownload-0.6.0.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in source.rglob('*'):
        if f.is_file() and f.suffix.lower() in ['.json','.js','.css','.html','.png','.svg','.md'] and not any(p.startswith('.') for p in f.relative_to(source).parts):z.write(f,f.relative_to(source))
    z.writestr('INSTALAR.txt','Extraia esta pasta. Em chrome://extensions ou edge://extensions, ative o modo do desenvolvedor. Use Carregar sem compactacao e escolha esta pasta. Mantenha os arquivos no mesmo lugar. Use apenas conteudos autorizados.')
with zipfile.ZipFile(out/'DarkDownload-0.6.0.zip') as z:assert 'manifest.json' in z.namelist() and z.testzip() is None
for name in ['members.sql']:
    source=old/'paineldarkedit/supabase'/name
    if source.exists():shutil.copy2(source,root/'supabase'/name)
print('Bonus ZIP: OK; manifest 0.6.0 na raiz; integridade verificada.')
