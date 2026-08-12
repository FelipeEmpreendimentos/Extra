from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'marker not found: {label}')
    return text.replace(old, new, 1)


# --- Auth HTML -------------------------------------------------------------
html_path = Path('salesboard/app/index.html')
html = html_path.read_text(encoding='utf-8')

html = html.replace(
    '<div class="form-inline"><label class="check"><input id="remember-session" type="checkbox" checked /> Manter conectado</label><button type="button" class="link-button" id="forgot-password">Esqueci a senha</button></div>',
    '<div class="form-inline auth-links"><span class="auth-security-note">Acesso protegido pelo Supabase</span><button type="button" class="link-button" id="forgot-password">Esqueci a senha</button></div>'
)

register_form = '<form id="register-form" class="stack-form"><label>Seu nome<input id="register-name" autocomplete="name" required maxlength="80" placeholder="Como podemos chamar você?" /></label><label>E-mail<input id="register-email" type="email" autocomplete="email" required placeholder="voce@exemplo.com" /></label><label>Senha<div class="password-field"><input id="register-password" type="password" autocomplete="new-password" required minlength="8" placeholder="Mínimo de 8 caracteres" /><button type="button" data-toggle-password="register-password" aria-label="Mostrar senha">◉</button></div></label><label class="check terms-check"><input id="accept-terms" type="checkbox" required /> <span>Li e aceito os <a href="../legal/termos.html" target="_blank" rel="noopener">Termos de Uso</a> e a <a href="../legal/privacidade.html" target="_blank" rel="noopener">Política de Privacidade</a>.</span></label><button class="button primary wide" type="submit">Criar conta grátis</button></form>'
register_new = register_form + '<button type="button" class="button subtle wide auth-secondary-action" id="resend-confirmation" hidden>Reenviar e-mail de confirmação</button>'
if 'id="resend-confirmation"' not in html:
    html = replace_once(html, register_form, register_new, 'register form')

forgot_screen = '''\n  <section id="forgot-screen" class="center-screen" hidden>\n    <div class="setup-card auth-flow-card">\n      <span class="brand-mark"><i></i><i></i><i></i></span>\n      <span class="kicker">Recuperar acesso</span>\n      <h1>Redefina sua senha</h1>\n      <p>Informe o e-mail da sua conta. Se ele estiver cadastrado, você receberá um link seguro para criar uma nova senha.</p>\n      <form id="forgot-form" class="stack-form">\n        <label>E-mail<input id="forgot-email" type="email" autocomplete="email" required placeholder="voce@exemplo.com" /></label>\n        <button class="button primary wide" type="submit">Enviar link de recuperação</button>\n      </form>\n      <div id="forgot-status" class="auth-message" hidden></div>\n      <button type="button" class="link-button auth-flow-back" id="forgot-back">← Voltar para o login</button>\n    </div>\n  </section>\n'''
if 'id="forgot-screen"' not in html:
    html = replace_once(html, '\n  <section id="recovery-screen"', forgot_screen + '\n  <section id="recovery-screen"', 'forgot screen insertion')

old_recovery = '<section id="recovery-screen" class="center-screen" hidden>\n    <div class="setup-card"><span class="brand-mark"><i></i><i></i><i></i></span><h1>Defina uma nova senha</h1><p>Use pelo menos 8 caracteres.</p><form id="recovery-form" class="stack-form"><label>Nova senha<input id="recovery-password" type="password" minlength="8" required autocomplete="new-password" /></label><button class="button primary wide" type="submit">Atualizar senha</button></form></div>\n  </section>'
new_recovery = '''<section id="recovery-screen" class="center-screen" hidden>\n    <div class="setup-card auth-flow-card"><span class="brand-mark"><i></i><i></i><i></i></span><span class="kicker">Link verificado</span><h1>Defina uma nova senha</h1><p>Escolha uma senha com pelo menos 8 caracteres e confirme antes de salvar.</p><form id="recovery-form" class="stack-form"><label>Nova senha<div class="password-field"><input id="recovery-password" type="password" minlength="8" required autocomplete="new-password" /><button type="button" data-toggle-password="recovery-password" aria-label="Mostrar senha">◉</button></div></label><label>Confirmar nova senha<div class="password-field"><input id="recovery-password-confirm" type="password" minlength="8" required autocomplete="new-password" /><button type="button" data-toggle-password="recovery-password-confirm" aria-label="Mostrar senha">◉</button></div></label><div class="password-rules"><span id="rule-length">○ 8 ou mais caracteres</span><span id="rule-match">○ As duas senhas são iguais</span></div><button class="button primary wide" type="submit">Salvar nova senha</button></form><div id="recovery-message" class="auth-message" hidden></div></div>\n  </section>'''
html = replace_once(html, old_recovery, new_recovery, 'recovery screen')
html_path.write_text(html, encoding='utf-8')


