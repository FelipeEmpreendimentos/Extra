'use strict';

const Stripe = require('stripe');
const { json, requireEnv, verifyUser, requestOrigin, safeError } = require('./_shared');

const PRICE_ENV = {
  essential: {
    monthly: 'STRIPE_PRICE_ESSENCIAL_MONTHLY',
    annual: 'STRIPE_PRICE_ESSENCIAL_ANNUAL'
  },
  pro: {
    monthly: 'STRIPE_PRICE_PRO_MONTHLY',
    annual: 'STRIPE_PRICE_PRO_ANNUAL'
  }
};

const PLAN_LABEL = {
  essential: 'Essencial',
  pro: 'Pro'
};

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return json(405, { error: 'Método não permitido.' }, { Allow: 'POST' });
  }

  try {
    requireEnv(['STRIPE_SECRET_KEY']);
    const { user, admin } = await verifyUser(event);
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
    const body = JSON.parse(event.body || '{}');
    const plan = String(body.plan || 'pro').toLowerCase();
    const billingCycle = String(body.billingCycle || 'monthly').toLowerCase();

    if (!PRICE_ENV[plan] || !PRICE_ENV[plan][billingCycle]) {
      return json(400, { error: 'Plano ou periodicidade inválidos.' });
    }

    const priceEnvName = PRICE_ENV[plan][billingCycle];
    const priceId = process.env[priceEnvName];
    if (!priceId) {
      return json(503, { error: `Preço Stripe ainda não configurado (${priceEnvName}).` });
    }

    const { data: profile, error: profileError } = await admin
      .from('profiles')
      .select('id,full_name,stripe_customer_id,subscription_status,trial_ends_at')
      .eq('id', user.id)
      .single();

    if (profileError || !profile) {
      throw profileError || new Error('Perfil financeiro não encontrado.');
    }

    const { data: existingSubscription } = await admin
      .from('subscriptions')
      .select('stripe_subscription_id,status')
      .eq('user_id', user.id)
      .maybeSingle();

    if (existingSubscription?.stripe_subscription_id && ['active', 'trialing', 'past_due'].includes(existingSubscription.status)) {
      return json(409, {
        error: 'Você já possui uma assinatura. Use “Gerenciar cobrança” para alterar seu plano.',
        code: 'SUBSCRIPTION_EXISTS'
      });
    }

    let customerId = profile.stripe_customer_id;
    if (!customerId) {
      const customer = await stripe.customers.create({
        email: user.email,
        name: profile.full_name || undefined,
        metadata: { salesboard_user_id: user.id }
      });
      customerId = customer.id;
      await admin.from('profiles').update({ stripe_customer_id: customerId }).eq('id', user.id);
    }

    const nowSeconds = Math.floor(Date.now() / 1000);
    const trialEndSeconds = profile.trial_ends_at ? Math.floor(new Date(profile.trial_ends_at).getTime() / 1000) : 0;
    const subscriptionData = {
      metadata: {
        salesboard_user_id: user.id,
        salesboard_plan: plan,
        billing_cycle: billingCycle
      }
    };

    // Preserve the remaining no-card trial when there is still meaningful time left.
    if (profile.subscription_status === 'trialing' && trialEndSeconds > nowSeconds + 3600) {
      subscriptionData.trial_end = trialEndSeconds;
    }

    const origin = requestOrigin(event);
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      customer: customerId,
      client_reference_id: user.id,
      line_items: [{ price: priceId, quantity: 1 }],
      allow_promotion_codes: true,
      billing_address_collection: 'auto',
      locale: 'pt-BR',
      subscription_data: subscriptionData,
      success_url: `${origin}/app/?checkout=success&plan=${encodeURIComponent(plan)}`,
      cancel_url: `${origin}/app/?checkout=cancelled`,
      metadata: {
        salesboard_user_id: user.id,
        salesboard_plan: plan,
        billing_cycle: billingCycle,
        plan_label: PLAN_LABEL[plan]
      }
    });

    return json(200, { url: session.url });
  } catch (error) {
    return safeError(error);
  }
};
