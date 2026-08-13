from pathlib import Path


def replace_once(path, old, new, label):
    text = path.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one match, found {count}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')

app = Path('salesboard/app/app.js')
html = Path('salesboard/app/index.html')
css = Path('salesboard/app/app.css')
audit = Path('salesboard/scripts/ui_contract_audit.mjs')
ci = Path('.github/workflows/salesboard-production-check.yml')

# 1) Toasts become explicit success/error/warning/info notifications.
replace_once(app, '''  function toast(title, message = '', type = 'success') {
    const stack = $('#toast-stack');
    if (!stack) return;
    const item = document.createElement('div');
    item.className = `toast ${type}`;
    item.innerHTML = `<span>${type === 'error' ? '!' : '✓'}</span><div><strong>${escapeHTML(title)}</strong>${message ? `<p>${escapeHTML(message)}</p>` : ''}</div><button aria-label="Fechar">×</button>`;
    item.querySelector('button').addEventListener('click', () => item.remove());
    stack.appendChild(item);
    setTimeout(() => item.remove(), 4800);
  }
''', '''  function toast(title, message = '', type = 'success') {
    const stack = $('#toast-stack');
    if (!stack) return;
    const normalizedType = ['success', 'error', 'warning', 'info'].includes(type) ? type : 'info';
    const icons = { success: '✓', error: '!', warning: '!', info: 'i' };
    const item = document.createElement('div');
    item.className = `toast ${normalizedType}`;
    item.setAttribute('role', ['error', 'warning'].includes(normalizedType) ? 'alert' : 'status');
    item.innerHTML = `<span>${icons[normalizedType]}</span><div><strong>${escapeHTML(title)}</strong>${message ? `<p>${escapeHTML(message)}</p>` : ''}</div><button type="button" aria-label="Fechar notificação">×</button>`;
    item.querySelector('button').addEventListener('click', () => item.remove());
    stack.appendChild(item);
    setTimeout(() => item.remove(), normalizedType === 'error' ? 6500 : 4800);
  }
''', 'toast system')

# 2) Confirmation component supports non-destructive primary actions too.
replace_once(app, '''    cancelLabel = 'Cancelar',
    requireText = '',
    details = []
  }) {''', '''    cancelLabel = 'Cancelar',
    requireText = '',
    details = [],
    tone = 'danger'
  }) {''', 'confirmation tone signature')
replace_once(app, '''      confirmButton.textContent = confirmLabel;
      cancelButton.textContent = cancelLabel;
''', '''      confirmButton.textContent = confirmLabel;
      cancelButton.textContent = cancelLabel;
      confirmButton.className = `button ${tone === 'primary' ? 'primary' : 'danger-solid'}`;
''', 'confirmation tone class')

# 3) Auth helpers: no browser-native validation, accessible resend action and explicit inline validation.
replace_once(app, '''  function setInlineMessage(selector, message, error = false) {
    const box = $(selector);
    if (!box) return;
    box.hidden = !message;
    box.textContent = message || '';
    box.classList.toggle('error', Boolean(error));
  }
''', '''  function setInlineMessage(selector, message, error = false) {
    const box = $(selector);
    if (!box) return;
    box.hidden = !message;
    box.textContent = message || '';
    box.classList.toggle('error', Boolean(error));
  }

  function isValidEmail(value) {
    return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(String(value || '').trim());
  }

  function focusField(selector) {
    const field = $(selector);
    if (!field) return;
    field.focus({ preventScroll: true });
    field.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function setResendConfirmation(email = '') {
    const button = $('#resend-confirmation');
    if (!button) return;
    const normalized = String(email || '').trim();
    button.dataset.email = normalized;
    button.hidden = !normalized;
  }
''', 'auth helpers')

