from pathlib import Path

app = Path('salesboard/app/app.js')
css = Path('salesboard/app/quality.css')
audit = Path('salesboard/scripts/ui_contract_audit.mjs')

app_text = app.read_text(encoding='utf-8')
css_text = css.read_text(encoding='utf-8')
audit_text = audit.read_text(encoding='utf-8')

# OAuth preference marker: keep Supabase Auth persistent only while crossing the Google redirect.
old = """  const KEEP_CONNECTED_KEY = 'salesboard_keep_connected';\n  const SESSION_ONLY_KEY = 'salesboard_session_only';\n  let rememberSession = false;\n"""
new = """  const KEEP_CONNECTED_KEY = 'salesboard_keep_connected';\n  const SESSION_ONLY_KEY = 'salesboard_session_only';\n  const OAUTH_REMEMBER_KEY = 'salesboard_oauth_remember';\n  let rememberSession = false;\n"""
if old not in app_text:
    raise SystemExit('keep-connected constants anchor missing')
app_text = app_text.replace(old, new, 1)

# When returning from Google, force the Supabase client to read the persistent auth token first.
old = """    try {\n      if (transient?.getItem(SESSION_ONLY_KEY) === '1') {\n        rememberSession = false;\n        return;\n      }\n"""
new = """    try {\n      const oauthRemember = persistent?.getItem(OAUTH_REMEMBER_KEY);\n      if (oauthRemember === '0' || oauthRemember === '1') {\n        // OAuth may leave the app and return through another mobile browser process.\n        // Use persistent storage only for that round-trip; the user's preference is\n        // restored immediately after Supabase has rebuilt the session.\n        rememberSession = true;\n        return;\n      }\n      if (transient?.getItem(SESSION_ONLY_KEY) === '1') {\n        rememberSession = false;\n        return;\n      }\n"""
if old not in app_text:
    raise SystemExit('initializeRememberPreference anchor missing')
app_text = app_text.replace(old, new, 1)

# Helpers to move only Supabase Auth tokens between persistent and session storage.
anchor = """  function clearRememberPreference() {\n    const persistent = persistentAuthStorage();\n    const transient = transientAuthStorage();\n    try {\n      persistent?.removeItem(KEEP_CONNECTED_KEY);\n      transient?.removeItem(SESSION_ONLY_KEY);\n    } catch {}\n    rememberSession = false;\n  }\n\n"""
insert = anchor + """  function authTokenKeys(storage) {\n    if (!storage) return [];\n    try {\n      return Object.keys(storage).filter((key) => key.startsWith('sb-') && key.endsWith('-auth-token'));\n    } catch {\n      return [];\n    }\n  }\n\n  function migrateAuthTokens(fromStorage, toStorage) {\n    if (!fromStorage || !toStorage || fromStorage === toStorage) return;\n    for (const key of authTokenKeys(fromStorage)) {\n      try {\n        const value = fromStorage.getItem(key);\n        if (value) toStorage.setItem(key, value);\n        fromStorage.removeItem(key);\n      } catch {}\n    }\n  }\n\n  function prepareGoogleOAuthStorage(shouldRemember) {\n    const persistent = persistentAuthStorage();\n    const transient = transientAuthStorage();\n    try {\n      persistent?.setItem(OAUTH_REMEMBER_KEY, shouldRemember ? '1' : '0');\n      transient?.removeItem(SESSION_ONLY_KEY);\n    } catch {}\n    // Google OAuth must survive leaving the current mobile webview/browser process.\n    rememberSession = true;\n  }\n\n  function finalizeGoogleOAuthStorage() {\n    const persistent = persistentAuthStorage();\n    const transient = transientAuthStorage();\n    let preference = null;\n    try { preference = persistent?.getItem(OAUTH_REMEMBER_KEY); } catch {}\n    if (preference !== '0' && preference !== '1') return;\n\n    const shouldRemember = preference === '1';\n    if (shouldRemember) {\n      migrateAuthTokens(transient, persistent);\n      rememberSession = true;\n      try {\n        persistent?.setItem(KEEP_CONNECTED_KEY, '1');\n        transient?.removeItem(SESSION_ONLY_KEY);\n      } catch {}\n    } else {\n      migrateAuthTokens(persistent, transient);\n      rememberSession = false;\n      try {\n        persistent?.removeItem(KEEP_CONNECTED_KEY);\n        transient?.setItem(SESSION_ONLY_KEY, '1');\n      } catch {}\n    }\n    try { persistent?.removeItem(OAUTH_REMEMBER_KEY); } catch {}\n  }\n\n"""
if app_text.count(anchor) != 1:
    raise SystemExit(f'clearRememberPreference anchor count={app_text.count(anchor)}')
