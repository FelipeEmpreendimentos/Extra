import { createClient } from 'npm:@supabase/supabase-js@2.111.0'

const PROD_ORIGIN = 'https://felipeempreendimentos.github.io'

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

async function cancelStripeSubscription(subscriptionId: string) {
  const secret = Deno.env.get('STRIPE_SECRET_KEY')
  if (!secret) throw new Error('STRIPE_NOT_CONFIGURED')
  const response = await fetch(`https://api.stripe.com/v1/subscriptions/${encodeURIComponent(subscriptionId)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${secret}` }
  })
  if (response.status === 404) return
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data?.error?.message || 'Stripe cancellation failed')
}

Deno.serve(async (req) => {
  const headers = cors(req)
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers })
  if (req.method !== 'POST') return new Response(JSON.stringify({ error: 'Método não permitido.' }), { status: 405, headers })

  try {
    const token = (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '')
    if (!token) return new Response(JSON.stringify({ error: 'Sessão necessária.' }), { status: 401, headers })

    const body = await req.json().catch(() => ({}))
    if (body.confirmation !== 'EXCLUIR') return new Response(JSON.stringify({ error: 'Confirmação inválida.' }), { status: 400, headers })

    const admin = adminClient()
    const { data, error } = await admin.auth.getUser(token)
    const user = data?.user
    if (error || !user) return new Response(JSON.stringify({ error: 'Sessão inválida.' }), { status: 401, headers })

    // Trial eligibility is claimed only by start_salesboard_trial().
    // Deleting an account that never started a trial must not consume the one-time trial.
    const { data: subscription, error: subscriptionError } = await admin
      .from('subscriptions')
      .select('stripe_subscription_id,status')
      .eq('user_id', user.id)
      .maybeSingle()
    if (subscriptionError) throw subscriptionError

    if (subscription?.stripe_subscription_id && subscription.status !== 'canceled') {
      await cancelStripeSubscription(subscription.stripe_subscription_id)
    }

    const { error: deleteError } = await admin.auth.admin.deleteUser(user.id)
    if (deleteError) throw deleteError

    return new Response(JSON.stringify({ deleted: true }), { status: 200, headers })
  } catch (error) {
    console.error(error)
    const message = error instanceof Error && error.message === 'STRIPE_NOT_CONFIGURED'
      ? 'Não é seguro excluir uma conta com assinatura enquanto o Stripe não estiver configurado.'
      : 'Não foi possível excluir a conta. Tente novamente.'
    return new Response(JSON.stringify({ error: message }), { status: 500, headers })
  }
})
