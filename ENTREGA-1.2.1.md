# DarkEdit 1.2.1 — entrega

## Endereços

- Apresentação: https://darkedit-vendas.vercel.app/
- Obrigado e tutorial: https://darkedit-vendas.vercel.app/obrigado/
- Downloads por e-mail: https://darkedit-vendas.vercel.app/downloads/
- Painel administrativo: https://paineldarkedit.vercel.app/
- Checkout: https://pay.kiwify.com.br/PZAivqQ

As três páginas de vendas/entrega estão públicas. O acesso administrativo continua com autenticação. Os arquivos ficam no bucket privado `darkedit-downloads`, com URLs de dois minutos emitidas após consulta à licença ativa. Nenhum serviço pago foi contratado nesta entrega.

## Instalador e bônus

- `releases/windows/DarkEdit-Setup-1.2.1-x64.exe`: tamanho e SHA-256 registrados no manifesto.
- `releases/bonus/DarkDownload-0.6.0.zip`: manifest na raiz; Chrome/Edge, modo desenvolvedor.
- Hashes SHA-256 e tamanhos estão em `releases/manifest.json` local.

A versão comercial usa dados em `%LOCALAPPDATA%\DarkEditCommercial`; a instalação pessoal DarkEdit Local é independente. O template incluído é genérico. O código comercial não inclui o template pessoal Momento Novela.

Na primeira ativação, o programa consulta a licença pelo e-mail. O servidor vincula dispositivo e credencial aleatória. A credencial é protegida pelo Windows DPAPI no perfil do usuário. Inicialização e início de cada lote consultam o servidor: bloqueio/reembolso é aplicado nas próximas validações. Internet é necessária. A desvinculação de aparelho pelo administrador libera uma nova ativação.

O acesso por e-mail sem senha foi uma escolha expressa do proprietário. Isso consulta uma licença; não comprova a identidade de quem digitou o endereço. Quem souber o e-mail ativo pode solicitar downloads e a primeira ativação. Não é proteção absoluta contra modificação de software local.

## Evidência de verificação

- Windows DPAPI: criptografia, recuperação de credencial estável e recusa offline.
- Interface: ativação, proteção CSRF, JSON inválido, entrada no editor e recusa da exportação após revogação.
- Supabase, transação revertida: aprovação → liberação → primeiro aparelho → recusa do segundo → reembolso bloqueia.
- Executável instalado: instalação silenciosa, renderização real, HTTPS de ativação, WebView2 e importação de mídia.
- Site público: obrigado → área do cliente, recusa de não comprador, e-mail de teste ativo, download real do ZIP e comparação SHA-256.
- Bucket público recusou acesso direto. Somente os arquivos do aplicativo e do bônus são entregues.
- Dados de cliente de teste removidos depois da verificação.

## Etapa externa pendente: Kiwify

O receptor está em modo de teste (`enabled=false`). Ainda não foi configurado/testado na conta Kiwify do proprietário; portanto uma venda real ainda não libera automaticamente a licença.

1. Em Produtos → DarkEdit → Configurações, configure a página de obrigado como `https://darkedit-vendas.vercel.app/obrigado/`, em Cartão ou Pix aprovado, e salve.
2. Em Apps → Webhooks, selecione o produto DarkEdit e a URL secreta de `private/configurar-webhook.txt` local. Marque compra aprovada, reembolso e chargeback.
3. Execute Testar webhook. Conferir o evento real recebido e o produto no Supabase; depois habilitar o processamento real.
4. Em Afiliados na Kiwify, o proprietário define comissão e regras. O link curto Sales Page não é um convite de afiliação. Fazer uma compra/teste permitido pela Kiwify para conferir atribuição e pagamento antes de divulgar.

Não foi cobrada compra de teste. A página de obrigado, sozinha, não prova pagamento.

## Configurações administrativas pendentes

No Supabase Auth → URL Configuration, verificar Site URL e Redirect URL com `https://paineldarkedit.vercel.app/` para links administrativos futuros não voltarem ao localhost. O login administrativo existente já funciona por senha.

O advisor ainda informa proteção contra senhas vazadas desativada. Verificar disponibilidade no plano antes de habilitar; nenhum upgrade foi contratado. As tabelas privadas com RLS sem políticas estão fechadas ao navegador por intenção.

## Código e reconstrução

Fonte comercial em `commercial/editor/`; serviços em `supabase/`; vendas em `vendas/`. O FFmpeg é uma dependência binária e não vai para o Git. O script de build usa o ambiente Python 3.14/pywebview/Pillow/PyInstaller recuperado do projeto anterior e o compilador Inno Setup. Os caminhos locais atuais estão no script; adapte-os em outra máquina. O upload usa sessão administrativa temporária e encerra a sessão ao terminar; não grava a senha.

Android continua no planejamento e não integra a versão 1.2.1 para Windows.
