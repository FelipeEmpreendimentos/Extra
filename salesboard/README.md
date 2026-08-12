# SalesBoard Finance v3

SaaS responsivo de controle financeiro para pessoas, autônomos e pequenos negócios.

## Status

O código está estruturado para lançamento comercial com:

- landing page de aquisição e demonstração pública;
- cadastro, login, confirmação de e-mail e recuperação de senha via Supabase Auth;
- onboarding em 3 etapas;
- PostgreSQL/Supabase com Row Level Security por usuário;
- validações server-side de integridade e limites de plano;
- dashboard, contas, entradas, saídas, categorias, orçamentos, metas e relatórios;
- exportação CSV e busca global;
- trial de 7 dias sem cartão com recursos Pro;
- planos Essencial e Pro, mensal e anual;
- Stripe Checkout autenticado, Customer Portal e webhook verificado;
- bloqueio de escrita após trial/assinatura expirar;
- exclusão de conta com cancelamento de assinatura ativa;
- páginas de Termos, Privacidade e Segurança;
- formulário de suporte via Netlify Forms;
- headers de segurança e Content Security Policy;
- endpoint `/api/health` para validar configuração do ambiente;
- CI `.github/workflows/salesboard-production-check.yml`.

> **Importante:** o repositório não contém segredos reais. O sistema só fica apto a receber clientes depois que Supabase, Stripe, identidade legal e variáveis do Netlify forem configurados. `/api/health` deve responder `status: "ready"` antes do lançamento.

## Ambientes

### GitHub Pages — demonstração pública

O workflow `.github/workflows/salesboard-pages.yml` publica a pasta `salesboard` no GitHub Pages. Nesse host, CTAs de cadastro são convertidos para `app/?demo=1` porque GitHub Pages é estático e não executa as Functions de autenticação/cobrança.

### Netlify / domínio próprio — produção

Use Netlify (ou plataforma equivalente compatível com as Functions deste projeto) para o SaaS comercial.

No Netlify, configure o projeto a partir do repositório e defina:

- **Base directory:** `salesboard`
- **Publish directory:** `.`
- **Functions directory:** `netlify/functions`

O `netlify.toml` já contém redirects, headers e CSP.

## 1. Configurar Supabase

1. Crie um projeto Supabase de produção.
2. Abra o SQL Editor.
3. Execute, nesta ordem:
   - `supabase/schema.sql`
   - `supabase/002_integrity.sql`
4. Em Auth, configure a URL principal para o domínio de produção.
5. Adicione como URL de redirecionamento a rota de produção do aplicativo, por exemplo `https://seu-dominio.com/app/`.
6. Mantenha confirmação de e-mail habilitada para contas reais.
7. Copie a URL do projeto, a chave **publishable** e a chave **secret** para as variáveis do Netlify.

Nunca coloque `SUPABASE_SECRET_KEY` no HTML ou JavaScript do navegador.

## 2. Configurar Stripe

Crie dois produtos/planos comerciais e quatro Prices recorrentes:

| Plano | Mensal | Anual |
|---|---:|---:|
| Essencial | R$ 14,90/mês | R$ 149,00/ano |
| Pro | R$ 24,90/mês | R$ 249,00/ano |

O anual equivale a 10 mensalidades, ou seja, 2 meses de desconto em relação a 12 pagamentos mensais.

Copie os Price IDs para:

- `STRIPE_PRICE_ESSENCIAL_MONTHLY`
- `STRIPE_PRICE_ESSENCIAL_ANNUAL`
- `STRIPE_PRICE_PRO_MONTHLY`
- `STRIPE_PRICE_PRO_ANNUAL`

### Customer Portal

Ative o Stripe Customer Portal para permitir que o cliente veja cobranças, atualize método de pagamento e cancele a renovação.

### Webhook

Crie um endpoint apontando para:

`https://SEU-DOMINIO/api/stripe-webhook`

Assine pelo menos os eventos:

- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

