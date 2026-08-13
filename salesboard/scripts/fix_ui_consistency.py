from pathlib import Path
import re

root = Path('salesboard')
app_path = root / 'app' / 'app.js'
index_path = root / 'app' / 'index.html'
quality_path = root / 'app' / 'quality.css'
runtime_path = root / 'app' / 'runtime-bridge.js'

app = app_path.read_text(encoding='utf-8')
index = index_path.read_text(encoding='utf-8')
quality = quality_path.read_text(encoding='utf-8')
runtime = runtime_path.read_text(encoding='utf-8')

# 1) Reusable in-app confirmation dialog. No browser-native confirm/prompt.
marker = "  function setAuthMessage(message, error = false) {"
if 'function requestConfirmation(' not in app:
    helper = r'''  let confirmationState = null;

  function closeConfirmation(result = false) {
    const modal = $('#confirm-modal');
    if (modal) modal.hidden = true;
    document.body.classList.remove('modal-open');
    const stateToResolve = confirmationState;
    confirmationState = null;
    if (stateToResolve?.resolve) stateToResolve.resolve(Boolean(result));
  }

  function requestConfirmation({
    title,
    message,
    confirmLabel = 'Excluir',
    cancelLabel = 'Cancelar',
    requireText = '',
    details = []
  }) {
    return new Promise((resolve) => {
      if (confirmationState?.resolve) closeConfirmation(false);
      confirmationState = { resolve };

      const modal = $('#confirm-modal');
      const titleNode = $('#confirm-title');
      const messageNode = $('#confirm-message');
      const detailsNode = $('#confirm-details');
      const textWrap = $('#confirm-text-wrap');
      const textHint = $('#confirm-text-hint');
      const textInput = $('#confirm-text-input');
      const confirmButton = $('#confirm-action');
      const cancelButton = $('#confirm-cancel');
      const closeButton = $('#confirm-close');

      titleNode.textContent = title || 'Confirmar ação';
      messageNode.textContent = message || 'Revise esta ação antes de continuar.';
      confirmButton.textContent = confirmLabel;
      cancelButton.textContent = cancelLabel;

      const safeDetails = Array.isArray(details) ? details.filter(Boolean) : [];
      detailsNode.hidden = safeDetails.length === 0;
      detailsNode.innerHTML = safeDetails.map((item) => `<li>${escapeHTML(item)}</li>`).join('');

      textWrap.hidden = !requireText;
      textHint.textContent = requireText;
      textInput.value = '';
      textInput.disabled = !requireText;
      confirmButton.disabled = Boolean(requireText);

      const syncConfirmState = () => {
        if (!requireText) return;
        textInput.value = textInput.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, requireText.length);
        confirmButton.disabled = textInput.value !== requireText;
      };

      textInput.oninput = syncConfirmState;
      confirmButton.onclick = () => {
        if (requireText && textInput.value !== requireText) return;
        closeConfirmation(true);
      };
      cancelButton.onclick = () => closeConfirmation(false);
      closeButton.onclick = () => closeConfirmation(false);
      modal.onclick = (event) => { if (event.target === modal) closeConfirmation(false); };

      openModal('confirm-modal');
      setTimeout(() => (requireText ? textInput : confirmButton).focus(), 40);
    });
  }

'''
    if marker not in app:
        raise SystemExit('Could not find setAuthMessage marker')
    app = app.replace(marker, helper + marker, 1)

old = """  async function deleteTransaction(id) {
    if (!confirm('Excluir este lançamento? Esta ação não pode ser desfeita.')) return;
    try {"""
new = """  async function deleteTransaction(id) {
    const row = state.transactions.find((item) => item.id === id);
    const confirmed = await requestConfirmation({
      title: 'Excluir lançamento?',
      message: row ? `“${row.description}” será removido do histórico e dos cálculos financeiros.` : 'Este lançamento será removido do histórico e dos cálculos financeiros.',
      confirmLabel: 'Excluir lançamento',
      details: row?.goal_id ? ['O valor destinado à meta também deixará de contar no progresso.'] : []
    });
    if (!confirmed) return;
    try {"""
