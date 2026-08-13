from pathlib import Path

app = Path('salesboard/app/app.js')
html = Path('salesboard/app/index.html')
audit = Path('salesboard/scripts/ui_contract_audit.mjs')
text = app.read_text(encoding='utf-8')

# Every actual SalesBoard form must opt out of browser-native validation UI.
old = """    ['#login-form', '#register-form', '#forgot-form', '#recovery-form'].forEach((selector) => {
"""
new = """    ['#login-form', '#register-form', '#forgot-form', '#recovery-form', '#onboarding-form', '#profile-form', '#transaction-form', '#entity-form', '#confirm-form'].forEach((selector) => {
"""
if text.count(old) != 1:
    raise SystemExit(f'form list anchor count={text.count(old)}')
text = text.replace(old, new, 1)

# Transaction validation must be complete and SalesBoard-owned.
old = """      if (!payload.description || payload.amount <= 0) throw new Error('Preencha descrição e valor corretamente.');
      if (!payload.category_id) throw new Error('Crie ou selecione uma categoria compatível com este lançamento.');
"""
new = """      if (!payload.description) throw new Error('Informe uma descrição para o lançamento.');
      if (payload.amount <= 0) throw new Error('Informe um valor maior que zero.');
      if (!payload.transaction_date) throw new Error('Informe a data do lançamento.');
      if (!payload.category_id) throw new Error('Crie ou selecione uma categoria compatível com este lançamento.');
      if (!payload.account_id) throw new Error('Crie ou selecione uma conta para este lançamento.');
"""
if text.count(old) != 1:
    raise SystemExit(f'transaction validation anchor count={text.count(old)}')
text = text.replace(old, new, 1)

# Entity form: validate name explicitly, never through required/native bubble.
old = """    const form = new FormData(event.currentTarget);
    const button = $('#entity-form button[type=\"submit\"]');
    setButtonLoading(button, true, 'Salvando...');
    try {
"""
new = """    const form = new FormData(event.currentTarget);
    const button = $('#entity-form button[type=\"submit\"]');
    setButtonLoading(button, true, 'Salvando...');
    try {
      const entityName = String(form.get('name') || '').trim();
      if (!entityName) throw new Error('Informe um nome antes de salvar.');
"""
if text.count(old) != 1:
    raise SystemExit(f'entity validation anchor count={text.count(old)}')
text = text.replace(old, new, 1)
text = text.replace("name: form.get('name').trim()", "name: entityName")
if "form.get('name').trim()" in text:
    raise SystemExit('raw entity name validation still remains')

# Onboarding: hidden required fields must never summon browser UI at the final submit.
old = """      const workspaceType = $('input[name=\"workspace_type\"]:checked').value;
      const workspaceName = $('#workspace-name-input').value.trim() || 'Meu espaço';
      const { error } = await supabaseClient.rpc('complete_salesboard_onboarding', {
"""
new = """      const workspaceType = $('input[name=\"workspace_type\"]:checked').value;
      const workspaceName = $('#workspace-name-input').value.trim();
      const accountName = $('#first-account-name').value.trim();
      if (!workspaceName) {
        onboardingStep = 1;
        updateOnboardingStep();
        toast('Nome do espaço necessário', 'Informe como você quer chamar seu espaço antes de continuar.', 'warning');
        focusField('#workspace-name-input');
        return;
      }
      if (!accountName) {
        onboardingStep = 2;
        updateOnboardingStep();
        toast('Nome da conta necessário', 'Informe um nome para sua primeira conta antes de continuar.', 'warning');
        focusField('#first-account-name');
        return;
      }
      const { error } = await supabaseClient.rpc('complete_salesboard_onboarding', {
"""
if text.count(old) != 1:
    raise SystemExit(f'onboarding validation anchor count={text.count(old)}')
text = text.replace(old, new, 1)
text = text.replace("p_account_name: $('#first-account-name').value.trim() || 'Conta principal'", "p_account_name: accountName", 1)
app.write_text(text, encoding='utf-8')

# Apply novalidate at markup level to every form, so behavior is correct before JS finishes booting.
html_text = html.read_text(encoding='utf-8')
form_ids = ['login-form','register-form','forgot-form','recovery-form','onboarding-form','profile-form','transaction-form','entity-form','confirm-form']
for form_id in form_ids:
    marker = f'<form id="{form_id}"'
    pos = html_text.find(marker)
    if pos < 0:
        raise SystemExit(f'missing form {form_id}')
    tag_end = html_text.find('>', pos)
    tag = html_text[pos:tag_end+1]
    if 'novalidate' not in tag:
        html_text = html_text[:pos] + tag.replace(marker, marker + ' novalidate', 1) + html_text[tag_end+1:]
html.write_text(html_text, encoding='utf-8')

# Static contract now enumerates all forms, not only auth forms.
audit_text = audit.read_text(encoding='utf-8')
old = """for (const id of ['login-form', 'register-form', 'forgot-form', 'recovery-form']) {
  if (!new RegExp(`<form id=\\\"${id}\\\"[^>]*novalidate`).test(appHtml)) failures.push(`static: formulário ${id} ainda permite validação nativa`);
}
"""
new = """for (const id of ['login-form', 'register-form', 'forgot-form', 'recovery-form', 'onboarding-form', 'profile-form', 'transaction-form', 'entity-form', 'confirm-form']) {
  if (!new RegExp(`<form id=\\\"${id}\\\"[^>]*novalidate`).test(appHtml)) failures.push(`static: formulário ${id} ainda permite validação nativa`);
}
"""
if audit_text.count(old) != 1:
    raise SystemExit(f'audit all-forms anchor count={audit_text.count(old)}')
audit.write_text(audit_text.replace(old, new, 1), encoding='utf-8')
print('All SalesBoard forms now use product-owned validation.')
