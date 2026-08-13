from pathlib import Path

app = Path('salesboard/app/app.js')
html = Path('salesboard/app/index.html')
css = Path('salesboard/app/quality.css')
audit = Path('salesboard/scripts/ui_contract_audit.mjs')

app_text = app.read_text(encoding='utf-8')
html_text = html.read_text(encoding='utf-8')
css_text = css.read_text(encoding='utf-8')
audit_text = audit.read_text(encoding='utf-8')

# 1) Session preference state.
old = """  let session = null;\n  let currentView = 'dashboard';\n"""
new = """  let session = null;\n  const KEEP_CONNECTED_KEY = 'salesboard_keep_connected';\n  const SESSION_ONLY_KEY = 'salesboard_session_only';\n  let rememberSession = false;\n  let currentView = 'dashboard';\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'session state anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

# 2) Auth-only storage adapter: localStorage only for remembered sessions, sessionStorage otherwise.
anchor = """  function appBaseUrl(query = '') {\n    const url = new URL('./', location.href);\n    url.search = query ? (query.startsWith('?') ? query : `?${query}`) : '';\n    url.hash = '';\n    return url.href;\n  }\n\n"""
insert = anchor + """  function persistentAuthStorage() {\n    try { return window.localStorage; } catch { return null; }\n  }\n\n  function transientAuthStorage() {\n    try { return window.sessionStorage; } catch { return null; }\n  }\n\n  function initializeRememberPreference() {\n    const persistent = persistentAuthStorage();\n    const transient = transientAuthStorage();\n    try {\n      if (transient?.getItem(SESSION_ONLY_KEY) === '1') {\n        rememberSession = false;\n        return;\n      }\n      if (persistent?.getItem(KEEP_CONNECTED_KEY) === '1') {\n        rememberSession = true;\n        return;\n      }\n      // Preserve sessions created before the Keep Connected option existed.\n      const legacyPersistentSession = persistent\n        ? Object.keys(persistent).some((key) => key.startsWith('sb-') && key.endsWith('-auth-token') && Boolean(persistent.getItem(key)))\n        : false;\n      rememberSession = legacyPersistentSession;\n      if (legacyPersistentSession) persistent?.setItem(KEEP_CONNECTED_KEY, '1');\n    } catch {\n      rememberSession = false;\n    }\n  }\n\n  function setRememberPreference(enabled) {\n    rememberSession = Boolean(enabled);\n    const persistent = persistentAuthStorage();\n    const transient = transientAuthStorage();\n    try {\n      if (rememberSession) {\n        persistent?.setItem(KEEP_CONNECTED_KEY, '1');\n        transient?.removeItem(SESSION_ONLY_KEY);\n      } else {\n        persistent?.removeItem(KEEP_CONNECTED_KEY);\n        transient?.setItem(SESSION_ONLY_KEY, '1');\n      }\n    } catch {}\n  }\n\n  function clearRememberPreference() {\n    const persistent = persistentAuthStorage();\n    const transient = transientAuthStorage();\n    try {\n      persistent?.removeItem(KEEP_CONNECTED_KEY);\n      transient?.removeItem(SESSION_ONLY_KEY);\n    } catch {}\n    rememberSession = false;\n  }\n\n  const authSessionStorage = {\n    getItem(key) {\n      const storage = rememberSession ? persistentAuthStorage() : transientAuthStorage();\n      try { return storage?.getItem(key) ?? null; } catch { return null; }\n    },\n    setItem(key, value) {\n      const target = rememberSession ? persistentAuthStorage() : transientAuthStorage();\n      const alternate = rememberSession ? transientAuthStorage() : persistentAuthStorage();\n      try {\n        target?.setItem(key, value);\n        alternate?.removeItem(key);\n      } catch {}\n    },\n    removeItem(key) {\n      try { persistentAuthStorage()?.removeItem(key); } catch {}\n      try { transientAuthStorage()?.removeItem(key); } catch {}\n    }\n  };\n\n"""
if app_text.count(anchor) != 1:
    raise SystemExit(f'appBaseUrl anchor count={app_text.count(anchor)}')
app_text = app_text.replace(anchor, insert, 1)

# 3) Initialize preference before binding UI and give Supabase the storage adapter.
old = """  async function initialize() {\n    initStaticEvents();\n"""
new = """  async function initialize() {\n    initializeRememberPreference();\n    initStaticEvents();\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'initialize anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

old = """      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }\n"""
new = """      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, storage: authSessionStorage }\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'createClient auth anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

