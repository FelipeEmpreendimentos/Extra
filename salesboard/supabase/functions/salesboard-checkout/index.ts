import { createClient } from 'npm:@supabase/supabase-js@2.111.0'

const PROD_ORIGIN = 'https://felipeempreendimentos.github.io'
const TEST_PRICES: Record<string, string> = {
  'essential:monthly': 'price_1U3eqnRlODNbnkUiLRDXlIZm',
  'essential:annual': 'price_1U3erCRlODNbnkUiYSxDq1e6',
  'pro:monthly': 'price_1U3eqyRlODNbnkUirbXIqvR8',
  'pro:annual': 'price_1U3erNRlODNbnkUiCYny1NeZ'
}

function allowedOrigin(req: Request) {
  const origin = req.headers.get('origin') || ''
  if (origin === PROD_ORIGIN || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)) return origin
  return PROD_ORIGIN
}

function cors(req: Request) {
  return {
    'Access-Control-Allow-Origin': allowedOrigin(req),
    'Access-Control-Allow-Headers': 'authorization, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Content-Type': 'application/json',
    'Cache-Control': 'no-store',
    'Vary': 'Origin'
  }
}

function adminClient() {
  const url = Deno.env.get('SUPABASE_URL')!
  const legacy = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')
  const modern = Deno.env.get('SUPABASE_SECRET_KEYS')
  const key = legacy || (modern ? JSON.parse(modern).default : '')
  if (!url || !key) throw new Error('SUPABASE_NOT_CONFIGURED')
  return createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } })
}

function stripeSecret() {
  const secret = Deno.env.get('STRIPE_SECRET_KEY') || ''
  if (!secret) throw new Error('STRIPE_NOT_CONFIGURED')
  return secret
}

function stripePrice(plan: 'essential' | 'pro', cycle: 'monthly' | 'annual') {
  const secret = stripeSecret()
  const envName = `STRIPE_PRICE_${plan.toUpperCase()}_${cycle.toUpperCase()}`
  const configured = Deno.env.get(envName)
  if (configured) return configured
  if (secret.startsWith('sk_test_')) return TEST_PRICES[`${plan}:${cycle}`]
  throw new Error('STRIPE_CATALOG_NOT_CONFIGURED')
}

async function stripeRequest(path: string, init: RequestInit = {}, idempotencyKey?: string) {
  const secret = stripeSecret()
  const headers: Record<string, string> = {
    Authorization: `Bearer ${secret}`,
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  if (idempotencyKey) headers['Idempotency-Key'] = idempotencyKey
  const response = await fetch(`https://api.stripe.com/v1${path}`, { ...init, headers: { ...headers, ...(init.headers || {}) } })
  const data = await response.json()
  if (!response.ok) {
    const error = new Error(data?.error?.message || 'Stripe request failed')
    ;(error as any).stripeCode = data?.error?.code || null
    throw error
  }
  return data
}

Deno.serve(async (req) => {
  const headers = cors(req)
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers })
  if (req.method !== 'POST') return new Response(JSON.stringify({ error: 'Método não permitido.' }), { status: 405, headers })

  try {
    const token = (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '')
    if (!token) return new Response(JSON.stringify({ error: 'Sessão necessária.' }), { status: 401, headers })

    const admin = adminClient()
    const { data: authData, error: authError } = await admin.auth.getUser(token)
    const user = authData?.user
    if (authError || !user) return new Response(JSON.stringify({ error: 'Sessão inválida.' }), { status: 401, headers })

    const body = await req.json().catch(() => ({}))
    const plan = body.plan === 'essential' ? 'essential' : body.plan === 'pro' ? 'pro' : null
    const billingCycle = body.billingCycle === 'annual' ? 'annual' : body.billingCycle === 'monthly' ? 'monthly' : null
    const requestId = typeof body.requestId === 'string' && /^[A-Za-z0-9_-]{8,100}$/.test(body.requestId) ? body.requestId : crypto.randomUUID()
    if (!plan || !billingCycle) return new Response(JSON.stringify({ error: 'Plano inválido.' }), { status: 400, headers })

    const [{ data: profile, error: profileError }, { data: subscription, error: subError }] = await Promise.all([
      admin.from('profiles').select('stripe_customer_id,subscription_status').eq('id', user.id).single(),
      admin.from('subscriptions').select('stripe_subscription_id,status').eq('user_id', user.id).maybeSingle()
    ])
    if (profileError) throw profileError
    if (subError) throw subError
    if (profile.subscription_status === 'active' || ['active', 'trialing', 'past_due'].includes(subscription?.status || '')) {
      return new Response(JSON.stringify({ code: 'SUBSCRIPTION_EXISTS', portalRecommended: true, error: 'Já existe uma assinatura vinculada a esta conta. Use “Gerenciar cobrança” para atualizar pagamento, plano ou cancelamento.' }), { status: 409, headers })
    }

    let customerId = profile.stripe_customer_id
    if (!customerId) {
      const customerBody = new URLSearchParams()
      if (user.email) customerBody.set('email', user.email)
      customerBody.set('metadata[salesboard_user_id]', user.id)
      const customer = await stripeRequest('/customers', { method: 'POST', body: customerBody }, `salesboard-customer-${user.id}`)
      customerId = customer.id
      const { error } = await admin.from('profiles').update({ stripe_customer_id: customerId }).eq('id', user.id)
      if (error) throw error
    }

    const origin = allowedOrigin(req)
    const appUrl = origin.includes('github.io') ? `${PROD_ORIGIN}/Extra/salesboard/app/` : `${origin.replace(/\/$/, '')}/app/`
    const params = new URLSearchParams()
    params.set('mode', 'subscription')
    params.set('customer', customerId)
    params.set('line_items[0][price]', stripePrice(plan, billingCycle))
    params.set('line_items[0][quantity]', '1')
    params.set('success_url', `${appUrl}?checkout=success`)
    params.set('cancel_url', `${appUrl}?checkout=cancelled`)
    params.set('client_reference_id', user.id)
    params.set('metadata[salesboard_user_id]', user.id)
    params.set('metadata[salesboard_plan]', plan)
    params.set('metadata[billing_cycle]', billingCycle)
    params.set('subscription_data[metadata][salesboard_user_id]', user.id)
    params.set('subscription_data[metadata][salesboard_plan]', plan)
    params.set('subscription_data[metadata][billing_cycle]', billingCycle)
    params.set('allow_promotion_codes', 'true')
    params.set('locale', 'pt-BR')

    const checkout = await stripeRequest('/checkout/sessions', { method: 'POST', body: params }, `salesboard-checkout-${user.id}-${requestId}`)
    return new Response(JSON.stringify({ id: checkout.id, url: checkout.url }), { status: 200, headers })
  } catch (error) {
    console.error(error)
    const raw = error instanceof Error ? error.message : String(error)
    const message = raw === 'STRIPE_NOT_CONFIGURED'
      ? 'Cobrança ainda não configurada no servidor.'
      : raw === 'STRIPE_CATALOG_NOT_CONFIGURED'
        ? 'Catálogo de cobrança de produção ainda não configurado.'
        : 'Não foi possível iniciar o checkout. Tente novamente em instantes.'
    return new Response(JSON.stringify({ error: message }), { status: 500, headers })
  }
})