if old not in app:
    raise SystemExit('deleteTransaction native confirm block not found')
app = app.replace(old, new, 1)

old_entity = r'''  async function deleteEntity(mode, id) {
    const label = mode === 'account' ? 'conta' : mode === 'category' ? 'categoria' : 'meta';
    if (!confirm(`Excluir esta ${label}?`)) return;
    try {
      if (demoMode) {
        const key = mode === 'account' ? 'accounts' : mode === 'category' ? 'categories' : 'goals';
        state[key] = state[key].filter((row) => row.id !== id);
      } else {
        const table = mode === 'account' ? 'accounts' : mode === 'category' ? 'categories' : 'goals';
        const { error } = await supabaseClient.from(table).delete().eq('id', id).eq('user_id', state.user.id);
        if (error) throw error;
        await loadFinancialData();
      }
      renderAll();
      toast(`${label[0].toUpperCase()}${label.slice(1)} excluída`);
    } catch (error) {
      toast('Não foi possível excluir', friendlyError(error), 'error');
    }
  }
'''
new_entity = r'''  async function deleteEntity(mode, id) {
    const config = {
      account: { label: 'conta', table: 'accounts', key: 'accounts' },
      category: { label: 'categoria', table: 'categories', key: 'categories' },
      goal: { label: 'meta', table: 'goals', key: 'goals' }
    }[mode];
    if (!config) return;

    const row = state[config.key].find((item) => item.id === id);
    const usedByHistory = mode === 'account'
      ? state.transactions.some((transaction) => transaction.account_id === id)
      : mode === 'category'
        ? state.transactions.some((transaction) => transaction.category_id === id)
        : state.transactions.some((transaction) => transaction.goal_id === id);
    const shouldArchive = usedByHistory && (mode === 'account' || mode === 'category');
    const displayName = row?.name ? `“${row.name}”` : `esta ${config.label}`;

    const confirmed = await requestConfirmation({
      title: shouldArchive ? `Arquivar ${config.label}?` : `Excluir ${config.label}?`,
      message: shouldArchive
        ? `${displayName} já possui lançamentos. Para preservar seu histórico financeiro, ela será arquivada em vez de apagada.`
        : `${displayName} será removida permanentemente.`,
      confirmLabel: shouldArchive ? 'Arquivar' : `Excluir ${config.label}`,
      details: shouldArchive ? ['Os lançamentos antigos continuam nos relatórios e saldos históricos.', 'O item deixa de aparecer nas opções para novos lançamentos.'] : []
    });
    if (!confirmed) return;

    try {
      if (demoMode) {
        state[config.key] = state[config.key].filter((item) => item.id !== id);
        if (mode === 'goal') state.transactions.forEach((transaction) => {
          if (transaction.goal_id === id) {
            transaction.goal_id = null;
            transaction.goal_amount = null;
          }
        });
      } else if (shouldArchive) {
        const { error } = await supabaseClient.from(config.table).update({ archived: true }).eq('id', id).eq('user_id', state.user.id);
        if (error) throw error;
        await loadFinancialData();
      } else {
        const { error } = await supabaseClient.from(config.table).delete().eq('id', id).eq('user_id', state.user.id);
        if (error) throw error;
        await loadFinancialData();
      }
      renderAll();
      toast(shouldArchive ? `${config.label[0].toUpperCase()}${config.label.slice(1)} arquivada` : `${config.label[0].toUpperCase()}${config.label.slice(1)} excluída`);
    } catch (error) {
      toast(shouldArchive ? 'Não foi possível arquivar' : 'Não foi possível excluir', friendlyError(error), 'error');
    }
  }
'''
if old_entity not in app:
    raise SystemExit('deleteEntity block not found')
app = app.replace(old_entity, new_entity, 1)

old_account = r'''    if (!confirm('Esta ação excluirá sua conta, dados financeiros e encerrará uma assinatura ativa. Deseja continuar?')) return;
    const confirmation = prompt('Digite EXCLUIR para confirmar a exclusão permanente:');
    if (confirmation !== 'EXCLUIR') return;
    try {'''
