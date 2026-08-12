'use strict';

const Stripe = require('stripe');
const { json, requireEnv, verifyUser, requestOrigin, safeError } = require('./_shared');

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return json(405, { error: 'Método não permitido.' }, { Allow: 'POST' });
  }

  try {
    requireEnv(['STRIPE_SECRET_KEY']);
    const { user, admin } = await verifyUser(event);
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

    const { data: profile, error } = await admin
      .from('profiles')
      .select('stripe_customer_id')
      .eq('id', user.id)
      .single();

    if (error) throw error;
    if (!profile?.stripe_customer_id) {
      return json(404, { error: 'Nenhuma cobrança vinculada a esta conta.' });
    }

    const session = await stripe.billingPortal.sessions.create({
      customer: profile.stripe_customer_id,
      return_url: `${requestOrigin(event)}/app/?billing=return`
    });

    return json(200, { url: session.url });
  } catch (error) {
    return safeError(error);
  }
};
