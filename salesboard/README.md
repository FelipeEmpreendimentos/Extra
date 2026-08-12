# SalesBoard Finance v3

SaaS responsivo de controle financeiro para pessoas, autônomos e pequenos negócios.

## Arquitetura atual

A versão publicada usa:

```text
GitHub Pages
  ├─ landing
  └─ aplicativo web
       ├─ Supabase Auth
       ├─ PostgreSQL + RLS
       └─ Supabase Edge Functions
            ├─ Checkout Stripe
            ├─ Customer Portal
            ├─ exclusão de conta
            ├─ health check
            └─ webhook Stripe

PostgreSQL / pg_cron
  └─ gera ocorrências de lançamentos recorrentes Pro diariamente
```

O GitHub Pages serve somente arquivos públicos. Nenhuma chave administrativa ou chave secreta do Stripe é enviada ao navegador. `app/runtime-bridge.js` fornece a configuração pública do Supabase e direciona as antigas rotas `/api/*` do frontend para as Edge Functions do projeto.

## URL pública

`https://felipeempreendimentos.github.io/Extra/salesboard/`

A raiz `https://felipeempreendimentos.github.io/Extra/` redireciona para o SalesBoard.

## O que já está implementado

- landing comercial responsiva;
- cadastro e login reais via Supabase Auth;
- login com Google via Supabase Auth (frontend pronto; requer credenciais Google no provedor);
- confirmação de e-mail e recuperação de senha;
- onboarding;
- dashboard financeiro;
- entradas e saídas;
- contas;
- categorias personalizadas;
- orçamentos;
- metas Pro;
- lançamentos recorrentes Pro;
- relatórios essenciais no Essencial e relatórios avançados de 12 meses no Pro;
- exportação CSV;
- trial Pro de 3 dias sem cartão, contado a partir da criação da conta;
- paywall após expiração;
- limite de 3 contas no Essencial aplicado também no banco;
- Stripe Checkout autenticado;
- Stripe Customer Portal;
- webhook idempotente e com verificação de assinatura;
- exclusão de conta com cancelamento da assinatura;
- RLS por usuário e validações de integridade;
- páginas de Termos, Privacidade e Segurança;
- CI e deploy automático pelo GitHub Actions.

## Matriz de planos

O trial de 3 dias entrega **todas as permissões do Pro**. A demonstração pública também roda como **Pro ativo**, para mostrar a melhor versão do produto.

| Recurso | Essencial | Pro |
|---|---|---|
| Lançamentos | Ilimitados | Ilimitados |
| Contas ativas | Até 3 | Ilimitadas |
| Categorias personalizadas | Sim | Sim |
| Orçamentos mensais | Sim | Sim |
| Dashboard financeiro | Sim | Sim |
| Relatórios essenciais | Sim | Sim |
| Relatórios avançados de 12 meses | Não | Sim |
| Comparações e diagnósticos | Não | Sim |
| Pendências e análise de recorrências | Não | Sim |
| Metas financeiras | Não | Sim |
| Lançamentos recorrentes | Não | Sim |
| Busca e filtros | Sim | Sim |
| Exportação CSV | Sim | Sim |

Os limites críticos são reforçados no PostgreSQL, e não apenas escondidos pela interface.

## Supabase de produção

Project ref:

`azjabgqvkkctgzqacpue`

O banco já possui as tabelas, RLS, guards de integridade, suporte a recorrência e job `salesboard-recurring-daily` ativo no `pg_cron` às `08:15 UTC`.

As Edge Functions implantadas são:

- `salesboard-health`
- `salesboard-checkout`
- `salesboard-billing-portal`
- `salesboard-delete-account`
- `salesboard-stripe-webhook`

## Stripe

A integração está preparada em **modo teste**. Produtos e Prices de teste existentes:

| Plano | Mensal | Anual |
|---|---:|---:|
| Essencial | R$ 14,90 | R$ 149,00 |
| Pro | R$ 24,90 | R$ 249,00 |