replace_once(app, '''    if (message.includes('password should be')) return 'A senha não atende aos requisitos de segurança. Use pelo menos 8 caracteres.';
    return friendlyError(error);
''', '''    if (message.includes('password should be')) return 'A senha não atende aos requisitos de segurança. Use pelo menos 8 caracteres.';
    if (code.includes('otp_expired') || code.includes('token_expired') || message.includes('otp expired') || message.includes('token has expired') || message.includes('invalid token')) return 'Este link não é mais válido. Solicite um novo link e use apenas o e-mail mais recente.';
    return friendlyError(error);
''', 'auth expired link message')

# 4) Invalid/expired recovery URL gets a real recovery message instead of silently falling to login.
replace_once(app, '''    if (params.get('recovery') === '1' && session) {
      showOnly('recovery-screen');
      return;
    }

    if (!session) {
      showAuth(params.get('mode') === 'register' ? 'register' : 'login');
      return;
    }
''', '''    if (params.get('recovery') === '1') {
      if (session) {
        showOnly('recovery-screen');
      } else {
        $('#forgot-email').value = '';
        setInlineMessage('#forgot-status', 'Este link de recuperação é inválido ou expirou. Solicite um novo link para continuar.', true);
        showOnly('forgot-screen');
      }
      return;
    }

    if (!session) {
      showAuth(params.get('mode') === 'register' ? 'register' : 'login');
      return;
    }
''', 'expired recovery route')

# 5) Auth mode resets context-specific resend action.
replace_once(app, '''    $('#auth-register-pane').hidden = login;
    setAuthMessage('');
  }
''', '''    $('#auth-register-pane').hidden = login;
    setAuthMessage('');
    setResendConfirmation('');
  }
''', 'auth mode resend reset')

# 6) Starting the one-time trial is consequential and now uses the standard confirmation component.
replace_once(app, '''  async function startTrial(plan, button) {
    if (!['essential', 'pro'].includes(plan) || demoMode) return;
    const buttons = $$('[data-start-trial]');
''', '''  async function startTrial(plan, button) {
    if (!['essential', 'pro'].includes(plan) || demoMode) return;
    const planLabel = plan === 'essential' ? 'Essencial' : 'Pro';
    const confirmed = await requestConfirmation({
      title: `Começar 3 dias no ${planLabel}?`,
      message: 'Seu período de 72 horas começa imediatamente após esta confirmação.',
      confirmLabel: 'Começar agora',
      cancelLabel: 'Voltar',
      tone: 'primary',
      details: ['Não é necessário cadastrar cartão.', 'A experiência é única por conta/e-mail.', 'Depois de iniciada, ela não reinicia ao trocar de plano.']
    });
    if (!confirmed) return;
    const buttons = $$('[data-start-trial]');
''', 'trial confirmation')

# 7) Notifications: distinguish information/warnings from errors/success.
replacements = {
"toast('Modo demonstração', 'Os dados desta tela são fictícios e não são enviados para um servidor.');": "toast('Modo demonstração', 'Os dados desta tela são fictícios e não são enviados para um servidor.', 'info');",
"if (checkout === 'cancelled') toast('Checkout cancelado', 'Nenhuma cobrança foi concluída.', 'error');": "if (checkout === 'cancelled') toast('Checkout cancelado', 'Nenhuma cobrança foi concluída.', 'info');",
"toast('Recurso Pro', 'Metas financeiras fazem parte do plano Pro.', 'error');": "toast('Recurso Pro', 'Metas financeiras fazem parte do plano Pro.', 'warning');",
"toast('Demonstração', 'A cobrança real fica disponível somente no ambiente de produção.');": "toast('Demonstração', 'A cobrança real fica disponível somente no ambiente de produção.', 'info');",
"toast('Assinatura já existente', payload.error, 'error');": "toast('Assinatura já existente', payload.error, 'warning');",
"toast('Demonstração', 'O portal de cobrança é ativado no ambiente de produção.');": "toast('Demonstração', 'O portal de cobrança é ativado no ambiente de produção.', 'info');",
"toast('Demonstração atualizada');": "toast('Demonstração atualizada', '', 'info');",
"toast('Demonstração', 'A exclusão real só existe no ambiente de produção.');": "toast('Demonstração', 'A exclusão real só existe no ambiente de produção.', 'info');"
}
text = app.read_text(encoding='utf-8')
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)
app.write_text(text, encoding='utf-8')

