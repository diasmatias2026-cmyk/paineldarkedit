from pathlib import Path
import shutil,json,hashlib,re
ROOT=Path(__file__).resolve().parent
private=ROOT/'private';private.mkdir(exist_ok=True)
old=Path('D:/DOC 3.11/Codex/2026-11-02/vam/outputs/DarkEdit-integracao-privada/configurar-webhook.txt')
shutil.copy2(old,private/'configurar-webhook.txt')
doc=ROOT/'KIWIFY-INTEGRACAO.md';s=doc.read_text(encoding='utf-8')
s=s.replace('As páginas continuam protegidas pela autenticação Vercel para avaliação. Compradores comuns não conseguem abrir sem acesso. Antes de divulgar vendas reais, resolver acesso público e hospedagem compatível com uso comercial; nenhum upgrade foi contratado.','As páginas de vendas, obrigado e downloads estão públicas. O painel administrativo tem autenticação própria. Nenhum upgrade de hospedagem foi contratado. A conformidade do plano escolhido com uso comercial deve ser conferida pelo proprietário antes da divulgação.')
s=s.replace('A URL completa com token está somente em ../DarkEdit-integracao-privada/configurar-webhook.txt (fora deste repositório).','A URL completa com token está em private/configurar-webhook.txt na cópia local, ignorada pelo Git.')
s=s.replace('Configurar o webhook na conta Kiwify e validar payload real; ativar integração; integrar consulta/vínculo de licença na versão comercial do executável; preparar entrega segura do instalador; liberar hospedagem pública apropriada; testar ponta a ponta.','Configurar o webhook na conta Kiwify, validar o evento real e ativar integração. O executável comercial 1.2.1, o vínculo por aparelho, o armazenamento privado e a área pública de downloads foram implementados e testados; ver ENTREGA-1.2.1.md.')
doc.write_text(s,encoding='utf-8')
out=Path('D:/DOC 3.11/DarkEdit-entrega-1.2.1')
out.mkdir(exist_ok=True)
for source in [ROOT/'releases/windows/DarkEdit-Setup-1.2.1-x64.exe',ROOT/'releases/bonus/DarkDownload-0.6.0.zip',ROOT/'releases/manifest.json',ROOT/'ENTREGA-1.2.1.md']:
    destination=out/source.name
    if destination.exists():assert hashlib.sha256(destination.read_bytes()).digest()==hashlib.sha256(source.read_bytes()).digest()
    else:shutil.copy2(source,destination)
(out/'LINKS.txt').write_text('Vendas: https://darkedit-vendas.vercel.app/\nObrigado: https://darkedit-vendas.vercel.app/obrigado/\nDownloads: https://darkedit-vendas.vercel.app/downloads/\nPainel: https://paineldarkedit.vercel.app/\nGitHub: https://github.com/diasmatias2026-cmyk/paineldarkedit\n\nUse seu e-mail administrativo na area de downloads para testar. A ativacao ocorre ao abrir o programa.\n\nA integracao Kiwify aguarda configurar e testar o webhook na conta do proprietario.\n',encoding='utf-8')
print('Entrega salva em:',out)