new_account = r'''    const confirmed = await requestConfirmation({
      title: 'Excluir conta permanentemente?',
      message: 'Essa ação encerra seu espaço no SalesBoard e não pode ser desfeita.',
      confirmLabel: 'Excluir permanentemente',
      cancelLabel: 'Manter minha conta',
      requireText: 'EXCLUIR',
      details: [
        'Contas, categorias, lançamentos, metas e configurações serão apagados.',
        'Se houver assinatura ativa, ela será cancelada antes da exclusão.',
        'Um período de experiência já utilizado não será liberado novamente para o mesmo e-mail.'
      ]
    });
    if (!confirmed) return;
    const confirmation = 'EXCLUIR';
    try {'''
if old_account not in app:
    raise SystemExit('deleteAccount native dialog block not found')
app = app.replace(old_account, new_account, 1)

# Escape must resolve a pending confirmation promise instead of only hiding it.
old_escape = "      if (event.key === 'Escape') { closeModals(); closeSidebar(); }"
new_escape = "      if (event.key === 'Escape') { if (confirmationState) closeConfirmation(false); else closeModals(); closeSidebar(); }"
if old_escape not in app:
    raise SystemExit('Escape handler not found')
app = app.replace(old_escape, new_escape, 1)

# Search copy must include goals because search already supports them.
app = app.replace('Procure lançamentos, contas ou categorias.</p>', 'Procure lançamentos, contas, categorias ou metas.</p>', 1)

# 2) Transaction modal gets an explicit grid class so alignment rules are scoped.
old_grid = '<div class="form-grid"><label class="full">Descrição<input id="tx-description"'
new_grid = '<div class="form-grid transaction-grid"><label class="full">Descrição<input id="tx-description"'
if old_grid not in index:
    raise SystemExit('Transaction form grid marker not found')
index = index.replace(old_grid, new_grid, 1)

# 3) Add reusable confirmation modal before scripts.
if 'id="confirm-modal"' not in index:
    confirm_html = r'''

  <div class="modal" id="confirm-modal" hidden>
    <div class="modal-card small confirm-card" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
      <header>
        <div><span class="kicker">Confirmação</span><h2 id="confirm-title">Confirmar ação</h2></div>
        <button class="icon-button" id="confirm-close" type="button" aria-label="Fechar">×</button>
      </header>
      <form id="confirm-form" novalidate onsubmit="return false">
        <div class="confirm-content">
          <span class="confirm-icon" aria-hidden="true">!</span>
          <div class="confirm-copy"><p id="confirm-message"></p><ul id="confirm-details" hidden></ul></div>
        </div>
        <label class="confirm-text-wrap" id="confirm-text-wrap" hidden>Para confirmar, digite <strong id="confirm-text-hint">EXCLUIR</strong>
          <input id="confirm-text-input" autocomplete="off" spellcheck="false" />
        </label>
        <footer><button type="button" class="button subtle" id="confirm-cancel">Cancelar</button><button type="button" class="button danger-solid" id="confirm-action">Excluir</button></footer>
      </form>
    </div>
  </div>
'''
    script_marker = '  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2" defer></script>'
    if script_marker not in index:
        raise SystemExit('Script marker not found in index')
    index = index.replace(script_marker, confirm_html + '\n' + script_marker, 1)

# 4) Remove obsolete runtime account-delete overlay interception. The app owns all confirmations now.
pattern = re.compile(r"\n\(\(\) => \{\n  'use strict';\n\n  const \{ projectUrl, publishableKey \} = window\.SALESBOARD_RUNTIME;.*?\n\}\)\(\);\n?", re.S)
runtime, count = pattern.subn('\n', runtime, count=1)
if count != 1:
    raise SystemExit(f'Expected to remove one obsolete delete-account runtime IIFE, removed {count}')

