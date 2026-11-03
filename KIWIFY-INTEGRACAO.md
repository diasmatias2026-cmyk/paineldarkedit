# Kiwify — checkout, obrigado e liberação

## Endereços
- Vendas: https://darkedit-vendas.vercel.app/
- Checkout: https://pay.kiwify.com.br/PZAivqQ
- Página de obrigado: https://darkedit-vendas.vercel.app/obrigado/
- Link curto Sales Page informado: https://kiwify.app/rEzmru3 (não é o convite de afiliação).

Os botões Comprar o DarkEdit e Comprar com a Kiwify já apontam para o checkout. WhatsApp continua como suporte. Os parâmetros afid, src, sck, UTM e s1/s2/s3 recebidos são repassados por uma lista permitida, sem aceitar URLs de destino arbitrárias. A atribuição final é feita pela Kiwify: testar uma compra com um link real de afiliado.

## Configurar a página de obrigado
Kiwify > Produtos > DarkEdit > Configurações > Página de obrigado e upsell.
Ativar a página personalizada e colar no campo Cartão ou Pix aprovado:
https://darkedit-vendas.vercel.app/obrigado/
Salvar produto. Não usar o gerador de upsell: esta página é orientação, não uma nova oferta.

As páginas continuam protegidas pela autenticação Vercel para avaliação. Compradores comuns não conseguem abrir sem acesso. Antes de divulgar vendas reais, resolver acesso público e hospedagem compatível com uso comercial; nenhum upgrade foi contratado.

## Configurar o webhook
A URL completa com token está somente em ../DarkEdit-integracao-privada/configurar-webhook.txt (fora deste repositório). Não publicar nem compartilhar com afiliados.
Kiwify > Apps > Webhooks > Criar Webhook > selecionar DarkEdit.
Eventos: compra aprovada, reembolso, chargeback. Usar Testar Webhook e consultar Ver logs.
Estado atual: TESTE; enabled=false. HTTP 200 com action=dry_run confirma que o evento foi autenticado e os campos/produto foram aceitos. duplicate indica repetição do mesmo pedido/evento. ignored_product requer conferir o ID do produto. Somente depois desse teste e da validação do executável comercial, habilitar o processamento real.

## Como o comprador é identificado
O servidor lê Customer.email do JSON enviado pela Kiwify e normaliza para minúsculas. Nunca usa e-mail de um formulário público ou query da página de obrigado como prova de compra. Product.product_id deve ser o configurado, sale_type precisa ser producer, order_approved deve trazer status paid. Refund e chargeback são vinculados pelo order_id.

## Segurança e estado
- Receptor Supabase: kiwify-webhook, autenticado por segredo aleatório de 256 bits na URL exclusiva de servidor. O banco guarda apenas SHA-256. Esta é autenticação por segredo compartilhado, não assinatura nativa Kiwify.
- RPC de processamento é exclusiva de service_role; sem permissão anon/authenticated. A chave de serviço é lida das variáveis privadas da Edge Function, nunca vai para a página.
- Body limitado a 32 KiB, JSON, POST; sem CORS; HTTPS e mensagens sem dados pessoais.
- Pedido + evento são únicos; aprovação atrasada não reativa pedido estornado. Bloqueios manuais e licenças manuais são preservados; outra compra paga evita bloquear por estorno de apenas um pedido. Recompra pode reativar bloqueio causado pelo pagamento.
- Tabelas privadas de pedidos/configuração/recebimentos têm RLS sem acesso ao navegador; banco processa mudanças em transação.
- Testes de aprovação/duplicação/estorno/recompra/bloqueio manual em transações revertidas. Nenhum cliente de teste persistido.
- HTTP real: sem token 401; token errado 403; token válido em modo teste 200/dry_run; repetição 200/duplicate.
- Advisor: RLS sem políticas nas tabelas privadas é intencional. Aviso de proteção contra senhas vazadas desativada no Auth continua pendente de configuração/limites do plano.

## Ainda pendente para vender com entrega automática
Configurar o webhook na conta Kiwify e validar payload real; ativar integração; integrar consulta/vínculo de licença na versão comercial do executável; preparar entrega segura do instalador; liberar hospedagem pública apropriada; testar ponta a ponta. A versão pessoal do DarkEdit continua sem licença por escolha do proprietário. Nenhum pagamento de teste real foi cobrado.