# 8) Archived items are now a managed reversible state, not a dead end.
replace_once(app, '''    renderBilling();
    renderSelectOptions();
    renderFeatureLocks();
''', '''    renderBilling();
    renderArchivedItems();
    renderSelectOptions();
    renderFeatureLocks();
''', 'render archived list')

archive_functions = r'''

  function renderArchivedItems() {
    const container = $('#archived-items');
    if (!container) return;
    const archived = [
      ...allAccounts().filter((item) => item.archived).map((item) => ({ ...item, entityKind: 'account', entityLabel: 'Conta', detail: accountTypeLabel(item.type) })),
      ...allCategories().filter((item) => item.archived).map((item) => ({ ...item, entityKind: 'category', entityLabel: 'Categoria', detail: item.type === 'expense' ? 'Saída' : 'Entrada' }))
    ];
    $('#archived-count').textContent = String(archived.length);
    container.innerHTML = archived.length ? archived.map((item) => `<div class="archived-row"><span class="archived-icon" style="background:${escapeHTML(item.color || '#64748b')}18;color:${escapeHTML(item.color || '#64748b')}">${escapeHTML(item.icon || '•')}</span><div><strong>${escapeHTML(item.name)}</strong><small>${escapeHTML(item.entityLabel)} · ${escapeHTML(item.detail)}</small></div><button type="button" class="button subtle compact" data-reactivate-entity="${item.entityKind}" data-reactivate-id="${item.id}">Reativar</button></div>`).join('') : '<div class="archived-empty"><span>✓</span><div><strong>Nenhum item arquivado</strong><small>Contas e categorias arquivadas aparecerão aqui para você reativar quando precisar.</small></div></div>';
    $$('[data-reactivate-entity]').forEach((button) => button.addEventListener('click', () => reactivateEntity(button.dataset.reactivateEntity, button.dataset.reactivateId)));
  }

  async function reactivateEntity(mode, id) {
    const isAccount = mode === 'account';
    const catalog = isAccount ? allAccounts() : allCategories();
    const row = catalog.find((item) => item.id === id && item.archived);
    if (!row) {
      toast('Item indisponível', 'Atualize os dados e tente novamente.', 'warning');
      return;
    }
    const label = isAccount ? 'conta' : 'categoria';
    const confirmed = await requestConfirmation({
      title: `Reativar ${label}?`,
      message: `“${row.name}” voltará a ficar disponível para novos lançamentos.`,
      confirmLabel: 'Reativar',
      tone: 'primary',
      details: ['Todo o histórico anterior continua preservado.', isAccount ? 'No Essencial, o limite de até 3 contas ativas continua valendo.' : 'A categoria voltará às opções compatíveis com o tipo dela.']
    });
    if (!confirmed) return;
    try {
      if (demoMode) {
        row.archived = false;
        const active = isAccount ? state.accounts : state.categories;
        if (!active.some((item) => item.id === row.id)) active.push(row);
      } else {
        const table = isAccount ? 'accounts' : 'categories';
        const { error } = await supabaseClient.from(table).update({ archived: false }).eq('id', id).eq('user_id', state.user.id);
        if (error) throw error;
        await loadFinancialData();
      }
      renderAll();
      toast(`${isAccount ? 'Conta' : 'Categoria'} reativada`, `“${row.name}” já pode ser usada novamente.`);
    } catch (error) {
      toast('Não foi possível reativar', friendlyError(error), 'error');
    }
  }
'''
replace_once(app, '''  function exportCSV(monthFilter = null) {''', archive_functions + '''

  function exportCSV(monthFilter = null) {''', 'reactivation functions')