app_text = app_text.replace(anchor, insert, 1)

# Explicit logout/delete/reset also clear an unfinished OAuth bridge marker.
old = """      persistent?.removeItem(KEEP_CONNECTED_KEY);\n      transient?.removeItem(SESSION_ONLY_KEY);\n"""
new = """      persistent?.removeItem(KEEP_CONNECTED_KEY);\n      persistent?.removeItem(OAUTH_REMEMBER_KEY);\n      transient?.removeItem(SESSION_ONLY_KEY);\n"""
if old not in app_text:
    raise SystemExit('clear preference storage lines missing')
app_text = app_text.replace(old, new, 1)

# Google login: remember the requested mode, but keep OAuth's round-trip state persistent.
old = """  async function signInWithGoogle() {\n    const button = $('#google-auth-button');\n    if (!supabaseClient) return;\n    setRememberPreference(Boolean($('#keep-connected')?.checked));\n    setButtonLoading(button, true, 'Verificando Google...');\n"""
new = """  async function signInWithGoogle() {\n    const button = $('#google-auth-button');\n    if (!supabaseClient) return;\n    const shouldRemember = Boolean($('#keep-connected')?.checked);\n    prepareGoogleOAuthStorage(shouldRemember);\n    setButtonLoading(button, true, 'Verificando Google...');\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'signInWithGoogle anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

# Intent metadata must never be allowed to abort Google login in restrictive mobile browsers.
old = """      sessionStorage.setItem('salesboard_oauth_intent', JSON.stringify({ plan: requestedPlan, billing: billingCycle, createdAt: Date.now() }));\n"""
new = """      try { transientAuthStorage()?.setItem('salesboard_oauth_intent', JSON.stringify({ plan: requestedPlan, billing: billingCycle, createdAt: Date.now() })); } catch {}\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'oauth intent anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

# Restore the user's Keep Connected choice only after Supabase has rebuilt the OAuth session.
old = """    const { data, error } = await supabaseClient.auth.getSession();\n    if (error) console.error(error);\n    session = data?.session || null;\n\n    if (params.get('recovery') === '1') {\n"""
new = """    const { data, error } = await supabaseClient.auth.getSession();\n    if (error) console.error(error);\n    session = data?.session || null;\n    finalizeGoogleOAuthStorage();\n\n    if (params.get('recovery') === '1') {\n"""
if app_text.count(old) != 1:
    raise SystemExit(f'getSession initialization anchor count={app_text.count(old)}')
app_text = app_text.replace(old, new, 1)

app.write_text(app_text, encoding='utf-8')

# Mobile plan cards: recommendation badge gets its own row and never overlays the price.
marker = """\n/* Mobile trial-plan alignment — badge must never overlap price */\n@media(max-width:760px){\n  .trial-plan-card.featured .trial-recommended{position:static;display:table;margin:0 0 14px auto}\n  .trial-plan-card .trial-plan-top{align-items:flex-start;min-width:0}\n  .trial-plan-card .trial-plan-top strong{position:relative;z-index:1}\n}\n@media(max-width:420px){\n  .trial-plan-card{padding:20px}\n  .trial-plan-card .trial-plan-top{gap:12px}\n  .trial-plan-card .trial-plan-top strong{font-size:23px}\n  .trial-plan-card .trial-plan-name{font-size:19px}\n}\n"""
if '/* Mobile trial-plan alignment — badge must never overlap price */' not in css_text:
    css_text = css_text.rstrip() + marker
css.write_text(css_text, encoding='utf-8')

# Permanent static contract markers.
needle = """for (const marker of ['authSessionStorage', 'setRememberPreference', 'KEEP_CONNECTED_KEY', 'SESSION_ONLY_KEY']) {\n"""
replacement = """for (const marker of ['authSessionStorage', 'setRememberPreference', 'KEEP_CONNECTED_KEY', 'SESSION_ONLY_KEY', 'OAUTH_REMEMBER_KEY', 'prepareGoogleOAuthStorage', 'finalizeGoogleOAuthStorage', 'migrateAuthTokens']) {\n"""
if needle not in audit_text:
    raise SystemExit('UI audit auth markers anchor missing')
audit_text = audit_text.replace(needle, replacement, 1)
audit.write_text(audit_text, encoding='utf-8')

print('Applied mobile OAuth bridge and trial plan card alignment fix.')
