const Stripe = require('stripe');

const PLAN_CATALOG = {
  Essencial: { amount: 1490, name: 'SalesBoard Finance Essencial' },
  Pro: { amount: 2490, name: 'SalesBoard Finance Pro' },
  'Negócios': { amount: 3990, name: 'SalesBoard Finance Negócios' }
};

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
    const selectedPlan = String(body.plan || 'Pro');
    const plan = PLAN_CATALOG[selectedPlan];

    if (!plan) {
      return { statusCode: 400, body: JSON.stringify({ error: 'Plano inválido.' }) };
    }

    const priceIdByPlan = {
      Essencial: process.env.STRIPE_PRICE_ESSENCIAL,
      Pro: process.env.STRIPE_PRICE_PRO,
      'Negócios': process.env.STRIPE_PRICE_NEGOCIOS
    };

    const configuredPriceId = priceIdByPlan[selectedPlan];
    const lineItem = configuredPriceId
      ? { price: configuredPriceId, quantity: 1 }
      : {
          price_data: {
            currency: 'brl',
            unit_amount: plan.amount,
            recurring: { interval: 'month' },
            product_data: { name: plan.name }
          },
          quantity: 1
        };

    const origin = event.headers.origin || process.env.URL || 'http://localhost:8888';
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      line_items: [lineItem],
      allow_promotion_codes: true,
      billing_address_collection: 'auto',
      success_url: `${origin}?checkout=success&plan=${encodeURIComponent(selectedPlan)}`,
      cancel_url: `${origin}?checkout=cancelled`,
      metadata: { plan: selectedPlan }
    });

    return { statusCode: 200, body: JSON.stringify({ url: session.url }) };
  } catch (error) {
    return { statusCode: 500, body: JSON.stringify({ error: error.message || 'Erro ao criar checkout.' }) };
  }
};