# 9) Disable native HTML constraint-validation UI for all auth forms and add explicit validation.
replace_once(app, '''  function initStaticEvents() {
    $('#google-auth-button')?.addEventListener('click', signInWithGoogle);
''', '''  function initStaticEvents() {
    ['#login-form', '#register-form', '#forgot-form', '#recovery-form'].forEach((selector) => {
      const form = $(selector);
      if (!form) return;
      form.noValidate = true;
      form.setAttribute('novalidate', 'novalidate');
    });
    $('#google-auth-button')?.addEventListener('click', signInWithGoogle);
''', 'disable native auth validation')

replace_once(app, '''      const button = event.currentTarget.querySelector('button[type="submit"]');
      setButtonLoading(button, true, 'Entrando...');
      setAuthMessage('');
      try {
        const { data, error } = await supabaseClient.auth.signInWithPassword({ email: $('#login-email').value.trim(), password: $('#login-password').value });
''', '''      const button = event.currentTarget.querySelector('button[type="submit"]');
      const email = $('#login-email').value.trim();
      const password = $('#login-password').value;
      setAuthMessage('');
      setResendConfirmation('');
      if (!isValidEmail(email)) { setAuthMessage('Informe um e-mail válido para entrar.', true); focusField('#login-email'); return; }
      if (!password) { setAuthMessage('Informe sua senha para entrar.', true); focusField('#login-password'); return; }
      setButtonLoading(button, true, 'Entrando...');
      try {
        const { data, error } = await supabaseClient.auth.signInWithPassword({ email, password });
''', 'login inline validation')

replace_once(app, '''      } catch (error) {
        setAuthMessage(authErrorMessage(error), true);
      } finally {
        setButtonLoading(button, false);
      }
    });
    $('#register-form').addEventListener('submit', async (event) => {
''', '''      } catch (error) {
        setAuthMessage(authErrorMessage(error), true);
        const rawAuthError = `${error?.code || ''} ${error?.message || ''}`.toLowerCase();
        if (rawAuthError.includes('email_not_confirmed') || rawAuthError.includes('email not confirmed')) setResendConfirmation(email);
      } finally {
        setButtonLoading(button, false);
      }
    });
    $('#register-form').addEventListener('submit', async (event) => {
''', 'login resend unconfirmed')

replace_once(app, '''      const button = event.currentTarget.querySelector('button[type="submit"]');
      if (!$('#accept-terms').checked) return;
      setButtonLoading(button, true, 'Criando conta...');
      setAuthMessage('');
      try {
        const email = $('#register-email').value.trim();
''', '''      const button = event.currentTarget.querySelector('button[type="submit"]');
      const name = $('#register-name').value.trim();
      const email = $('#register-email').value.trim();
      const password = $('#register-password').value;
      setAuthMessage('');
      setResendConfirmation('');
      if (!name) { setAuthMessage('Informe seu nome para criar a conta.', true); focusField('#register-name'); return; }
      if (!isValidEmail(email)) { setAuthMessage('Informe um e-mail válido para criar a conta.', true); focusField('#register-email'); return; }
      if (password.length < 8) { setAuthMessage('Crie uma senha com pelo menos 8 caracteres.', true); focusField('#register-password'); return; }
      if (!$('#accept-terms').checked) { setAuthMessage('Aceite os Termos de Uso e a Política de Privacidade para continuar.', true); focusField('#accept-terms'); return; }
      setButtonLoading(button, true, 'Criando conta...');
      try {
''', 'register inline validation')

replace_once(app, '''          password: $('#register-password').value,
''', '''          password,
''', 'register password variable')
replace_once(app, '''              full_name: $('#register-name').value.trim(),
''', '''              full_name: name,
''', 'register name variable')

replace_once(app, '''        } else {
          setAuthMessage(`Conta criada. Enviamos uma confirmação para ${email}. Confirme o e-mail e depois entre no SalesBoard.`);
          setAuthMode('login');
          $('#login-email').value = email;
        }
''', '''        } else {
          setAuthMode('login');
          $('#login-email').value = email;
          setAuthMessage(`Conta criada. Enviamos uma confirmação para ${email}. Confirme o e-mail e depois entre no SalesBoard.`);
          setResendConfirmation(email);
        }
''', 'signup confirmation message order')