O webhook de teste aponta para:

`https://azjabgqvkkctgzqacpue.supabase.co/functions/v1/salesboard-stripe-webhook`

Eventos utilizados:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

## Segredos obrigatórios no Supabase

Antes de testar cobrança, abra **Supabase → Edge Functions → Secrets** e configure:

```text
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
LEGAL_ENTITY_NAME
LEGAL_ENTITY_ID
SUPPORT_EMAIL
PRIVACY_EMAIL
```

`STRIPE_SECRET_KEY` deve corresponder ao mesmo modo dos Prices usados pelas Functions. Atualmente os IDs configurados são de **teste**, portanto use uma `sk_test_...` para o smoke test.

O signing secret deve ser o segredo do webhook `salesboard-stripe-webhook` criado no mesmo ambiente Stripe.

Não coloque nenhum desses valores no GitHub ou em arquivos JavaScript públicos.

## Customer Portal

O Stripe Customer Portal precisa ser ativado/configurado no Dashboard antes do smoke test de gerenciamento de assinatura. Configure cancelamento no fim do período, atualização de método de pagamento e histórico de cobrança conforme a política comercial.

## Auth

No Supabase Auth, mantenha confirmação de e-mail habilitada e autorize o endereço do app como redirect URL:

`https://felipeempreendimentos.github.io/Extra/salesboard/app/`

O frontend já chama `signInWithOAuth({ provider: 'google' })`. Para o botão Google funcionar de verdade, habilite o provedor Google no Supabase Auth com um Client ID e Client Secret do Google Cloud. No Google, o callback autorizado do projeto Supabase deve apontar para:

`https://azjabgqvkkctgzqacpue.supabase.co/auth/v1/callback`

Usuários criados por OAuth que ainda não tenham aceite registrado precisam aceitar Termos e Privacidade durante o onboarding.

Quando houver domínio próprio, adicione o novo domínio antes de remover a URL do Pages.

## Recorrências

A função PostgreSQL `public.process_salesboard_recurring_transactions()` é chamada diariamente pelo job `salesboard-recurring-daily`.

- trial válido recebe recursos Pro;
- plano Pro ativo recebe recorrências;
- Essencial não recebe geração automática;
- ocorrências geradas começam como `pending`;
- índice único impede duplicação por origem/data.

## Critério de lançamento

Não abra cobrança real antes de concluir estes itens:

1. configurar os segredos acima;
2. configurar o Customer Portal;
3. configurar redirects do Supabase Auth;
4. ativar e testar o provedor Google OAuth;
5. testar cadastro → onboarding → CRUD financeiro;
6. testar dois usuários e confirmar isolamento de dados;
7. testar checkout em modo teste;
8. confirmar atualização da assinatura pelo webhook;
9. testar falha de pagamento e cancelamento;
10. testar exclusão de conta com assinatura;
11. preencher identidade legal e canais de suporte/privacidade;
12. criar os quatro Prices em **live mode** e trocar os IDs das Edge Functions para os Prices live;
13. usar `sk_live_...` e webhook live somente depois do smoke test completo;
14. revisar os textos legais para a operação real.

## Marca

`SalesBoard Finance` deve ser tratado como nome de trabalho até a validação de marca. Antes de investir em domínio e tráfego, faça pesquisa de anterioridade/registrabilidade no INPI.

## Segurança

- chave publishable do Supabase pode ficar no navegador; RLS protege os dados;
- chaves administrativas e Stripe ficam apenas no Supabase Edge Functions Secrets;
- webhook verifica assinatura Stripe;
- billing fields são server-managed;
- referências conta/categoria/recorrência são validadas no banco;
- o app comercial não usa `localStorage` como banco financeiro;
- o repositório é público: para um produto proprietário, considere migrar a base de produção para um repositório privado antes de ampliar a equipe ou adicionar código proprietário sensível.
