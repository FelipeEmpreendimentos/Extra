'use strict';

const Stripe = require('stripe');
const { json, requireEnv, getAdminClient } = require('./_shared');

function priceMapping(priceId) {
  const entries = [
    ['essential', 'monthly', process.env.STRIPE_PRICE_ESSENCIAL_MONTHLY],
    ['essential', 'annual', process.env.STRIPE_PRICE_ESSENCIAL_ANNUAL],
    ['pro', 'monthly', process.env.STRIPE_PRICE_PRO_MONTHLY],
    ['pro', 'annual', process.env.STRIPE_PRICE_PRO_ANNUAL]
  ];
  const match = entries.find((entry) => entry[2] && entry[2] === priceId);
  return match ? { plan: match[0], billingCycle: match[1] } : null;
}

function periodEnd(subscription) {
  const value = subscription.current_period_end || subscription.items?.data?.[0]?.current_period_end;
  return value ? new Date(value * 1000).toISOString() : null;
}

async function userIdForCustomer(admin, customerId) {
  if (!customerId) return null;
  const { data } = await admin
    .from('profiles')
    .select('id')
    .eq('stripe_customer_id', String(customerId))
    .maybeSingle();
  return data?.id || null;
}

async function syncSubscription(admin, subscription) {
  const item = subscription.items?.data?.[0];
  const priceId = item?.price?.id || null;
  const mapped = priceMapping(priceId);
  const userId = subscription.metadata?.salesboard_user_id || await userIdForCustomer(admin, subscription.customer);
  if (!userId) throw new Error(`Usuário não localizado para assinatura ${subscription.id}.`);

  const plan = subscription.metadata?.salesboard_plan || mapped?.plan || 'pro';
  const billingCycle = subscription.metadata?.billing_cycle || mapped?.billingCycle || 'monthly';
  const normalizedStatus = ['active', 'trialing', 'past_due', 'canceled'].includes(subscription.status)
    ? subscription.status
    : 'none';

  const { error: subscriptionError } = await admin.from('subscriptions').upsert({
    user_id: userId,
    stripe_customer_id: String(subscription.customer),
    stripe_subscription_id: subscription.id,
    stripe_price_id: priceId,
    plan,
    billing_cycle: billingCycle,
    status: normalizedStatus,
    current_period_end: periodEnd(subscription),
    cancel_at_period_end: Boolean(subscription.cancel_at_period_end)
  }, { onConflict: 'user_id' });
  if (subscriptionError) throw subscriptionError;

  const profileStatus = normalizedStatus === 'canceled' ? 'canceled' : normalizedStatus;
  const { error: profileError } = await admin.from('profiles').update({
    stripe_customer_id: String(subscription.customer),
    plan: plan === 'essential' ? 'essential' : 'pro',
    subscription_status: profileStatus
  }).eq('id', userId);
  if (profileError) throw profileError;
}

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return json(405, { error: 'Método não permitido.' }, { Allow: 'POST' });
  }

  try {
    requireEnv(['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'SUPABASE_URL', 'SUPABASE_SECRET_KEY']);
    const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
    const admin = getAdminClient();
    const signature = event.headers?.['stripe-signature'] || event.headers?.['Stripe-Signature'];
    if (!signature) return json(400, { error: 'Assinatura Stripe ausente.' });

    const rawBody = event.isBase64Encoded
      ? Buffer.from(event.body || '', 'base64')
      : (event.body || '');

    let stripeEvent;
    try {
      stripeEvent = stripe.webhooks.constructEvent(rawBody, signature, process.env.STRIPE_WEBHOOK_SECRET);
    } catch (error) {
      console.error('Stripe signature validation failed:', error.message);
      return json(400, { error: 'Assinatura de webhook inválida.' });
    }

    const { data: alreadyProcessed } = await admin
      .from('webhook_events')
      .select('id')
      .eq('id', stripeEvent.id)
      .maybeSingle();
    if (alreadyProcessed) return json(200, { received: true, duplicate: true });

    switch (stripeEvent.type) {
      case 'checkout.session.completed': {
        const session = stripeEvent.data.object;
        const userId = session.metadata?.salesboard_user_id || session.client_reference_id;
        if (userId && session.customer) {
          await admin.from('profiles').update({ stripe_customer_id: String(session.customer) }).eq('id', userId);
        }
        if (session.subscription) {
          const subscription = await stripe.subscriptions.retrieve(String(session.subscription));
          await syncSubscription(admin, subscription);
        }
        break;
      }
      case 'customer.subscription.created':
      case 'customer.subscription.updated':
      case 'customer.subscription.deleted': {
        await syncSubscription(admin, stripeEvent.data.object);
        break;
      }
      case 'invoice.payment_failed': {
        const invoice = stripeEvent.data.object;
        const userId = await userIdForCustomer(admin, invoice.customer);
        if (userId) {
          await admin.from('profiles').update({ subscription_status: 'past_due' }).eq('id', userId);
          await admin.from('subscriptions').update({ status: 'past_due' }).eq('user_id', userId);
        }
        break;
      }
      case 'invoice.paid': {
        const invoice = stripeEvent.data.object;
        const subscriptionId = invoice.subscription || invoice.parent?.subscription_details?.subscription;
        if (subscriptionId) {
          const subscription = await stripe.subscriptions.retrieve(String(subscriptionId));
          await syncSubscription(admin, subscription);
        }
        break;
      }
      default:
        break;
    }

    const { error: eventError } = await admin.from('webhook_events').insert({
      id: stripeEvent.id,
      event_type: stripeEvent.type
    });
    if (eventError && eventError.code !== '23505') throw eventError;

    return json(200, { received: true });
  } catch (error) {
    console.error('Stripe webhook error:', error);
    return json(500, { error: 'Falha ao processar webhook.' });
  }
};
