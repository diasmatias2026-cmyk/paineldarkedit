from pathlib import Path
import json, base64
root=Path(__file__).resolve().parent
thanks=root/'vendas/obrigado/index.html'
s=thanks.read_text(encoding='utf-8')
if 'href="/downloads/"' not in s:
    s=s.replace('<section class="delivery">','<section class="delivery"><div><h2>Seu programa e seu bônus.</h2><p>Acesse com o e-mail da compra para baixar o DarkEdit e a extensão DarkDownload.</p><a class="button dark" href="/downloads/">Acessar meus downloads ↓</a></div></section><section class="delivery">',1)
thanks.write_text(s,encoding='utf-8')
sales=root/'vendas/index.html';s=sales.read_text(encoding='utf-8')
if 'Bônus: extensão DarkDownload' not in s:s=s.replace('<li>Exportações ilimitadas</li>','<li>Exportações ilimitadas</li><li>Bônus: extensão DarkDownload para Instagram</li>')
if 'href="/downloads/"' not in s:s=s.replace('<footer>','<footer><a href="/downloads/">Já comprou? Acessar downloads →</a>',1)
sales.write_text(s,encoding='utf-8')
config=json.loads((root/'vercel.json').read_text(encoding='utf-8'))
for h in config['headers'][0]['headers']:
    if h['key']=='Content-Security-Policy':h['value']="default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' blob:; media-src 'self' blob:; connect-src https://idsesxzabyswkfmtgjen.supabase.co; base-uri 'none'; form-action 'self'; frame-ancestors 'none'; upgrade-insecure-requests"
(root/'vendas/vercel.json').write_text(json.dumps(config),encoding='utf-8')
files=[]
for path in sorted((root/'vendas').rglob('*')):
    if path.is_file() and path.suffix in ['.html','.css','.js']:
        files.append({'file':'public/'+path.relative_to(root/'vendas').as_posix(),'data':base64.b64encode(path.read_bytes()).decode(),'encoding':'base64'})
files.append({'file':'vercel.json','data':base64.b64encode(json.dumps(config).encode()).decode(),'encoding':'base64'})
(root/'deployment-text.json').write_text(json.dumps(files),encoding='utf-8')
print('Portal e obrigado atualizados; manifesto de deploy pronto.')
