'use strict';

const { json } = require('./_shared');

exports.handler = async (event) => {
  if (event.httpMethod !== 'GET') {
    return json(405, { error: 'Método não permitido.' }, { Allow: 'GET' });
  }

  const checks = {
    supabasePublic: Boolean(process.env.SUPABASE_URL && process.env.SUPABASE_PUBLISHABLE_KEY),
    supabaseServer: Boolean(process.env.SUPABASE_URL && process.env.SUPABASE_SECRET_KEY),
    stripeServer: Boolean(process.env.STRIPE_SECRET_KEY && process.env.STRIPE_WEBHOOK_SECRET),
    stripePrices: Boolean(
      process.env.STRIPE_PRICE_ESSENCIAL_MONTHLY &&
      process.env.STRIPE_PRICE_ESSENCIAL_ANNUAL &&
      process.env.STRIPE_PRICE_PRO_MONTHLY &&
      process.env.STRIPE_PRICE_PRO_ANNUAL
    ),
    legalIdentity: Boolean(process.env.LEGAL_ENTITY_NAME && process.env.LEGAL_ENTITY_ID),
    contactChannels: Boolean(process.env.SUPPORT_EMAIL && process.env.PRIVACY_EMAIL)
  };

  const ready = Object.values(checks).every(Boolean);
  return json(ready ? 200 : 503, {
    status: ready ? 'ready' : 'configuration_required',
    checks,
    timestamp: new Date().toISOString()
  });
};