# --- Auth + billing frontend logic -----------------------------------------
js_path = Path('salesboard/app/app.js')
js = js_path.read_text(encoding='utf-8')

js = js.replace("['boot-screen', 'setup-error', 'auth-screen', 'recovery-screen', 'onboarding-screen', 'paywall-screen', 'app-shell']", "['boot-screen', 'setup-error', 'auth-screen', 'forgot-screen', 'recovery-screen', 'onboarding-screen', 'paywall-screen', 'app-shell']")

helper_marker = "  function profileEntitlement() {"
helpers = '''  function appBaseUrl(query = '') {\n    const url = new URL('./', location.href);\n    url.search = query ? (query.startsWith('?') ? query : `?${query}`) : '';\n    url.hash = '';\n    return url.href;\n  }\n\n  function authErrorMessage(error) {\n    const code = String(error?.code || '').toLowerCase();\n    const message = String(error?.message || error || '').toLowerCase();\n    if (code === 'email_not_confirmed' || message.includes('email not confirmed')) return 'Seu e-mail ainda não foi confirmado. Abra o e-mail enviado pelo SalesBoard e confirme sua conta antes de entrar.';\n    if (code === 'invalid_credentials' || message.includes('invalid login credentials')) return 'E-mail ou senha incorretos. Confira os dados e tente novamente.';\n    if (code === 'over_email_send_rate_limit' || message.includes('after 45 seconds') || message.includes('rate limit')) return 'Aguarde alguns segundos antes de pedir outro e-mail. Isso protege sua conta contra abuso.';\n    if (message.includes('provider is not enabled')) return 'O login com Google ainda não foi ativado no servidor. Use e-mail e senha por enquanto.';\n    if (code === 'user_already_exists' || message.includes('already registered') || message.includes('already exists')) return 'Já existe uma conta com este e-mail. Entre normalmente ou use “Esqueci a senha”.';\n    if (message.includes('password should be')) return 'A senha não atende aos requisitos de segurança. Use pelo menos 8 caracteres.';\n    return friendlyError(error);\n  }\n\n  function setInlineMessage(selector, message, error = false) {\n    const box = $(selector);\n    if (!box) return;\n    box.hidden = !message;\n    box.textContent = message || '';\n    box.classList.toggle('error', Boolean(error));\n  }\n\n  async function waitForBillingSync(attempts = 8) {\n    if (demoMode || !supabaseClient || !state.user) return;\n    for (let attempt = 0; attempt < attempts; attempt += 1) {\n      const { data } = await supabaseClient.from('profiles').select('*').eq('id', state.user.id).maybeSingle();\n      if (data) state.profile = data;\n      if (data?.subscription_status === 'active') return;\n      await new Promise((resolve) => setTimeout(resolve, 750));\n    }\n  }\n\n'''
if 'function authErrorMessage(error)' not in js:
    js = replace_once(js, helper_marker, helpers + helper_marker, 'auth helper marker')

# Make checkout return wait for webhook before deciding entitlement.
old_init_profile = "    state.profile = profile;\n\n    if (!profile.onboarded) {"
new_init_profile = "    state.profile = profile;\n\n    if (params.get('checkout') === 'success') await waitForBillingSync();\n\n    if (!state.profile.onboarded) {"
js = replace_once(js, old_init_profile, new_init_profile, 'billing sync after checkout')
js = js.replace("    if (!profile.onboarded) {", "    if (!state.profile.onboarded) {", 1)

