const Stripe = require('stripe');

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Método não permitido.' }) };
  }

  if (!process.env.STRIPE_SECRET_KEY) {
    return { statusCode: 503, body: JSON.stringify({ error: 'STRIPE_SECRET_KEY não configurada.' }) };
  }

  try {
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
    const body = JSON.parse(event.body || '{}');

    // Em produção, mantenha ALLOW_DYNAMIC_PRICE=false e defina SUBSCRIPTION_PRICE_CENTS no servidor.
    // Preço vindo do navegador só deve ser aceito em um painel administrativo autenticado.
    const allowDynamic = process.env.ALLOW_DYNAMIC_PRICE === 'true';
    const serverAmount = Number(process.env.SUBSCRIPTION_PRICE_CENTS || 4990);
    const amountCents = allowDynamic ? Number(body.amountCents || serverAmount) : serverAmount;
    const currency = String(process.env.SUBSCRIPTION_CURRENCY || body.currency || 'brl').toLowerCase();
    const productName = String(process.env.SUBSCRIPTION_PLAN_NAME || body.planName || 'SalesBoard Pro');

    if (!Number.isFinite(amountCents) || amountCents < 100) {
      return { statusCode: 400, body: JSON.stringify({ error: 'Valor inválido para assinatura.' }) };
    }

    const origin = event.headers.origin || process.env.URL || 'http://localhost:8888';
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      line_items: [
        {
          price_data: {
            currency,
            unit_amount: Math.round(amountCents),
            recurring: { interval: 'month' },
            product_data: { name: productName }
          },
          quantity: 1
        }
      ],
      success_url: `${origin}?checkout=success`,
      cancel_url: `${origin}?checkout=cancelled`
    });

    return { statusCode: 200, body: JSON.stringify({ url: session.url }) };
  } catch (error) {
    return { statusCode: 500, body: JSON.stringify({ error: error.message || 'Erro ao criar checkout.' }) };
  }
};
