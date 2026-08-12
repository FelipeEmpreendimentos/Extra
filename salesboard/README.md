# SalesBoard Finance v2

SaaS responsivo de controle financeiro para pessoas, autônomos, MEIs e pequenos negócios.

## O que já existe

- Landing page comercial completa com hero, demonstração do produto, recursos, planos, FAQ e CTAs.
- Fluxo de cadastro/login demonstrativo e período de teste.
- Dashboard com saldo, entradas, saídas, taxa de economia, fluxo de caixa e saúde financeira.
- Lançamentos de entrada e saída com conta, categoria, data, observação e recorrência.
- Categorias personalizáveis para entrada e saída, incluindo limite mensal.
- Contas bancárias, dinheiro, carteiras e investimentos.
- Orçamentos mensais por categoria.
- Metas financeiras com progresso e aportes.
- Relatórios e insights do período.
- Busca global, filtros e exportação CSV.
- Interface totalmente responsiva com sidebar desktop e navegação inferior mobile.
- Três planos: Essencial (R$ 14,90), Pro (R$ 24,90) e Negócios (R$ 39,90).
- Checkout Stripe preparado em Netlify Function com preços definidos no servidor.

## Deploy público

O repositório possui o workflow `.github/workflows/salesboard-pages.yml`, que publica a pasta `salesboard` no GitHub Pages a cada alteração no `main`.

> O GitHub Pages hospeda a experiência web estática. A função de cobrança Stripe exige deploy em uma plataforma com funções server-side, como Netlify. O front-end detecta quando o checkout não está disponível e continua operando em modo demonstração.

## Rodar com Netlify localmente

```bash
npm install
cp .env.example .env
npm run dev
```

Configure `STRIPE_SECRET_KEY` e, preferencialmente, os Price IDs recorrentes do Stripe em `STRIPE_PRICE_ESSENCIAL`, `STRIPE_PRICE_PRO` e `STRIPE_PRICE_NEGOCIOS`.

## Status para produção

A interface e as regras de demonstração estão prontas para validação de produto. Antes de vender comercialmente, a próxima camada deve substituir o armazenamento local por autenticação e banco multiusuário reais (por exemplo PostgreSQL/Supabase), adicionar webhooks do Stripe, controle de acesso por assinatura, recuperação de senha, termos/política publicados e backups.