# Replace generic login error.
js = js.replace("        setAuthMessage('E-mail ou senha inválidos. Confira os dados e tente novamente.', true);", "        setAuthMessage(authErrorMessage(error), true);")

# Signup: clearer status and resend availability.
signup_success_old = "        if (data.session) { session = data.session; await initializeAuthenticatedUser(); }\n        else setAuthMessage('Conta criada. Confirme o link enviado ao seu e-mail para liberar o acesso.');"
signup_success_new = "        if (data.session) { session = data.session; await initializeAuthenticatedUser(); }\n        else {\n          $('#resend-confirmation').dataset.email = email;\n          $('#resend-confirmation').hidden = false;\n          setAuthMessage('Conta criada. Enviamos um e-mail de confirmação. Abra o link recebido para validar sua conta e então faça login.');\n        }"
if signup_success_old in js:
    js = js.replace(signup_success_old, signup_success_new, 1)

# Replace signup friendly error if present.
js = js.replace("        setAuthMessage(friendlyError(error), true);", "        setAuthMessage(authErrorMessage(error), true);", 1)

# OAuth: use skipBrowserRedirect so disabled provider is handled inside our UI.
old_google = '''  async function signInWithGoogle() {\n    const button = $('#google-auth-button');\n    if (!supabaseClient) return;\n    setButtonLoading(button, true, 'Abrindo Google...');\n    setAuthMessage('');\n    try {\n      const redirectTo = `${location.origin}${location.pathname}?oauth=google`;\n      const { error } = await supabaseClient.auth.signInWithOAuth({\n        provider: 'google',\n        options: { redirectTo, queryParams: { prompt: 'select_account' } }\n      });\n      if (error) throw error;\n    } catch (error) {\n      setButtonLoading(button, false);\n      const message = String(error?.message || error || '');\n      setAuthMessage(message.toLowerCase().includes('provider') ? 'O login com Google ainda precisa ser ativado no Supabase Auth. Use e-mail e senha enquanto a configuração externa não estiver concluída.' : friendlyError(error), true);\n    }\n  }'''
new_google = '''  async function signInWithGoogle() {\n    const button = $('#google-auth-button');\n    if (!supabaseClient) return;\n    setButtonLoading(button, true, 'Abrindo Google...');\n    setAuthMessage('');\n    try {\n      sessionStorage.setItem('salesboard_oauth_intent', JSON.stringify({ plan: requestedPlan, billing: billingCycle, createdAt: Date.now() }));\n      const { data, error } = await supabaseClient.auth.signInWithOAuth({\n        provider: 'google',\n        options: { redirectTo: appBaseUrl('oauth=google'), skipBrowserRedirect: true, queryParams: { prompt: 'select_account' } }\n      });\n      if (error) throw error;\n      if (!data?.url) throw new Error('Não foi possível iniciar o login com Google.');\n      location.assign(data.url);\n    } catch (error) {\n      setButtonLoading(button, false);\n      setAuthMessage(authErrorMessage(error), true);\n    }\n  }'''
js = replace_once(js, old_google, new_google, 'google oauth function')

