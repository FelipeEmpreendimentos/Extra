'use strict';

const Stripe = require('stripe');
const { json, verifyUser, safeError } = require('./_shared');

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return json(405, { error: 'Método não permitido.' }, { Allow: 'POST' });
  }

  try {
    const { user, admin } = await verifyUser(event);
    const body = JSON.parse(event.body || '{}');
    if (body.confirmation !== 'EXCLUIR') {
      return json(400, { error: 'Confirmação inválida.' });
    }

    const { data: subscription } = await admin
      .from('subscriptions')
      .select('stripe_subscription_id,status')
      .eq('user_id', user.id)
      .maybeSingle();

    if (subscription?.stripe_subscription_id && process.env.STRIPE_SECRET_KEY && subscription.status !== 'canceled') {
      const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
      try {
        await stripe.subscriptions.cancel(subscription.stripe_subscription_id);
      } catch (error) {
        if (error?.code !== 'resource_missing') throw error;
      }
    }

    const { error } = await admin.auth.admin.deleteUser(user.id);
    if (error) throw error;

    return json(200, { deleted: true });
  } catch (error) {
    return safeError(error);
  }
};
