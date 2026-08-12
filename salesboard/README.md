# SalesBoard Finance v3.1

SaaS responsivo de controle financeiro para pessoas, autônomos e pequenos negócios.

## Arquitetura de produção

```text
GitHub Pages
  ├─ landing comercial
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
  └─ gera ocorrências de lançamentos recorrentes Pro
```

O navegador recebe somente configuração pública. Chaves administrativas, Stripe Secret Key e webhook secret ficam no ambiente server-side do Supabase.

## URLs

- Landing: `https://felipeempreendimentos.github.io/Extra/salesboard/`
- Aplicativo: `https://felipeempreendimentos.github.io/Extra/salesboard/app/`
- Supabase project ref: `azjabgqvkkctgzqacpue`

## Fluxo de aquisição e trial

1. usuário cria a conta por e-mail ou Google;
2. entra em uma tela de seleção de experiência;
3. escolhe **Essencial** ou **Pro** para testar;
4. somente nesse clique começam 72 horas completas;
5. onboarding cria conta/categorias iniciais de forma atômica;
6. durante o trial valem exatamente as permissões do plano escolhido;
7. terminado o período, os dados são preservados e a tela de continuidade oferece assinatura;
8. o mesmo e-mail pode iniciar somente um trial, mesmo que a conta seja excluída depois.

A demonstração pública continua como **Pro completo** para apresentar a melhor versão do produto.

## Planos

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
| Metas financeiras | Não | Sim |
| Lançamentos recorrentes | Não | Sim |
| Busca e filtros | Sim | Sim |
| Exportação CSV | Sim | Sim |

Os limites críticos são reforçados no PostgreSQL, e não apenas escondidos pela interface.

## Recursos principais

- Supabase Auth com e-mail/senha, confirmação, recuperação e Google OAuth;
- onboarding transacional, com categorias iniciais coerentes com Pessoal/Autônomo/Negócio e sem orçamentos monetários arbitrários;
- dashboard, entradas, saídas, contas e categorias;
- orçamentos e metas vinculáveis a lançamentos;
- recorrências Pro;
- relatórios essenciais/avançados conforme entitlement, com filtro mensal simples;
- exportação CSV;
- pesquisa e filtros;
- trial único por e-mail;
- paywall de continuidade;
- Stripe Checkout e Customer Portal autenticados;
- webhook idempotente com assinatura Stripe;
- exclusão de conta com cancelamento da assinatura;
- RLS por usuário e validações de integridade;
- Termos, Privacidade e Segurança;
- auditoria automatizada de responsividade e CI de produção.

## Responsividade

O frontend é auditado automaticamente em uma matriz que inclui:

`320x568`, `360x800`, `375x812`, `390x844`, `412x915`, `430x932`, `768x1024`, `820x1180`, `1024x768`, `1280x720`, `1366x768`, `1440x900`, `1536x864`, `1920x1080` e `2560x1440`.

O teste percorre landing, dashboard, lançamentos, contas, orçamentos, metas, relatórios, cobrança, configurações e modais, verificando overflow, clipping, erros de JavaScript/rede e alvos interativos.

## Stripe

O código suporta separação TEST/LIVE.

Em TEST mode, existem preços de referência do projeto. Em LIVE mode, os IDs devem ser fornecidos por secrets do Supabase; o código não reutiliza automaticamente catálogo de teste com uma chave live.

Secrets necessários:

```text
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRICE_ESSENTIAL_MONTHLY
STRIPE_PRICE_ESSENTIAL_ANNUAL
STRIPE_PRICE_PRO_MONTHLY
STRIPE_PRICE_PRO_ANNUAL
STRIPE_PRODUCT_ESSENTIAL
STRIPE_PRODUCT_PRO
LEGAL_ENTITY_NAME
LEGAL_ENTITY_ID
SUPPORT_EMAIL
PRIVACY_EMAIL
```

## Estado de lançamento

O software e a infraestrutura de código podem ser validados pelo CI, mas **cobrança real não deve ser aberta enquanto o health check de produção estiver em `configuration_required`**.

Antes de aceitar clientes pagantes:

1. preencher identidade legal e canais de suporte/privacidade;
2. criar os Products/Prices no Stripe **LIVE mode**;
3. configurar `sk_live_...` e os seis IDs live nos Supabase Secrets;
4. criar o webhook live e configurar `STRIPE_WEBHOOK_SECRET`;
5. confirmar que `salesboard-health` retorna `ready`;
6. executar checkout real controlado e confirmar atualização via webhook;
7. validar portal, troca de plano, falha de pagamento e cancelamento;
8. testar exclusão de uma conta com assinatura;
9. revisar novamente textos legais para a identidade real da operação.

## Segurança

- RLS ativo nas tabelas de usuário;
- referências conta/categoria/meta/recorrência validadas no banco;
- campos de billing são controlados pelo backend;
- entitlement é aplicado também no PostgreSQL;
- chave publishable do Supabase pode ficar no navegador; segredos não;
- webhook verifica assinatura do Stripe;
- app comercial não usa `localStorage` como banco financeiro;
- repositório é público: antes de adicionar lógica proprietária sensível ou ampliar equipe, considere migrar o produto para um repositório privado.

## Marca

`SalesBoard Finance` é nome de trabalho. Antes de investimento relevante em domínio e tráfego, faça pesquisa de anterioridade/registrabilidade no INPI.
