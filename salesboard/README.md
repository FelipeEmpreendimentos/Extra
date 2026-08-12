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
- recorrências Pro com geração automática diária de ocorrências pendentes;
- exportação CSV e busca global;
- trial de 7 dias sem cartão com recursos Pro;
- planos Essencial e Pro, mensal e anual;
- Stripe Checkout autenticado, Customer Portal e webhook verificado;
- bloqueio de escrita após trial/assinatura expirar;
- exclusão de conta com cancelamento seguro de assinatura ativa;
- páginas de Termos, Privacidade e Segurança;
- formulário de suporte via Netlify Forms;
- headers de segurança e Content Security Policy;
- artefato público separado de Functions/migrations/arquivos internos;
- endpoint `/api/health` para validar configuração do ambiente;
- CI `.github/workflows/salesboard-production-check.yml`.

> **Importante:** o repositório não contém segredos reais. O sistema só fica apto a receber clientes depois que Supabase, Stripe, identidade legal e variáveis do Netlify forem configurados. `/api/health` deve responder `status: "ready"` antes do lançamento.

## Ambientes

### GitHub Pages — demonstração pública

O workflow `.github/workflows/salesboard-pages.yml` gera um artefato contendo somente os arquivos públicos e o publica no GitHub Pages. Nesse host, CTAs de cadastro são convertidos para `app/?demo=1` porque GitHub Pages é estático e não executa autenticação/cobrança server-side.

### Netlify / domínio próprio — produção

Use Netlify para o SaaS comercial.

No Netlify, conecte este repositório e configure:

- **Base directory:** `salesboard`
- o `netlify.toml` já define o comando de build;
- o build gera `.dist` e publica somente a interface;
- Functions ficam em `netlify/functions`, fora do diretório publicado.

O `netlify.toml` já contém redirects, headers, CSP e configuração de Functions.

## 1. Configurar Supabase

1. Crie um projeto Supabase de produção.
2. Abra o SQL Editor.
3. Execute, nesta ordem:
   - `supabase/schema.sql`
   - `supabase/002_integrity.sql`
   - `supabase/003_recurring.sql`
4. Em Auth, configure a URL principal para o domínio de produção.
5. Adicione como URL de redirecionamento a rota do aplicativo, por exemplo `https://seu-dominio.com/app/`.
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

Ative o Stripe Customer Portal para permitir que o cliente visualize cobrança, atualize método de pagamento e cancele a renovação.

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

## 4. Recorrências automáticas

`netlify/functions/process-recurring.mjs` é uma Scheduled Function configurada para `08:00 UTC` diariamente.

O comportamento é:

- somente usuários em trial válido ou plano Pro ativo recebem geração automática;
- lançamentos marcados como semanais, mensais ou anuais funcionam como origem;
- cada nova ocorrência é criada como **pendente**, para não alterar o saldo até o usuário confirmar que ela realmente aconteceu;
- uma constraint única impede duplicação da mesma ocorrência;
- contas cujo trial expirou ou cuja assinatura não dá acesso Pro são ignoradas.

Depois do primeiro deploy de produção, confira no painel de Functions do Netlify se `process-recurring` aparece como `Scheduled` e execute uma vez manualmente em ambiente de teste.

## 5. Identidade legal e suporte

Antes de vender:

- substitua `LEGAL_ENTITY_NAME` pela pessoa/empresa responsável pelo serviço;
- substitua `LEGAL_ENTITY_ID` pelo identificador jurídico aplicável;
- configure um e-mail de suporte monitorado;
- configure um canal de privacidade monitorado;
- revise `legal/termos.html` e `legal/privacidade.html` com orientação jurídica adequada ao responsável pelo negócio e ao público-alvo.

As páginas legais exibem um aviso quando esses dados não estão configurados.

## 6. Smoke test antes de abrir tráfego

Faça o fluxo completo em ambiente de teste:

1. Abra `/api/health` e confirme HTTP 200 + `"status":"ready"`.
2. Crie uma nova conta com um e-mail real de teste.
3. Confirme o e-mail.
4. Complete o onboarding.
5. Crie entrada, saída, categoria e orçamento.
6. Confirme que outro usuário não enxerga nenhum desses dados.
7. Teste limite de 3 contas no Essencial.
8. Teste que meta e recorrência exigem Pro.
9. Crie uma recorrência Pro, execute `process-recurring` manualmente e confirme que a ocorrência foi criada uma única vez como pendente.
10. Exporte CSV.
11. Inicie checkout Essencial mensal em modo de teste.
12. Confirme que o webhook altera a assinatura.
13. Abra o Customer Portal.
14. Simule falha/cancelamento e confirme atualização do acesso.
15. Teste recuperação de senha.
16. Envie o formulário de contato.
17. Exclua uma conta de teste e confirme que os dados foram removidos e a assinatura encerrada.
18. Faça testes em desktop e celular.

## 7. Validação automática

A cada alteração relevante, o workflow `Validate SalesBoard production` verifica:

- presença de todos os arquivos de lançamento;
- sintaxe JavaScript, inclusive Scheduled Function;
- RLS e validações de integridade;
- isolamento de referências de conta/categoria/recorrência;
- autenticação nas Functions de cobrança;
- assinatura de webhook Stripe;
- ausência de banco financeiro em `localStorage` no app comercial;
- ausência de segredos Stripe acidentalmente commitados;
- geração de artefato estático limpo, sem Functions, migrations, `.env.example` ou `package.json`;
- páginas legais, contato, exclusão de conta e gestão de cobrança;
- ausência de depoimentos fictícios e de planos não lançados na landing.

## Desenvolvimento local

```bash
cd salesboard
npm install
cp .env.example .env
npm run check
npm run dev
```

Depois abra a URL local informada pelo Netlify CLI.

## Arquitetura resumida

```text
Browser
  ├─ Landing / app estático (.dist)
  ├─ Supabase Auth + queries autorizadas por RLS
  └─ /api/*
        └─ Netlify Functions
             ├─ Supabase secret key (server only)
             └─ Stripe secret key (server only)

Stripe Webhook
  └─ valida assinatura do evento
       └─ atualiza assinatura/permissão no Supabase

Scheduled Function diária
  └─ lê origens recorrentes Pro
       └─ gera ocorrências pendentes sem duplicação
```

## Critério de GO

O lançamento comercial está liberado somente quando todos os itens abaixo forem verdadeiros:

- CI do SalesBoard verde;
- `/api/health` retorna `ready`;
- domínio HTTPS de produção configurado;
- três migrations Supabase executadas;
- Stripe Prices + webhook + Customer Portal configurados;
- Scheduled Function de recorrência verificada no Netlify;
- identidade legal e canais de contato preenchidos;
- smoke test de cadastro → uso → recorrência → checkout → cancelamento aprovado;
- páginas legais revisadas para a operação real.
