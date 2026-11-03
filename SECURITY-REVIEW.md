# Revisão de segurança — 2026-11-03

Corrigidos: ausência de login, dados exclusivamente locais, falta de autorização no banco e histórico alterável pelo cliente. Removidos clientes de demonstração da versão integrada.

Verificações realizadas:
- Chamadas HTTP reais sem login às três tabelas: HTTP 401, acesso negado.
- Papel authenticated sem administrador/sessão autorizados: nenhuma linha de clientes/oferta visível.
- Administrador confirmado com sessão, em transação revertida: cadastro e bloqueio permitidos; dois eventos de auditoria gerados.
- Testes do navegador com API simulada: login, cadastro, bloqueio, escape de conteúdo HTML, logout, memória sem localStorage e layout móvel.
- Nenhuma dependência npm; nenhum segredo administrativo em arquivos públicos.
- Advisor Supabase: somente aviso informativo de RLS sem policy na tabela PRIVADA de administradores, intencionalmente inacessível aos clientes. A função interna controlada consulta a lista.

Limites: login real do proprietário e verificação após publicação dependem da criação/confirmação da conta. A licença do executável não está integrada neste escopo. O frontend consulta no máximo 1.000 clientes e 200 eventos. Nenhum upgrade pago contratado.

## Publicação verificada
URL: https://paineldarkedit.vercel.app/
Projeto Vercel: prj_EzxoXYJqfche7VY8MoxD8Ar0HAlU
Deployment: dpl_6RFj9qYrkcXfQxbsJBca4wBuMo8g (READY)
Equipe: team_wsoW9seBAz7UF9DptJbWFfJu

Acesso protegido por Vercel Authentication (all_except_custom_domains; apenas domínios vercel.app cadastrados) e por Supabase Auth + autorização administrativa. HTML/JS/CSS retornaram 200 via acesso autenticado; CSP, no-store e cabeçalhos de segurança presentes. Nenhuma conta Auth e nenhum cliente real criado durante os testes.

O vínculo automático GitHub→Vercel foi recusado pela ausência de autorização da integração GitHub para este repositório. A publicação foi feita por snapshot dos arquivos já enviados ao GitHub. Novos pushes ainda NÃO geram deploy automático. O Site alternativo criado durante a avaliação permaneceu sem publicação e não é utilizado.

Primeiro acesso real do proprietário pendente: cadastrar senha exclusiva de 12+ caracteres com diasmatias2026@gmail.com, confirmar e-mail e entrar. Não enviar senhas por chat. A integração da licença no executável pessoal permanece pendente; este painel não bloqueia o DarkEdit pessoal já instalado.