# 5) Final visual/alignment hardening. quality.css is loaded last.
css_block = r'''

/* SB_UI_CONSISTENCY_V3 — strict alignment + one confirmation language */
.transaction-grid>label{align-self:start;align-content:start;min-width:0}
.transaction-grid>label>input,.transaction-grid>label>select,.transaction-grid>label>.money-field{width:100%}
.transaction-grid .field-help{margin-top:0;min-height:30px}
.transaction-grid .check{align-self:start!important;min-height:44px;align-items:center!important;margin:0!important;padding:0 4px!important}
.transaction-grid .check input{margin:0!important}
.transaction-grid #tx-goal-wrap,.transaction-grid #tx-goal-amount-wrap{align-self:start}
.transaction-grid #tx-status{height:44px}
.transaction-grid #tx-goal,.transaction-grid #tx-category,.transaction-grid #tx-account,.transaction-grid #tx-recurrence{height:44px}

.confirm-card form{padding-top:22px}
.confirm-content{display:grid;grid-template-columns:48px minmax(0,1fr);gap:16px;align-items:start}
.confirm-icon{width:48px;height:48px;border-radius:15px;background:#fff1f2;color:#cf3443;display:grid;place-items:center;font:900 21px var(--display)}
.confirm-copy{min-width:0}.confirm-copy p{margin:2px 0 0;color:#5f6c7d;font-size:13px;line-height:1.6}
.confirm-copy ul{list-style:none;margin:16px 0 0;padding:14px 16px;border:1px solid #e5eaf0;border-radius:14px;background:#f8fafc;display:grid;gap:9px}
.confirm-copy li{position:relative;padding-left:14px;color:#49576a;font-size:11px;line-height:1.5}.confirm-copy li:before{content:'•';position:absolute;left:0;color:#cf3443;font-weight:900}
.confirm-text-wrap{display:grid;gap:8px;margin-top:20px;color:#344054;font-size:11px;font-weight:700}.confirm-text-wrap strong{color:#182230}
.confirm-text-wrap input{width:100%;min-height:44px;border:1px solid #d7dee7;border-radius:12px;padding:11px 13px;outline:none;text-transform:uppercase;font-weight:750;letter-spacing:.04em}
.confirm-text-wrap input:focus{border-color:#e65b67;box-shadow:0 0 0 4px rgba(230,91,103,.10)}
.button.danger-solid{background:#d94b58;color:#fff;border:1px solid #d94b58;box-shadow:0 8px 22px rgba(217,75,88,.16)}.button.danger-solid:hover{background:#c83f4d}.button.danger-solid:disabled{background:#cbd3dc;border-color:#cbd3dc;color:#6f7b89;box-shadow:none;cursor:not-allowed;transform:none}

.current-plan>div:last-child{align-self:center}.current-plan>div:last-child small,.current-plan>div:last-child strong{display:block;line-height:1.1}
.trial-card{display:grid;gap:0}.trial-card>span,.trial-card strong,.trial-card p,.trial-card button{justify-self:start}.trial-card button{margin-top:2px}

@media(max-width:680px){
  .transaction-grid{grid-template-columns:1fr!important}
  .transaction-grid .full{grid-column:1!important}
  .transaction-grid .field-help{min-height:0}
  .confirm-content{grid-template-columns:42px minmax(0,1fr);gap:13px}.confirm-icon{width:42px;height:42px;border-radius:13px}
}
'''
if 'SB_UI_CONSISTENCY_V3' not in quality:
    quality += css_block

# Safety assertions: no browser-native dialog APIs remain in production app JS/runtime.
for name, text in [('app.js', app), ('runtime-bridge.js', runtime)]:
    if re.search(r'\b(?:confirm|prompt|alert)\s*\(', text):
        raise SystemExit(f'Native browser dialog still present in {name}')

if 'transaction-grid' not in index or 'confirm-modal' not in index:
    raise SystemExit('Required UI markers missing after patch')

app_path.write_text(app, encoding='utf-8')
index_path.write_text(index, encoding='utf-8')
quality_path.write_text(quality, encoding='utf-8')
runtime_path.write_text(runtime, encoding='utf-8')
print('SalesBoard UI consistency patch applied successfully.')
