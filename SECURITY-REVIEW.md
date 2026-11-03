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
