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
- confirmação de e-mail e recuperação de senha;
- onboarding;
- dashboard financeiro;
- entradas e saídas;
- contas;
- categorias personalizadas;
- orçamentos;
- metas Pro;
- lançamentos recorrentes Pro;
- relatórios e insights;
- exportação CSV;
- trial Pro de 7 dias sem cartão;
- paywall após expiração;
- limite de 3 contas no Essencial aplicado também no banco;
- Stripe Checkout autenticado;
- Stripe Customer Portal;
- webhook idempotente e com verificação de assinatura;
- exclusão de conta com cancelamento da assinatura;
- RLS por usuário e validações de integridade;
- páginas de Termos, Privacidade e Segurança;
- CI e deploy automático pelo GitHub Actions.

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
4. testar cadastro → onboarding → CRUD financeiro;
5. testar dois usuários e confirmar isolamento de dados;
6. testar checkout em modo teste;
7. confirmar atualização da assinatura pelo webhook;
8. testar falha de pagamento e cancelamento;
9. testar exclusão de conta com assinatura;
10. preencher identidade legal e canais de suporte/privacidade;
11. criar os quatro Prices em **live mode** e trocar os IDs das Edge Functions para os Prices live;
12. usar `sk_live_...` e webhook live somente depois do smoke test completo;
13. revisar os textos legais para a operação real.

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
