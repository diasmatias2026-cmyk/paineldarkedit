from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent
for name in ['KIWIFY-INTEGRACAO.md','prepare_commercial.py']:
    f=ROOT/name;s=f.read_text(encoding='utf-8',errors='replace').replace('1.2.0','1.2.1');f.write_text(s,encoding='utf-8')
security=ROOT/'SECURITY-REVIEW.md'
s=security.read_text(encoding='utf-8',errors='replace')
if not s.startswith('# Verificação atual'):
    s='''# Verificação atual — Windows 1.2.1 e entrega

Ver [ENTREGA-1.2.1.md](ENTREGA-1.2.1.md) para o estado atual. A versão comercial possui consulta online e vínculo de um aparelho; a área pública emite URLs temporárias de arquivos privados. Testes reais de instalação, renderização, ativação HTTPS e download foram executados. As contas de teste foram removidas. A licença manual do proprietário está ativa.

O receptor Kiwify permanece em modo de teste, aguardando configurar e testar na conta do proprietário. O advisor informa proteção contra senhas vazadas desativada. O acesso por e-mail sem senha é uma decisão expressa do proprietário e não autentica a identidade do comprador. Não houve contratação de plano pago nem auditoria externa/pentest completo. O plano de hospedagem deve ser adequado ao uso comercial.

O texto abaixo registra a auditoria anterior do painel, antes da implementação comercial.

---

'''+s
security.write_text(s,encoding='utf-8')
script=ROOT/'check_final_release.py'
s=script.read_text(encoding='utf-8')
if 'unins000.exe' not in s:
    s+="\nuninstaller=installed/'unins000.exe'\nassert uninstaller.resolve().is_relative_to((ROOT/'build').resolve())\nsubprocess.run([str(uninstaller),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],check=True,timeout=90)\n"
script.write_text(s,encoding='utf-8')
installed=ROOT/'build/installed-121';uninstaller=installed/'unins000.exe'
if uninstaller.exists():
    assert uninstaller.resolve().is_relative_to((ROOT/'build').resolve())
    subprocess.run([str(uninstaller),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],check=True,timeout=90)
old=Path('D:/DOC 3.11/DarkEdit-entrega-1.2.0')
if old.is_dir():(old/'NOVA-VERSAO.txt').write_text('Use a versao atual em D:/DOC 3.11/DarkEdit-entrega-1.2.1.\nO contato WhatsApp foi corrigido na versao 1.2.1.\n',encoding='utf-8')
print('Documentacao atualizada e instalacao de teste desinstalada.')