replace_once(app, '''      const button = event.currentTarget.querySelector('button[type="submit"]');
      const email = $('#forgot-email').value.trim();
      setButtonLoading(button, true, 'Enviando...');
      setInlineMessage('#forgot-status', '');
      try {
''', '''      const button = event.currentTarget.querySelector('button[type="submit"]');
      const email = $('#forgot-email').value.trim();
      setInlineMessage('#forgot-status', '');
      if (!isValidEmail(email)) { setInlineMessage('#forgot-status', 'Informe um e-mail válido para recuperar o acesso.', true); focusField('#forgot-email'); return; }
      setButtonLoading(button, true, 'Enviando...');
      try {
''', 'forgot inline validation')

# 10) HTML: auth forms opt out of native validation and resend button is visible in either auth mode.
html_text = html.read_text(encoding='utf-8')
for form_id in ['login-form', 'register-form', 'forgot-form', 'recovery-form']:
    html_text = html_text.replace(f'<form id="{form_id}"', f'<form id="{form_id}" novalidate', 1)
old_resend = '<button type="button" class="button subtle wide auth-secondary-action" id="resend-confirmation" hidden>Reenviar e-mail de confirmação</button>'
if html_text.count(old_resend) != 1:
    raise SystemExit(f'resend HTML expected once, found {html_text.count(old_resend)}')
html_text = html_text.replace(old_resend, '', 1)
old_auth_message = '<div id="auth-message" class="auth-message" hidden></div>'
if html_text.count(old_auth_message) != 1:
    raise SystemExit('auth message anchor missing')
html_text = html_text.replace(old_auth_message, old_auth_message + '<button type="button" class="button subtle wide auth-secondary-action" id="resend-confirmation" hidden>Reenviar e-mail de confirmação</button>', 1)

# Settings gets an Archived Items manager.
settings_anchor = '<article class="panel"><div class="panel-head"><div><strong>Sessão</strong><small>Segurança da conta</small></div></div><div class="settings-actions"><button class="button dark" id="logout-button">Sair deste dispositivo</button></div></article>'
archived_panel = '<article class="panel archived-panel"><div class="panel-head"><div><strong>Itens arquivados</strong><small>Reative contas e categorias sem perder o histórico</small></div><span class="archived-count" id="archived-count">0</span></div><div id="archived-items" class="archived-items"></div></article>'
if html_text.count(settings_anchor) != 1:
    raise SystemExit('settings session anchor missing')
html_text = html_text.replace(settings_anchor, archived_panel + settings_anchor, 1)
html.write_text(html_text, encoding='utf-8')

# 11) Styling for notification tones and archive manager.
css_text = css.read_text(encoding='utf-8')
addition = '''\n/* Interaction consistency audit 2026-08 */\n.toast.info>span{background:#eef4ff;color:#3b67c4}.toast.warning>span{background:#fff6df;color:#a76c00}.toast.warning{border-color:#f3dfad}.toast.info{border-color:#dbe7f7}.auth-secondary-action:not([hidden]){margin-top:10px}.archived-panel{min-height:180px}.archived-count{min-width:28px;height:28px;padding:0 8px;border-radius:999px;background:#f2f5f7;color:#667085;display:grid;place-items:center;font-size:10px;font-weight:800}.archived-items{display:grid;gap:0}.archived-row{display:grid;grid-template-columns:36px minmax(0,1fr) auto;gap:11px;align-items:center;padding:12px 0;border-bottom:1px solid #eef1f4}.archived-row:last-child{border-bottom:0}.archived-icon{width:36px;height:36px;border-radius:10px;display:grid;place-items:center;font-size:15px}.archived-row strong{display:block;font-size:10px}.archived-row small{display:block;margin-top:4px;color:#8a96a6;font-size:8px}.archived-empty{display:grid;grid-template-columns:34px 1fr;gap:10px;align-items:center;padding:14px 0}.archived-empty>span{width:34px;height:34px;border-radius:10px;background:#eafff7;color:#0b8a63;display:grid;place-items:center}.archived-empty strong{display:block;font-size:10px}.archived-empty small{display:block;margin-top:4px;color:#8a96a6;font-size:8px;line-height:1.5}@media(max-width:430px){.archived-row{grid-template-columns:34px minmax(0,1fr)}.archived-row .button{grid-column:1/-1;width:100%}}\n'''
if '/* Interaction consistency audit 2026-08 */' not in css_text:
    css_text += addition