# 4) Google and password login both honor the checkbox.
old = """  async function signInWithGoogle() {\n    const button = $('#google-auth-button');\n    if (!supabaseClient) return;\n    setButtonLoading(button, true, 'Verificando Google...');\n"""
new = """  async function signInWithGoogle() {\n    const button = $('#google-auth-button');\n    if (!supabaseClient) return;\n    setRememberPreference(Boolean($('#keep-connected')?.checked));\n    setButtonLoading(button, true, 'Verificando Google...');\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'google login anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

old = """      if (!password) { setAuthMessage('Informe sua senha para entrar.', true); focusField('#login-password'); return; }\n      setButtonLoading(button, true, 'Entrando...');\n"""
new = """      if (!password) { setAuthMessage('Informe sua senha para entrar.', true); focusField('#login-password'); return; }\n      setRememberPreference(Boolean($('#keep-connected')?.checked));\n      setButtonLoading(button, true, 'Entrando...');\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'password login anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

# 5) The checkbox reflects the current persistence mode.
old = """    $('#google-auth-button')?.addEventListener('click', signInWithGoogle);\n"""
new = """    const keepConnected = $('#keep-connected');\n    if (keepConnected) keepConnected.checked = rememberSession;\n    $('#google-auth-button')?.addEventListener('click', signInWithGoogle);\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'keep-connected init anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

# 6) Explicit logout/password reset/account deletion reset the preference too.
old = """    await supabaseClient.auth.signOut();\n    location.href = './?mode=login';\n"""
new = """    await supabaseClient.auth.signOut();\n    clearRememberPreference();\n    location.href = './?mode=login';\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'logout anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

old = """        await supabaseClient.auth.signOut();\n        session = null;\n        history.replaceState({}, '', appBaseUrl());\n"""
new = """        await supabaseClient.auth.signOut();\n        clearRememberPreference();\n        session = null;\n        history.replaceState({}, '', appBaseUrl());\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'recovery logout anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

old = """      await supabaseClient.auth.signOut({ scope: 'local' });\n      location.href = '../?account=deleted';\n"""
new = """      await supabaseClient.auth.signOut({ scope: 'local' });\n      clearRememberPreference();\n      location.href = '../?account=deleted';\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'delete account logout anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

app.write_text(app_text, encoding='utf-8')

# 7) Login UI.
old = """<div class=\"form-inline auth-links\"><span class=\"auth-security-note\">Acesso protegido pelo Supabase</span><button type=\"button\" class=\"link-button\" id=\"forgot-password\">Esqueci a senha</button></div>"""
new = """<div class=\"form-inline auth-links\"><label class=\"keep-connected\" title=\"Em dispositivo pessoal, mantém sua sessão mesmo depois de fechar o navegador.\"><input id=\"keep-connected\" type=\"checkbox\" /><span>Manter conectado</span></label><button type=\"button\" class=\"link-button\" id=\"forgot-password\">Esqueci a senha</button></div>"""
if html_text.count(old) != 1:
    raise SystemExit(f'login links HTML anchor count={html_text.count(old)}')
html_text = html_text.replace(old, new, 1)
html.write_text(html_text, encoding='utf-8')

# 8) Styling / responsive behavior.
marker = """\n/* Keep-connected authentication control */\n.keep-connected{display:inline-flex;align-items:center;gap:8px;min-height:36px;color:#596579;font-size:12px;font-weight:650;cursor:pointer;user-select:none}\n.keep-connected input{width:16px!important;height:16px;margin:0!important;accent-color:var(--greenDark);cursor:pointer}\n.keep-connected span{line-height:1.25}\n@media(max-width:420px){.auth-links{align-items:center;gap:10px}.keep-connected{font-size:11px}.auth-links .link-button{white-space:nowrap}}\n"""
if '/* Keep-connected authentication control */' not in css_text:
    css_text = css_text.rstrip() + marker
css.write_text(css_text, encoding='utf-8')

# 9) Permanent UI contract markers.
old = """if (!appHtml.includes('id=\\\"resend-confirmation\\\"')) failures.push('static: ação de reenviar confirmação ausente');\n"""
new = old + """if (!appHtml.includes('id=\\\"keep-connected\\\"')) failures.push('static: opção Manter conectado ausente');\nfor (const marker of ['authSessionStorage', 'setRememberPreference', 'KEEP_CONNECTED_KEY', 'SESSION_ONLY_KEY']) {\n  if (!appSource.includes(marker)) failures.push(`static: persistência de sessão ausente: ${marker}`);\n}\n"""
if audit_text.count(old) != 1:
    raise SystemExit(f'audit marker anchor count={audit_text.count(old)}')
audit_text = audit_text.replace(old, new, 1)
audit_text = audit_text.replace(
    "PASS UI contract: alignment + billing/sidebar + confirmations + auth validation + archive/reactivate + historical editing",
    "PASS UI contract: alignment + billing/sidebar + confirmations + auth validation + keep-connected + archive/reactivate + historical editing",
    1
)
audit.write_text(audit_text, encoding='utf-8')

print('Keep Connected option added with persistent-vs-session Supabase Auth storage.')
