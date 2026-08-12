const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Content-Type': 'application/json',
  'Cache-Control': 'no-store'
}

Deno.serve((req) => {
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors })
  if (req.method !== 'GET') return new Response(JSON.stringify({ error: 'Método não permitido.' }), { status: 405, headers: cors })

  const checks = {
    supabase: Boolean(Deno.env.get('SUPABASE_URL') && (Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') || Deno.env.get('SUPABASE_SECRET_KEYS'))),
    stripeSecret: Boolean(Deno.env.get('STRIPE_SECRET_KEY')),
    stripeWebhook: Boolean(Deno.env.get('STRIPE_WEBHOOK_SECRET')),
    legalIdentity: Boolean(Deno.env.get('LEGAL_ENTITY_NAME') && Deno.env.get('LEGAL_ENTITY_ID')),
    contactChannels: Boolean(Deno.env.get('SUPPORT_EMAIL') && Deno.env.get('PRIVACY_EMAIL'))
  }
  const ready = Object.values(checks).every(Boolean)
  return new Response(JSON.stringify({ status: ready ? 'ready' : 'configuration_required', checks, timestamp: new Date().toISOString() }), { status: ready ? 200 : 503, headers: cors })
})