# Forgot password old prompt handler -> dedicated screen flow.
old_forgot = '''    $('#forgot-password').addEventListener('click', async () => {\n      const email = $('#login-email').value.trim() || prompt('Qual e-mail está cadastrado na sua conta?') || '';\n      if (!email) return;\n      try {\n        const { error } = await supabaseClient.auth.resetPasswordForEmail(email, { redirectTo: `${location.origin}${location.pathname}?recovery=1` });\n        if (error) throw error;\n        setAuthMessage('Enviamos um link de recuperação para o seu e-mail.');\n      } catch (error) {\n        setAuthMessage(friendlyError(error), true);\n      }\n    });'''
new_forgot = '''    $('#forgot-password').addEventListener('click', () => {\n      $('#forgot-email').value = $('#login-email').value.trim();\n      setInlineMessage('#forgot-status', '');\n      showOnly('forgot-screen');\n    });\n    $('#forgot-back').addEventListener('click', () => showAuth('login'));\n    $('#forgot-form').addEventListener('submit', async (event) => {\n      event.preventDefault();\n      const button = event.currentTarget.querySelector('button[type="submit"]');\n      const email = $('#forgot-email').value.trim();\n      setButtonLoading(button, true, 'Enviando...');\n      setInlineMessage('#forgot-status', '');\n      try {\n        const { error } = await supabaseClient.auth.resetPasswordForEmail(email, { redirectTo: appBaseUrl('recovery=1') });\n        if (error) throw error;\n        setInlineMessage('#forgot-status', 'Se este e-mail estiver cadastrado, o link de recuperação foi enviado. Confira também a caixa de spam.');\n      } catch (error) {\n        setInlineMessage('#forgot-status', authErrorMessage(error), true);\n      } finally {\n        setButtonLoading(button, false);\n      }\n    });\n    $('#resend-confirmation').addEventListener('click', async (event) => {\n      const button = event.currentTarget;\n      const email = button.dataset.email || $('#register-email').value.trim();\n      if (!email) return;\n      setButtonLoading(button, true, 'Reenviando...');\n      try {\n        const { error } = await supabaseClient.auth.resend({ type: 'signup', email, options: { emailRedirectTo: appBaseUrl() } });\n        if (error) throw error;\n        setAuthMessage('Novo e-mail de confirmação enviado. Aguarde pelo menos 45 segundos antes de pedir outro.');\n      } catch (error) {\n        setAuthMessage(authErrorMessage(error), true);\n      } finally {\n        setTimeout(() => setButtonLoading(button, false), 45000);\n      }\n    });'''
js = replace_once(js, old_forgot, new_forgot, 'forgot password handler')

# Password recovery: confirm + logout after update.
old_recovery_js = '''    $('#recovery-form').addEventListener('submit', async (event) => {\n      event.preventDefault();\n      try {\n        const { error } = await supabaseClient.auth.updateUser({ password: $('#recovery-password').value });\n        if (error) throw error;\n        toast('Senha atualizada');\n        history.replaceState({}, '', './');\n        await initializeAuthenticatedUser();\n      } catch (error) {\n        toast('Não foi possível atualizar', friendlyError(error), 'error');\n      }\n    });'''
new_recovery_js = '''    const updateRecoveryRules = () => {\n      const password = $('#recovery-password').value;\n      const confirmPassword = $('#recovery-password-confirm').value;\n      $('#rule-length').textContent = `${password.length >= 8 ? '✓' : '○'} 8 ou mais caracteres`;\n      $('#rule-match').textContent = `${password && password === confirmPassword ? '✓' : '○'} As duas senhas são iguais`;\n    };\n    $('#recovery-password').addEventListener('input', updateRecoveryRules);\n    $('#recovery-password-confirm').addEventListener('input', updateRecoveryRules);\n    $('#recovery-form').addEventListener('submit', async (event) => {\n      event.preventDefault();\n      const button = event.currentTarget.querySelector('button[type="submit"]');\n      const password = $('#recovery-password').value;\n      const confirmPassword = $('#recovery-password-confirm').value;\n      if (password.length < 8) return setInlineMessage('#recovery-message', 'Use pelo menos 8 caracteres.', true);\n      if (password !== confirmPassword) return setInlineMessage('#recovery-message', 'As duas senhas precisam ser iguais.', true);\n      setButtonLoading(button, true, 'Salvando...');\n      setInlineMessage('#recovery-message', '');\n      try {\n        const email = session?.user?.email || '';\n        const { error } = await supabaseClient.auth.updateUser({ password });\n        if (error) throw error;\n        await supabaseClient.auth.signOut();\n        session = null;\n        history.replaceState({}, '', appBaseUrl());\n        showAuth('login');\n        if (email) $('#login-email').value = email;\n        setAuthMessage('Senha atualizada com sucesso. Entre novamente usando sua nova senha.');\n      } catch (error) {\n        setInlineMessage('#recovery-message', authErrorMessage(error), true);\n      } finally {\n        setButtonLoading(button, false);\n      }\n    });'''
js = replace_once(js, old_recovery_js, new_recovery_js, 'recovery submit handler')

