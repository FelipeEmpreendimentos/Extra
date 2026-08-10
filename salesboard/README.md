# SalesBoard MVP

Dashboard responsivo para acompanhar vendas, clientes, metas e assinatura mensal.

## O que já funciona

- Dashboard com receita, número de vendas, ticket médio e meta mensal
- Gráfico dos últimos 6 meses em Canvas, sem biblioteca externa
- Cadastro e exclusão de vendas
- Busca e filtro por status
- Visão consolidada de clientes
- Exportação CSV
- Configurações salvas no navegador (nome, plano, mensalidade, meta, moeda e ticket sugerido)
- Página de assinatura mensal
- Função Netlify para criar uma assinatura recorrente no Stripe Checkout
- Layout responsivo para desktop e celular

## Rodar localmente sem cobrança

Abra `index.html` diretamente no navegador. O dashboard funciona e os dados ficam no `localStorage`.

## Rodar com Netlify Functions / Stripe

1. Instale Node.js.
2. No diretório do projeto, execute `npm install`.
3. Copie `.env.example` para `.env` e informe sua `STRIPE_SECRET_KEY`.
4. Execute `npm run dev`.
5. Abra a URL exibida pelo Netlify CLI.

## Preço personalizável e segurança

A interface permite editar a mensalidade livremente para o MVP. Para produção, o valor que realmente será cobrado deve permanecer controlado no servidor, por exemplo via `SUBSCRIPTION_PRICE_CENTS`.

Se `ALLOW_DYNAMIC_PRICE=true`, a função aceita o preço enviado pela interface. Isso é útil apenas em painel administrativo autenticado; não é seguro permitir isso em uma página pública, pois o navegador pode ser manipulado.

## Próxima evolução recomendada

Para transformar este MVP em SaaS multiusuário de produção: autenticação, banco de dados, organizações/contas, webhooks Stripe para controlar status de assinatura e autorização de acesso por plano.
