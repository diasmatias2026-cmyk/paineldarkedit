from pathlib import Path
ROOT=Path(__file__).resolve().parent
for folder in ['commercial/editor','vendas']:
    for file in (ROOT/folder).rglob('*'):
        if file.is_file() and file.suffix in ['.html','.js','.css','.py','.md','.txt']:
            text=file.read_text(encoding='utf-8-sig').replace('55349999929764','5534999929764').replace('(34) 99999-29764','(34) 99992-9764').replace('1.2.0','1.2.1')
            file.write_text(text,encoding='utf-8')
for name in ['build_commercial.py','upload_releases.py','test_native_delivery.py','test_activation_flow.py','test_public_delivery.py','finalize_delivery.py']:
    file=ROOT/name;text=file.read_text(encoding='utf-8').replace('1.2.0','1.2.1');file.write_text(text,encoding='utf-8')
source=ROOT/'supabase/functions/darkedit-members/index.ts'
source.write_text(source.read_text(encoding='utf-8').replace('1.2.0','1.2.1'),encoding='utf-8')
old=ROOT/'ENTREGA-1.2.0.md';new=ROOT/'ENTREGA-1.2.1.md'
if old.exists():new.write_text(old.read_text(encoding='utf-8').replace('1.2.0','1.2.1').replace('45.619.664 bytes','tamanho e SHA-256 registrados no manifesto'),encoding='utf-8');old.unlink()
print('WhatsApp corrigido para 55 + 34 99992-9764; release 1.2.1 preparada.')
