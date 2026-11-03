# DarkEdit — painel administrativo

Painel conectado ao Supabase `idsesxzabyswkfmtgjen`. Frontend estático sem dependências de terceiros. Diretório público: `public/`.

## Primeiro acesso
Use o e-mail administrativo `diasmatias2026@gmail.com` e clique em **Primeiro acesso: cadastrar minha senha**. Escolha uma senha exclusiva com pelo menos 12 caracteres, confirme o e-mail enviado pelo Supabase e entre. A confirmação é exclusiva do administrador; o fluxo dos clientes continuará sem código. Não envie senhas pelo chat.

Somente o e-mail aprovado em `darkedit_private.administrators`, confirmado pelo Supabase Auth e com sessão existente, pode consultar ou alterar dados. Cadastrar outra conta não concede acesso administrativo.

## Segurança e operação
- RLS e privilégios mínimos em todas as tabelas; acesso anônimo negado.
- Lista de administradores em schema privado; sem permissão de edição pelo painel.
- Sessão somente em memória: recarregar a página exige login. Nenhum token no localStorage.
- Auditoria criada por triggers do banco; clientes do navegador não podem editar o histórico.
- Chave publishable pública; nenhuma chave administrativa no frontend.
- CSP restritiva e headers de segurança em `vercel.json`.
- Consulta de até 1.000 clientes recentes e 200 eventos recentes. Paginação completa é uma etapa futura.
- Banco é a autoridade para validar campos, unicidade de e-mail e permissões.

## Escopo desta versão
Gerenciar cadastro, bloquear/reativar licenças, desvincular aparelho e editar a oferta. A integração da ativação e verificação de licença no executável Windows/Android ainda não foi implementada. Desvincular no painel não controla versões pessoais antigas do aplicativo.

A tabela começa vazia; nenhum cliente fictício foi inserido. O banco e o navegador foram testados separadamente; primeiro login real depende de confirmar o e-mail administrativo. Uma auditoria não garante ausência de toda vulnerabilidade.

## Publicação
Hospedar `public/` como site estático HTTPS; `vercel.json` configura headers na Vercel. Antes de publicar verificar plano, equipe e permissão para uso comercial. Não contratar upgrades sem autorização. A migração inicial está em `supabase/schema.sql`, já aplicada ao projeto indicado.