# Checkout request id for server-side idempotency.
old_checkout_body = "body: JSON.stringify({ plan, billingCycle })"
new_checkout_body = "body: JSON.stringify({ plan, billingCycle, requestId: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}` })"
js = js.replace(old_checkout_body, new_checkout_body)

js_path.write_text(js, encoding='utf-8')


# --- Styling ---------------------------------------------------------------
css_path = Path('salesboard/app/app.css')
css = css_path.read_text(encoding='utf-8')
marker = '/* SalesBoard auth and billing repair 2026-08 */'
if marker not in css:
    css += '''\n\n/* SalesBoard auth and billing repair 2026-08 */\n.auth-security-note{font-size:10px;color:#98a2b3}.auth-secondary-action{margin-top:12px}.auth-flow-card{text-align:left}.auth-flow-card>.brand-mark{margin:0 auto 18px}.auth-flow-card>.kicker{display:block;text-align:center}.auth-flow-card>h1,.auth-flow-card>p{text-align:center}.auth-flow-back{display:block;margin:20px auto 0}.password-rules{display:grid;gap:6px;padding:10px 12px;background:#f8fafc;border:1px solid var(--line);border-radius:10px;color:#667085;font-size:10px}.password-rules span{display:block}.auth-links{min-height:22px}@media(max-width:520px){.auth-security-note{display:none}.auth-links{justify-content:flex-end}}\n'''
    css_path.write_text(css, encoding='utf-8')


# --- Versioned Supabase Edge Function source ------------------------------
functions = Path('salesboard/supabase/functions')
checkout_dir = functions / 'salesboard-checkout'
portal_dir = functions / 'salesboard-billing-portal'
checkout_dir.mkdir(parents=True, exist_ok=True)
portal_dir.mkdir(parents=True, exist_ok=True)

checkout_code = r'''import { createClient } from 'npm:@supabase/supabase-js@2.111.0'

const PROD_ORIGIN = 'https://felipeempreendimentos.github.io'
const priceMap: Record<string, string> = {
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

async function stripeRequest(path: string, init: RequestInit = {}, idempotencyKey?: string) {
  const secret = Deno.env.get('STRIPE_SECRET_KEY')
  if (!secret) throw new Error('STRIPE_NOT_CONFIGURED')
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
    params.set('line_items[0][price]', priceMap[`${plan}:${billingCycle}`])
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
    const message = error instanceof Error && error.message === 'STRIPE_NOT_CONFIGURED'
      ? 'Cobrança ainda não configurada no servidor.'
      : 'Não foi possível iniciar o checkout. Tente novamente em instantes.'
    return new Response(JSON.stringify({ error: message }), { status: 500, headers })
  }
})
'''
checkout_dir.joinpath('index.ts').write_text(checkout_code, encoding='utf-8')

