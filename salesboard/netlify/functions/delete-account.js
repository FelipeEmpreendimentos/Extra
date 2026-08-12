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

    const { data: subscription, error: subscriptionLookupError } = await admin
      .from('subscriptions')
      .select('stripe_subscription_id,status')
      .eq('user_id', user.id)
      .maybeSingle();
    if (subscriptionLookupError) throw subscriptionLookupError;

    const hasLiveStripeSubscription = subscription?.stripe_subscription_id && subscription.status !== 'canceled';
    if (hasLiveStripeSubscription) {
      // Never delete the local account while a paid Stripe subscription could keep charging.
      if (!process.env.STRIPE_SECRET_KEY) {
        const configurationError = new Error('Não é seguro excluir a conta enquanto a integração de cobrança está indisponível. Tente novamente ou contate o suporte.');
        configurationError.code = 'BILLING_CONFIGURATION_REQUIRED';
        throw configurationError;
      }

      const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
      try {
        await stripe.subscriptions.cancel(subscription.stripe_subscription_id);
      } catch (error) {
        // If Stripe says the subscription no longer exists, local deletion can proceed.
        if (error?.code !== 'resource_missing') throw error;
      }
    }

    const { error } = await admin.auth.admin.deleteUser(user.id);
    if (error) throw error;

    return json(200, { deleted: true });
  } catch (error) {
    if (error?.code === 'BILLING_CONFIGURATION_REQUIRED') {
      return json(503, { error: error.message });
    }
    return safeError(error);
  }
};
