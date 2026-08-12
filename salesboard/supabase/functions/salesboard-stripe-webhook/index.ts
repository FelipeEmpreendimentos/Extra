import Stripe from 'npm:stripe@18.5.0'
import { createClient } from 'npm:@supabase/supabase-js@2.111.0'

const stripeSecret = Deno.env.get('STRIPE_SECRET_KEY') || ''
const webhookSecret = Deno.env.get('STRIPE_WEBHOOK_SECRET') || ''
const stripe = new Stripe(stripeSecret, { httpClient: Stripe.createFetchHttpClient() })
const cryptoProvider = Stripe.createSubtleCryptoProvider()

function adminClient() {
  const url = Deno.env.get('SUPABASE_URL')!
  const legacy = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
  const modern = Deno.env.get('SUPABASE_SECRET_KEYS')
  const key = legacy || (modern ? JSON.parse(modern).default : '')
  return createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } })
}

const priceMap: Record<string, { plan: 'essential' | 'pro'; billing: 'monthly' | 'annual' }> = {
  'price_1U3eqnRlODNbnkUiLRDXlIZm': { plan: 'essential', billing: 'monthly' },
  'price_1U3erCRlODNbnkUiYSxDq1e6': { plan: 'essential', billing: 'annual' },
  'price_1U3eqyRlODNbnkUirbXIqvR8': { plan: 'pro', billing: 'monthly' },
  'price_1U3erNRlODNbnkUiCYny1NeZ': { plan: 'pro', billing: 'annual' }
}

async function profileExists(admin: ReturnType<typeof adminClient>, userId: string) {
  const { data, error } = await admin.from('profiles').select('id').eq('id', userId).maybeSingle()
  if (error) throw error
  return Boolean(data?.id)
}

async function userIdForCustomer(admin: ReturnType<typeof adminClient>, customer: string | Stripe.Customer | Stripe.DeletedCustomer | null) {
  if (!customer) return null
  const customerId = typeof customer === 'string' ? customer : customer.id
  const { data, error } = await admin.from('profiles').select('id').eq('stripe_customer_id', customerId).maybeSingle()
  if (error) throw error
  return data?.id || null
}

async function syncSubscription(admin: ReturnType<typeof adminClient>, subscription: Stripe.Subscription) {
  const item = subscription.items.data[0]
  const priceId = item?.price?.id || null
  const mapped = priceId ? priceMap[priceId] : null
  const customerId = typeof subscription.customer === 'string' ? subscription.customer : subscription.customer.id
  const userId = subscription.metadata?.salesboard_user_id || await userIdForCustomer(admin, subscription.customer)
  if (!userId || !(await profileExists(admin, userId))) return

  const plan = subscription.metadata?.salesboard_plan === 'essential' ? 'essential' : subscription.metadata?.salesboard_plan === 'pro' ? 'pro' : mapped?.plan || 'pro'
  const billing = subscription.metadata?.billing_cycle === 'annual' ? 'annual' : subscription.metadata?.billing_cycle === 'monthly' ? 'monthly' : mapped?.billing || 'monthly'
  const normalized = ['active', 'trialing', 'past_due', 'canceled'].includes(subscription.status) ? subscription.status : 'none'
  const period = subscription.items.data[0]?.current_period_end

  const { error: subError } = await admin.from('subscriptions').upsert({
    user_id: userId,
    stripe_customer_id: customerId,
    stripe_subscription_id: subscription.id,
    stripe_price_id: priceId,
    plan,
    billing_cycle: billing,
    status: normalized,
    current_period_end: period ? new Date(period * 1000).toISOString() : null,
    cancel_at_period_end: Boolean(subscription.cancel_at_period_end)
  }, { onConflict: 'user_id' })
  if (subError) throw subError

  const { error: profileError } = await admin.from('profiles').update({
    stripe_customer_id: customerId,
    plan,
    subscription_status: normalized
  }).eq('id', userId)
  if (profileError) throw profileError
}

Deno.serve(async (req) => {
  if (req.method !== 'POST') return new Response('Method not allowed', { status: 405 })
  if (!stripeSecret || !webhookSecret) return new Response('Stripe webhook not configured', { status: 503 })

  try {
    const signature = req.headers.get('stripe-signature')
    if (!signature) return new Response('Missing Stripe signature', { status: 400 })
    const body = await req.text()
    const event = await stripe.webhooks.constructEventAsync(body, signature, webhookSecret, undefined, cryptoProvider)
    const admin = adminClient()

    const { data: processed, error: processedError } = await admin.from('webhook_events').select('id').eq('id', event.id).maybeSingle()
    if (processedError) throw processedError
    if (processed) return Response.json({ received: true, duplicate: true })

    switch (event.type) {
      case 'checkout.session.completed': {
        const checkout = event.data.object as Stripe.Checkout.Session
        const userId = checkout.metadata?.salesboard_user_id || checkout.client_reference_id
        const customerId = typeof checkout.customer === 'string' ? checkout.customer : checkout.customer?.id
        if (userId && customerId && await profileExists(admin, userId)) {
          const { error } = await admin.from('profiles').update({ stripe_customer_id: customerId }).eq('id', userId)
          if (error) throw error
        }
        if (checkout.subscription) {
          const subscriptionId = typeof checkout.subscription === 'string' ? checkout.subscription : checkout.subscription.id
          const subscription = await stripe.subscriptions.retrieve(subscriptionId)
          await syncSubscription(admin, subscription)
        }
        break
      }
      case 'customer.subscription.created':
      case 'customer.subscription.updated':
      case 'customer.subscription.deleted':
        await syncSubscription(admin, event.data.object as Stripe.Subscription)
        break
      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice
        const userId = await userIdForCustomer(admin, invoice.customer)
        if (userId && await profileExists(admin, userId)) {
          await admin.from('profiles').update({ subscription_status: 'past_due' }).eq('id', userId)
          await admin.from('subscriptions').update({ status: 'past_due' }).eq('user_id', userId)
        }
        break
      }
      case 'invoice.paid': {
        const invoice = event.data.object as Stripe.Invoice
        const subscriptionDetails = invoice.parent?.subscription_details
        const subscriptionId = subscriptionDetails?.subscription
        if (subscriptionId) {
          const id = typeof subscriptionId === 'string' ? subscriptionId : subscriptionId.id
          const subscription = await stripe.subscriptions.retrieve(id)
          await syncSubscription(admin, subscription)
        }
        break
      }
      default:
        break
    }

    const { error: eventError } = await admin.from('webhook_events').insert({ id: event.id, event_type: event.type })
    if (eventError && eventError.code !== '23505') throw eventError
    return Response.json({ received: true })
  } catch (error) {
    console.error(error)
    return new Response('Webhook processing failed', { status: 400 })
  }
})