portal_code = r'''import { createClient } from 'npm:@supabase/supabase-js@2.111.0'

const PROD_ORIGIN = 'https://felipeempreendimentos.github.io'
const ESSENTIAL_PRODUCT = 'prod_V3mP62OMS5pAmt'
const PRO_PRODUCT = 'prod_V3mPwwBjaVkm8E'
const ESSENTIAL_PRICES = ['price_1U3eqnRlODNbnkUiLRDXlIZm', 'price_1U3erCRlODNbnkUiYSxDq1e6']
const PRO_PRICES = ['price_1U3eqyRlODNbnkUirbXIqvR8', 'price_1U3erNRlODNbnkUiCYny1NeZ']

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

async function stripeRequest(path: string, init: RequestInit = {}) {
  const secret = Deno.env.get('STRIPE_SECRET_KEY')
  if (!secret) throw new Error('STRIPE_NOT_CONFIGURED')
  const response = await fetch(`https://api.stripe.com/v1${path}`, {
    ...init,
    headers: { Authorization: `Bearer ${secret}`, 'Content-Type': 'application/x-www-form-urlencoded', ...(init.headers || {}) }
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data?.error?.message || 'Stripe request failed')
  return data
}

async function ensurePortalConfiguration(returnUrl: string) {
  const existing = await stripeRequest('/billing_portal/configurations?active=true&limit=10', { method: 'GET' })
  const salesboardConfig = (existing.data || []).find((item: any) => item.metadata?.salesboard === 'true')
  if (salesboardConfig) return salesboardConfig.id

  const body = new URLSearchParams()
  body.set('default_return_url', returnUrl)
  body.set('business_profile[headline]', 'Gerencie sua assinatura do SalesBoard Finance')
  body.set('business_profile[privacy_policy_url]', `${PROD_ORIGIN}/Extra/salesboard/legal/privacidade.html`)
  body.set('business_profile[terms_of_service_url]', `${PROD_ORIGIN}/Extra/salesboard/legal/termos.html`)
  body.set('features[payment_method_update][enabled]', 'true')
  body.set('features[invoice_history][enabled]', 'true')
  body.set('features[subscription_cancel][enabled]', 'true')
  body.set('features[subscription_cancel][mode]', 'at_period_end')
  body.set('features[subscription_update][enabled]', 'true')
  body.set('features[subscription_update][default_allowed_updates][0]', 'price')
  body.set('features[subscription_update][proration_behavior]', 'create_prorations')
  body.set('features[subscription_update][products][0][product]', ESSENTIAL_PRODUCT)
  ESSENTIAL_PRICES.forEach((price, index) => body.set(`features[subscription_update][products][0][prices][${index}]`, price))
  body.set('features[subscription_update][products][1][product]', PRO_PRODUCT)
  PRO_PRICES.forEach((price, index) => body.set(`features[subscription_update][products][1][prices][${index}]`, price))
  body.set('metadata[salesboard]', 'true')
  const config = await stripeRequest('/billing_portal/configurations', { method: 'POST', body })
  return config.id
}

Deno.serve(async (req) => {
  const headers = cors(req)
  if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers })
  if (req.method !== 'POST') return new Response(JSON.stringify({ error: 'Método não permitido.' }), { status: 405, headers })

  try {
    const token = (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '')
    if (!token) return new Response(JSON.stringify({ error: 'Sessão necessária.' }), { status: 401, headers })
    const admin = adminClient()
    const { data, error } = await admin.auth.getUser(token)
    if (error || !data?.user) return new Response(JSON.stringify({ error: 'Sessão inválida.' }), { status: 401, headers })

    const { data: profile, error: profileError } = await admin.from('profiles').select('stripe_customer_id').eq('id', data.user.id).single()
    if (profileError) throw profileError
    if (!profile.stripe_customer_id) return new Response(JSON.stringify({ error: 'Nenhuma cobrança encontrada para esta conta.' }), { status: 404, headers })

    const origin = allowedOrigin(req)
    const returnUrl = origin.includes('github.io') ? `${PROD_ORIGIN}/Extra/salesboard/app/?view=billing` : `${origin.replace(/\/$/, '')}/app/?view=billing`
    const configuration = await ensurePortalConfiguration(returnUrl)
    const params = new URLSearchParams({ customer: profile.stripe_customer_id, return_url: returnUrl, configuration })
    const portal = await stripeRequest('/billing_portal/sessions', { method: 'POST', body: params })
    return new Response(JSON.stringify({ url: portal.url }), { status: 200, headers })
  } catch (error) {
    console.error(error)
    const raw = String(error instanceof Error ? error.message : error)
    const message = raw === 'STRIPE_NOT_CONFIGURED' ? 'Cobrança ainda não configurada no servidor.' : `Não foi possível abrir o portal de cobrança. ${raw.includes('configuration') ? 'A configuração do portal precisa ser revisada no Stripe.' : ''}`.trim()
    return new Response(JSON.stringify({ error: message }), { status: 500, headers })
  }
})
'''
portal_dir.joinpath('index.ts').write_text(portal_code, encoding='utf-8')

# Lightweight static checks.
assert 'forgot-screen' in html_path.read_text(encoding='utf-8')
assert 'recovery-password-confirm' in html_path.read_text(encoding='utf-8')
assert 'skipBrowserRedirect: true' in js_path.read_text(encoding='utf-8')
assert 'resetPasswordForEmail' in js_path.read_text(encoding='utf-8')
assert 'requestId:' in js_path.read_text(encoding='utf-8')
print('SalesBoard auth + billing patch applied')