css.write_text(css_text, encoding='utf-8')

# 12) UI contract: static coverage for auth/native-dialog rules + runtime reactivation coverage.
audit_text = audit.read_text(encoding='utf-8')
audit_text = audit_text.replace("for (const file of ['salesboard/app/app.js', 'salesboard/app/runtime-bridge.js']) {", "for (const file of ['salesboard/app/app.js', 'salesboard/app/runtime-bridge.js', 'salesboard/app.js', 'salesboard/legal/legal.js']) {", 1)
audit_text = audit_text.replace("for (const marker of ['accountCatalog', 'categoryCatalog', 'allAccounts()', 'allCategories()', 'historicalAccount', 'historicalCategory']) {", "for (const marker of ['accountCatalog', 'categoryCatalog', 'allAccounts()', 'allCategories()', 'historicalAccount', 'historicalCategory', 'renderArchivedItems', 'reactivateEntity', 'setResendConfirmation', 'form.noValidate = true', 'Começar 3 dias no']) {", 1)
static_anchor = "const browser = await chromium.launch({ headless: true });"
static_insert = """const appHtml = fs.readFileSync('salesboard/app/index.html', 'utf8');\nfor (const id of ['login-form', 'register-form', 'forgot-form', 'recovery-form']) {\n  if (!new RegExp(`<form id=\\\"${id}\\\"[^>]*novalidate`).test(appHtml)) failures.push(`static: formulário ${id} ainda permite validação nativa`);\n}\nif (!appHtml.includes('id=\\\"archived-items\\\"')) failures.push('static: gerenciador de itens arquivados ausente');\nif (!appHtml.includes('id=\\\"resend-confirmation\\\"')) failures.push('static: ação de reenviar confirmação ausente');\n\n""" + static_anchor
if static_anchor not in audit_text:
    raise SystemExit('audit browser anchor missing')
audit_text = audit_text.replace(static_anchor, static_insert, 1)

runtime_anchor = """    await page.locator('#transaction-modal [data-close-modal]').first().evaluate((element) => element.click());\n\n    if (!(await openView(page, 'goals'))) throw new Error('view goals não encontrada');"""
runtime_insert = """    await page.locator('#transaction-modal [data-close-modal]').first().evaluate((element) => element.click());\n\n    // Arquivamento é reversível pela própria interface e usa o mesmo modal padrão.\n    if (!(await openView(page, 'settings'))) throw new Error('view settings não encontrada');\n    const archivedPanelText = await page.locator('#archived-items').innerText();\n    if (!archivedPanelText.includes('Conta principal') || !archivedPanelText.includes('Moradia')) fail(viewport, 'itens arquivados não aparecem no gerenciador');\n    const reactivateAccount = page.locator('[data-reactivate-entity=\\\"account\\\"][data-reactivate-id=\\\"a1\\\"]');\n    if (!(await reactivateAccount.count())) fail(viewport, 'ação de reativar conta ausente');\n    else {\n      await reactivateAccount.click();\n      await page.waitForSelector('#confirm-modal:not([hidden])');\n      if (!(await page.locator('#confirm-title').textContent()).includes('Reativar conta')) fail(viewport, 'reativação de conta não usa confirmação padrão');\n      if (!(await page.locator('#confirm-action').getAttribute('class') || '').includes('primary')) fail(viewport, 'reativação usa tom visual destrutivo');\n      await page.locator('#confirm-action').click();\n    }\n    const reactivateCategory = page.locator('[data-reactivate-entity=\\\"category\\\"][data-reactivate-id=\\\"c3\\\"]');\n    if (!(await reactivateCategory.count())) fail(viewport, 'ação de reativar categoria ausente');\n    else {\n      await reactivateCategory.click();\n      await page.waitForSelector('#confirm-modal:not([hidden])');\n      if (!(await page.locator('#confirm-title').textContent()).includes('Reativar categoria')) fail(viewport, 'reativação de categoria não usa confirmação padrão');\n      await page.locator('#confirm-action').click();\n    }\n    await page.waitForTimeout(120);\n    await page.locator('#quick-add').evaluate((element) => element.click());\n    await page.locator('input[name=\\\"transaction_type\\\"][value=\\\"expense\\\"]').check();\n    await page.waitForTimeout(80);\n    const restoredOptions = await page.evaluate(() => ({ account: [...document.querySelector('#tx-account').options].some((option) => option.value === 'a1'), category: [...document.querySelector('#tx-category').options].some((option) => option.value === 'c3') }));\n    if (!restoredOptions.account || !restoredOptions.category) fail(viewport, 'item reativado não voltou às opções de novo lançamento');\n    await page.locator('#transaction-modal [data-close-modal]').first().evaluate((element) => element.click());\n\n    if (!(await openView(page, 'goals'))) throw new Error('view goals não encontrada');"""
if runtime_anchor not in audit_text:
    raise SystemExit('audit runtime anchor missing')