Copie o signing secret para `STRIPE_WEBHOOK_SECRET`.

## 3. Variáveis do Netlify

Use `.env.example` como referência, mas cadastre valores reais no painel de Environment Variables do Netlify.

Obrigatórias para o lançamento:

```text
SUPABASE_URL
SUPABASE_PUBLISHABLE_KEY
SUPABASE_SECRET_KEY
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRICE_ESSENCIAL_MONTHLY
STRIPE_PRICE_ESSENCIAL_ANNUAL
STRIPE_PRICE_PRO_MONTHLY
STRIPE_PRICE_PRO_ANNUAL
SUPPORT_EMAIL
PRIVACY_EMAIL
LEGAL_ENTITY_NAME
LEGAL_ENTITY_ID
APP_NAME
```

Não versione `.env` com valores reais.

## 4. Identidade legal e suporte

Antes de vender:

- substitua `LEGAL_ENTITY_NAME` pela pessoa/empresa responsável pelo serviço;
- substitua `LEGAL_ENTITY_ID` pelo identificador jurídico aplicável;
- configure um e-mail de suporte monitorado;
- configure um canal de privacidade monitorado;
- revise `legal/termos.html` e `legal/privacidade.html` com orientação jurídica adequada ao responsável pelo negócio e ao público-alvo.

As páginas legais exibem um aviso quando esses dados não estão configurados.

## 5. Smoke test antes de abrir tráfego

Faça o fluxo completo em ambiente de teste:

1. Abra `/api/health` e confirme HTTP 200 + `"status":"ready"`.
2. Crie uma nova conta com um e-mail real de teste.
3. Confirme o e-mail.
4. Complete o onboarding.
5. Crie entrada, saída, categoria e orçamento.
6. Confirme que outro usuário não enxerga nenhum desses dados.
7. Teste limite de 3 contas no Essencial.
8. Teste que meta e recorrência exigem Pro.
9. Exporte CSV.
10. Inicie checkout Essencial mensal em modo de teste.
11. Confirme que o webhook altera a assinatura.
12. Abra o Customer Portal.
13. Simule falha/cancelamento e confirme atualização do acesso.
14. Teste recuperação de senha.
15. Envie o formulário de contato.
16. Exclua uma conta de teste e confirme que os dados foram removidos e a assinatura encerrada.
17. Faça testes em desktop e celular.

## 6. Validação automática

A cada alteração em `salesboard/**`, o workflow `Validate SalesBoard production` verifica:

- presença de todos os arquivos de lançamento;
- sintaxe JavaScript;
- RLS e validações de integridade;
- autenticação nas Functions de cobrança;
- assinatura de webhook Stripe;
- ausência de banco financeiro em `localStorage` no app comercial;
- ausência de segredos Stripe acidentalmente commitados;
- páginas legais, contato, exclusão de conta e gestão de cobrança;
- ausência de depoimentos fictícios e de planos não lançados na landing.

## Desenvolvimento local

```bash
cd salesboard
npm install
cp .env.example .env
npm run dev
```

Depois abra a URL local informada pelo Netlify CLI.

## Arquitetura resumida

```text
Browser
  ├─ Landing estática
  ├─ Supabase Auth + queries autorizadas por RLS
  └─ /api/*
        └─ Netlify Functions
             ├─ Supabase secret key (server only)
             └─ Stripe secret key (server only)

Stripe Webhook
  └─ Netlify Function
       └─ valida assinatura do evento
            └─ atualiza assinatura/permissão no Supabase
```

## Critério de GO

O lançamento comercial está liberado somente quando todos os itens abaixo forem verdadeiros:

- CI do SalesBoard verde;
- `/api/health` retorna `ready`;
- domínio HTTPS de produção configurado;
- Supabase migrations executadas;
- Stripe Prices + webhook + Customer Portal configurados;
- identidade legal e canais de contato preenchidos;
- smoke test de cadastro → uso → checkout → cancelamento aprovado;
- páginas legais revisadas para a operação real.
