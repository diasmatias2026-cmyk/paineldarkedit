# DarkEdit

Editor Windows com ativação por e-mail em um aparelho, painel de licenças no Supabase e páginas de apresentação e entrega na Vercel. Consulte [ENTREGA-1.2.1.md](ENTREGA-1.2.1.md) para evidências e pendências.

## Acessos
- Vendas: https://darkedit-vendas.vercel.app/
- Obrigado/tutorial: https://darkedit-vendas.vercel.app/obrigado/
- Downloads: https://darkedit-vendas.vercel.app/downloads/
- Administração: https://paineldarkedit.vercel.app/

A conta administrativa existente entra com e-mail e senha. O comprador usa o e-mail da compra na área de downloads e no programa. A licença do proprietário está cadastrada como manual; não é uma compra Kiwify.

## Código
- public/: painel administrativo estático.
- vendas/: apresentação, tutorial e área do cliente.
- commercial/editor/: fonte da versão comercial Windows 1.2.1.
- supabase/: schema, funções de pagamento e controle de dispositivos.
- releases/: instaladores e hashes locais, ignorados pelo Git.
- private/: URL secreta do webhook, somente local e ignorada pelo Git.

Nenhuma chave de serviço ou senha integra o frontend. A chave publishable é pública. O banco aplica RLS e autorização administrativa por conta verificada e sessão existente; os clientes não podem editar o histórico de auditoria. A sessão administrativa do navegador fica em memória.

As páginas de vendas e entrega estão públicas. O bucket de arquivos é privado e emite links temporários após consulta à licença. A instalação pessoal antiga permanece independente da versão comercial.

## Kiwify
O checkout está conectado aos botões de compra. A configuração da conta Kiwify e o teste de webhook ainda são necessários para ativar a liberação automática; o receptor continua em modo de teste. Ver [KIWIFY-INTEGRACAO.md](KIWIFY-INTEGRACAO.md). Não foi cobrada compra de teste.

## Hospedagem e operação
Nenhum upgrade pago foi contratado. O plano Vercel Hobby restringe uso comercial; o proprietário precisa adequar o plano/hospedagem antes da operação comercial. Não houve alteração de cobrança. A publicação é feita por snapshot; push no GitHub não faz deploy automático enquanto a integração GitHub/Vercel não for autorizada.

O advisor Supabase ainda informa proteção contra senhas vazadas desativada. As tabelas privadas com RLS sem políticas estão intencionalmente fechadas ao navegador. Verificar também as URLs administrativas de redirecionamento do Auth para futuras recuperações de senha.

Android está no planejamento e não integra a oferta Windows atual.