audit_text = audit_text.replace(runtime_anchor, runtime_insert, 1)
audit_text = audit_text.replace("console.log('PASS UI contract: alignment + billing/sidebar + confirmations + archive history + historical editing');", "console.log('PASS UI contract: alignment + billing/sidebar + confirmations + auth validation + archive/reactivate + historical editing');", 1)
audit.write_text(audit_text, encoding='utf-8')

# 13) Production CI scans every user-facing JS and permanently requires the repaired flows.
ci_text = ci.read_text(encoding='utf-8')
old_native = "if grep -Pq '\\b(confirm|prompt|alert)\\s*\\(' salesboard/app/app.js salesboard/app/runtime-bridge.js; then echo 'Native browser dialogs are forbidden in SalesBoard'; exit 1; fi"
new_native = "if grep -Pq '\\b(confirm|prompt|alert)\\s*\\(' salesboard/app/app.js salesboard/app/runtime-bridge.js salesboard/app.js salesboard/legal/legal.js; then echo 'Native browser dialogs are forbidden in SalesBoard'; exit 1; fi"
if old_native not in ci_text:
    raise SystemExit('CI native-dialog rule anchor missing')
ci_text = ci_text.replace(old_native, new_native, 1)
ci_anchor = "          grep -Fq 'requestConfirmation' salesboard/app/app.js\n"
ci_extra = ci_anchor + "          grep -Fq 'reactivateEntity' salesboard/app/app.js\n          grep -Fq 'renderArchivedItems' salesboard/app/app.js\n          grep -Fq 'setResendConfirmation' salesboard/app/app.js\n          grep -Fq 'form.noValidate = true' salesboard/app/app.js\n          grep -Fq 'Começar 3 dias no' salesboard/app/app.js\n          grep -Fq 'id=\"archived-items\"' salesboard/app/index.html\n          grep -Fq 'id=\"resend-confirmation\"' salesboard/app/index.html\n          for form in login-form register-form forgot-form recovery-form; do grep -Pq \"<form id=\\\"$form\\\"[^>]*novalidate\" salesboard/app/index.html || { echo \"$form must disable native browser validation\"; exit 1; }; done\n          if grep -Pq '\\breportValidity\\s*\\(' salesboard/app/app.js salesboard/app/runtime-bridge.js; then echo 'Native browser validation UI is forbidden in SalesBoard'; exit 1; fi\n"
if ci_anchor not in ci_text:
    raise SystemExit('CI requestConfirmation anchor missing')
ci_text = ci_text.replace(ci_anchor, ci_extra, 1)
ci.write_text(ci_text, encoding='utf-8')

print('Full interaction audit repair patched successfully.')
