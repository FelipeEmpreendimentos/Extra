# Checklist de lançamento — SalesBoard Finance v3

Este arquivo separa o que já está resolvido no código do que depende de contas, identidade e decisões do proprietário do produto.

## Engenharia — concluído

- [x] Landing comercial responsiva
- [x] Demonstração pública sem conta
- [x] Cadastro, login, confirmação de e-mail e recuperação de senha
- [x] Onboarding de primeiro acesso
- [x] Banco PostgreSQL com Row Level Security
- [x] Isolamento e integridade de registros por usuário
- [x] Dashboard, contas, lançamentos, categorias, orçamentos, metas e relatórios
- [x] Limites de recursos por plano aplicados também no banco
- [x] Trial de 7 dias sem cartão
- [x] Checkout Stripe autenticado
- [x] Customer Portal
- [x] Webhook Stripe com verificação de assinatura e idempotência
- [x] Recorrências Pro com Scheduled Function e proteção contra duplicação
- [x] Exportação CSV
- [x] Exclusão de conta com cancelamento seguro de assinatura
- [x] Página de contato e formulário antispam básico
- [x] Termos, Privacidade e Segurança como base operacional
- [x] CSP, headers de segurança e segredos fora do frontend
- [x] Artefato público separado do backend/migrations
- [x] CI com instalação, audit, sintaxe, segurança e build
- [x] Dependabot e runtime Node pinado
- [x] GitHub Pages como ambiente de demonstração

## Identidade e marca — obrigatório antes de anunciar

- [ ] Decidir o nome comercial definitivo.
- [ ] Fazer busca na base de marcas do INPI nas classes aplicáveis antes de investir em domínio/identidade.
- [ ] Se o nome final mudar, substituir o branding no projeto antes do domínio público.
- [ ] Definir responsável legal/razão social e CPF/CNPJ aplicável.
- [ ] Definir e-mails monitorados de suporte e privacidade.
- [ ] Revisar implicações fiscais/tributárias da cobrança recorrente com profissional adequado à operação.

> Observação: “SalesBoard Finance” deve ser tratado como nome de trabalho até a decisão de marca. Há softwares públicos usando “SalesBoard” no mercado; uma busca web não substitui a pesquisa oficial e análise de registrabilidade no INPI.

## Supabase — obrigatório

- [ ] Criar projeto de produção.
- [ ] Executar `supabase/schema.sql`.
- [ ] Executar `supabase/002_integrity.sql`.
- [ ] Executar `supabase/003_recurring.sql`.
- [ ] Configurar Site URL para o domínio de produção.
- [ ] Configurar redirect URL de autenticação para `/app/`.
- [ ] Confirmar que confirmação de e-mail está habilitada.
- [ ] Guardar `SUPABASE_URL`, publishable key e secret key nas variáveis do Netlify.

## Stripe — obrigatório

- [ ] Criar produto/Price Essencial mensal — R$14,90.
- [ ] Criar produto/Price Essencial anual — R$149,00.
- [ ] Criar produto/Price Pro mensal — R$24,90.
- [ ] Criar produto/Price Pro anual — R$249,00.
- [ ] Configurar Customer Portal.
- [ ] Criar webhook de produção apontando para `/api/stripe-webhook`.
- [ ] Assinar eventos descritos no README.
- [ ] Guardar a secret key, webhook secret e Price IDs no Netlify.
- [ ] Testar checkout, renovação, falha de pagamento e cancelamento em modo de teste.

## Netlify / domínio — obrigatório

- [ ] Criar site de produção conectado ao repositório com base directory `salesboard`.
- [ ] Cadastrar todas as variáveis do `.env.example` no Netlify.
- [ ] Publicar primeiro deploy.
- [ ] Conferir que `process-recurring` aparece como Scheduled Function.
- [ ] Configurar domínio próprio e HTTPS.
- [ ] Atualizar Site URL/redirects no Supabase para o domínio final.
- [ ] Atualizar webhook Stripe se o endpoint/domínio mudar.
- [ ] Abrir `/api/health` e exigir HTTP 200 + `status: ready`.

## Smoke test — obrigatório

- [ ] Criar usuário real de teste e confirmar e-mail.
- [ ] Completar onboarding.
- [ ] Criar duas contas de usuários diferentes e confirmar isolamento total de dados.
- [ ] Testar CRUD de conta/categoria/lançamento/orçamento/meta.
- [ ] Confirmar limite de 3 contas no Essencial.
- [ ] Confirmar bloqueio de metas/recorrência no Essencial.
- [ ] Confirmar geração única de recorrência Pro como pendente.
- [ ] Testar busca e exportação CSV.
- [ ] Testar trial expirado e paywall.
- [ ] Testar checkout mensal e anual de cada plano.
- [ ] Confirmar webhook e atualização do acesso.
- [ ] Testar Customer Portal/cancelamento.
- [ ] Testar recuperação de senha.
- [ ] Testar formulário de suporte.
- [ ] Testar exclusão de conta com assinatura.
- [ ] Testar Chrome/Edge/Firefox/Safari e Android/iPhone em tamanhos comuns.

## Legal/operacional — obrigatório

- [ ] Revisar Termos de Uso e Política de Privacidade com orientação jurídica adequada à operação real.
- [ ] Confirmar canal para solicitações de titulares de dados.
- [ ] Definir procedimento interno para incidentes e suporte.
- [ ] Definir emissão fiscal/contábil conforme o responsável pela operação.
- [ ] Não usar depoimentos ou números de clientes que não sejam reais e verificáveis.

## GO

Abrir vendas/tráfego somente quando:

- [ ] CI `Validate SalesBoard production` estiver verde no commit lançado.
- [ ] `/api/health` estiver `ready`.
- [ ] Marca/nome definitivo estiver decidido.
- [ ] Supabase, Stripe, Netlify e domínio estiverem em produção.
- [ ] Smoke test completo estiver aprovado.
- [ ] Dados legais e canais de contato estiverem preenchidos.
- [ ] Revisão legal/tributária aplicável estiver concluída.
