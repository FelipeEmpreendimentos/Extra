from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
js_path = ROOT / 'app' / 'app.js'
html_path = ROOT / 'app' / 'index.html'
css_path = ROOT / 'app' / 'quality.css'

js = js_path.read_text(encoding='utf-8')
html = html_path.read_text(encoding='utf-8')
css = css_path.read_text(encoding='utf-8')


def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {count}')
    return text.replace(old, new, 1)


def sub_once(text, pattern, replacement, label):
    updated, count = re.subn(pattern, lambda _m: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 match, found {count}')
    return updated

# Transaction modal: goal allocation is visible only when a goal is selected on an income.
html = once(
    html,
    '<label id="tx-goal-wrap">Meta (opcional)<select id="tx-goal"><option value="">Nenhuma meta</option></select><small class="field-help">Quando o lançamento estiver realizado, o valor entra no progresso da meta.</small></label><label>Status<select id="tx-status">',
    '<label id="tx-goal-wrap">Meta (opcional)<select id="tx-goal"><option value="">Nenhuma meta</option></select><small class="field-help">Escolha uma meta para destinar parte ou todo o valor desta entrada.</small></label><label id="tx-goal-amount-wrap" hidden>Valor destinado à meta<div class="money-field"><span>R$</span><input id="tx-goal-amount" inputmode="decimal" placeholder="Valor inteiro da entrada" /></div><small class="field-help">Se ficar vazio, o valor inteiro da entrada será considerado na meta.</small></label><label>Status<select id="tx-status">',
    'goal amount field',
)
html = once(
    html,
    'placeholder="Buscar lançamentos, contas ou categorias..."',
    'placeholder="Buscar lançamentos, contas, categorias ou metas..."',
    'global search placeholder',
)

# Goal progress is the real baseline + allocated values; never hide overfunding.
js = once(
    js,
    "const linked = paidTransactions().filter((row) => row.type === 'income' && row.goal_id === goal?.id).reduce((sum, row) => sum + Number(row.amount), 0);\n    return Math.min(Number(goal?.target_amount || 0), base + linked);",
    "const linked = paidTransactions().filter((row) => row.type === 'income' && row.goal_id === goal?.id).reduce((sum, row) => sum + Number(row.goal_amount || row.amount), 0);\n    return base + linked;",
    'goal allocated progress',
)
js = once(
    js,
    "const linkedCount = paidTransactions().filter((row) => row.goal_id === goal.id).length;",
    "const linkedCount = paidTransactions().filter((row) => row.type === 'income' && row.goal_id === goal.id).length;",
    'goal linked count',
)
js = once(
    js,
    "const details = [row.recurring ? 'Recorrente' : '', goal ? `Meta: ${goal.icon} ${goal.name}` : ''].filter(Boolean).join(' · ');",
    "const details = [row.recurring ? 'Recorrente' : '', goal ? `Meta: ${goal.icon} ${goal.name} (${brl.format(Number(row.goal_amount || row.amount))})` : ''].filter(Boolean).join(' · ');",
    'transaction allocation detail',
)

# Remove the misleading quick "Aportar" path. Goal progress comes from real income records.
js = js.replace('<footer><small>Faltam ${brl.format(Math.max(0, target - current))}${linkedCount ? ` · ${linkedCount} ${linkedCount === 1 ? \'lançamento vinculado\' : \'lançamentos vinculados\'}` : \'\'}</small><button data-contribute-goal="${goal.id}">+ Aportar</button></footer>', '<footer><small>Faltam ${brl.format(Math.max(0, target - current))}${linkedCount ? ` · ${linkedCount} ${linkedCount === 1 ? \'entrada vinculada\' : \'entradas vinculadas\'}` : \'\'}</small><span class="goal-source-note">Vincule entradas em Novo lançamento</span></footer>')
js = once(
    js,
    "    $$('[data-contribute-goal]').forEach((button) => button.addEventListener('click', () => contributeGoal(button.dataset.contributeGoal)));\n",
    '',
    'remove goal contribute listener',
)
js = sub_once(js, r"  async function contributeGoal\(id\) \{.*?\n  \}\n\n  function exportCSV", "  function exportCSV", 'remove synthetic goal contribution function')

# Goal allocation visibility and normalization.
marker = "  function renderSelectOptions(type = null) {\n"
sync_function = '''  function syncGoalAllocationField() {
    const wrap = $('#tx-goal-amount-wrap');
    const input = $('#tx-goal-amount');
    const selectedType = $('input[name="transaction_type"]:checked')?.value || 'expense';
    const visible = hasPro() && selectedType === 'income' && Boolean($('#tx-goal')?.value);
    if (wrap) wrap.hidden = !visible;
    if (!visible && input) input.value = '';
  }

'''
js = once(js, marker, sync_function + marker, 'goal allocation helper')
js = once(
    js,
    "      if (!canLinkGoal) goalSelect.value = '';\n    }\n  }",
    "      if (!canLinkGoal) goalSelect.value = '';\n    }\n    syncGoalAllocationField();\n  }",
    'sync allocation after selects',
)
js = once(
    js,
    "    if ($('#tx-goal-wrap')) $('#tx-goal-wrap').hidden = !hasPro();",
    "    syncGoalAllocationField();",
    'feature lock allocation sync',
)
js = once(
    js,
    "    $('#tx-goal').value = row?.goal_id || transactionGoalPreset || '';\n    transactionGoalPreset = null;",
    "    $('#tx-goal').value = row?.goal_id || transactionGoalPreset || '';\n    $('#tx-goal-amount').value = row?.goal_amount ? Number(row.goal_amount).toFixed(2).replace('.', ',') : '';\n    syncGoalAllocationField();\n    transactionGoalPreset = null;",
    'load transaction allocation',
)

old_save_head = '''      const type = $('input[name="transaction_type"]:checked').value;
      const payload = {
        user_id: state.user.id,
        type,
        description: $('#tx-description').value.trim(),
        amount: parseMoney($('#tx-amount').value),
        transaction_date: $('#tx-date').value,
        category_id: $('#tx-category').value,
        account_id: $('#tx-account').value,
        goal_id: hasPro() && type === 'income' ? ($('#tx-goal').value || null) : null,
        status: $('#tx-status').value,
'''
new_save_head = '''      const type = $('input[name="transaction_type"]:checked').value;
      const amount = parseMoney($('#tx-amount').value);
      const goalId = hasPro() && type === 'income' ? ($('#tx-goal').value || null) : null;
      const allocationInput = $('#tx-goal-amount').value.trim();
      const goalAmount = goalId ? (allocationInput ? parseMoney(allocationInput) : amount) : null;
      const payload = {
        user_id: state.user.id,
        type,
        description: $('#tx-description').value.trim(),
        amount,
        transaction_date: $('#tx-date').value,
        category_id: $('#tx-category').value,
        account_id: $('#tx-account').value,
        goal_id: goalId,
        goal_amount: goalAmount,
        status: $('#tx-status').value,
'''
js = once(js, old_save_head, new_save_head, 'save goal allocation')
js = once(
    js,
    "      if (!payload.description || payload.amount <= 0) throw new Error('Preencha descrição e valor corretamente.');\n      if (payload.recurring && !hasPro())",
    "      if (!payload.description || payload.amount <= 0) throw new Error('Preencha descrição e valor corretamente.');\n      if (!payload.category_id) throw new Error('Crie ou selecione uma categoria compatível com este lançamento.');\n      if (payload.goal_amount != null && (payload.goal_amount <= 0 || payload.goal_amount > payload.amount)) throw new Error('INVALID_GOAL_AMOUNT');\n      if (payload.recurring && !hasPro())",
    'validate goal allocation',
)
js = once(
    js,
    "if (message.includes('GOAL_REQUIRES_INCOME')) return 'Metas podem ser vinculadas apenas a entradas. Para dinheiro que você já tinha guardado, use o valor já acumulado da meta.';",
    "if (message.includes('INVALID_GOAL_AMOUNT')) return 'O valor destinado à meta precisa ser maior que zero e não pode ultrapassar o valor da entrada.';\n    if (message.includes('GOAL_REQUIRES_INCOME')) return 'Metas podem ser vinculadas apenas a entradas. Para dinheiro que você já tinha guardado, use o valor já acumulado da meta.';",
    'goal allocation error',
)
js = once(
    js,
    "    $('#report-month').addEventListener('change', (event) => { reportMonthKey = event.target.value || currentMonthKey(); renderReports(); });",
    "    $('#report-month').addEventListener('change', (event) => { reportMonthKey = event.target.value || currentMonthKey(); renderReports(); });\n    $('#tx-goal').addEventListener('change', syncGoalAllocationField);",
    'goal allocation listener',
)

# CSV keeps the relationship transparent.
js = once(
    js,
    "const rows = [['Descrição', 'Tipo', 'Categoria', 'Conta', 'Meta', 'Data', 'Status', 'Recorrente', 'Valor'], ...source.map((row) => [row.description, row.type === 'income' ? 'Entrada' : 'Saída', categoryById(row.category_id).name, accountById(row.account_id).name, goalById(row.goal_id)?.name || '', row.transaction_date, row.status === 'paid' ? 'Pago' : 'Pendente', row.recurring ? 'Sim' : 'Não', Number(row.amount).toFixed(2).replace('.', ',')])];",
    "const rows = [['Descrição', 'Tipo', 'Categoria', 'Conta', 'Meta', 'Valor na meta', 'Data', 'Status', 'Recorrente', 'Valor'], ...source.map((row) => [row.description, row.type === 'income' ? 'Entrada' : 'Saída', categoryById(row.category_id).name, accountById(row.account_id).name, goalById(row.goal_id)?.name || '', row.goal_id ? Number(row.goal_amount || row.amount).toFixed(2).replace('.', ',') : '', row.transaction_date, row.status === 'paid' ? 'Pago' : 'Pendente', row.recurring ? 'Sim' : 'Não', Number(row.amount).toFixed(2).replace('.', ',')])];",
    'csv goal allocation',
)

# Budget overrun: report real percentages and negative room instead of hiding the excess.
js = once(
    js,
    "$('#budget-summary').innerHTML = `<article><span>Limite planejado</span><strong>${brl.format(budgetTotal)}</strong></article><article><span>Gasto até agora</span><strong>${brl.format(spentTotal)}</strong></article><article><span>Disponível</span><strong>${brl.format(Math.max(0, budgetTotal - spentTotal))}</strong></article>`;",
    "const budgetRoom = budgetTotal - spentTotal;\n    $('#budget-summary').innerHTML = `<article><span>Limite planejado</span><strong>${brl.format(budgetTotal)}</strong></article><article><span>Gasto até agora</span><strong>${brl.format(spentTotal)}</strong></article><article><span>${budgetRoom >= 0 ? 'Disponível' : 'Acima do limite'}</span><strong class=\"${budgetRoom < 0 ? 'value-expense' : ''}\">${brl.format(Math.abs(budgetRoom))}</strong></article>`;",
    'budget summary overrun',
)
js = once(
    js,
    "      const percent = Math.min(100, spent / budget * 100);\n      const cls = percent >= 95 ? 'danger' : percent >= 75 ? 'warning' : '';\n      return `<article class=\"entity-card budget-card\"><div class=\"entity-head\"><div class=\"entity-title\"><span class=\"entity-icon\">${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>Limite mensal</small></div></div><button class=\"entity-menu\" data-edit-category=\"${category.id}\">✎</button></div><div class=\"budget-values\"><strong>${brl.format(spent)}</strong><span>de ${brl.format(budget)}</span></div><div class=\"progress\"><i class=\"${cls}\" style=\"width:${percent}%\"></i></div><small>${Math.round(percent)}% utilizado · ${brl.format(Math.max(0, budget - spent))} restante</small></article>`;",
    "      const percent = spent / budget * 100;\n      const barPercent = Math.min(100, percent);\n      const cls = percent >= 95 ? 'danger' : percent >= 75 ? 'warning' : '';\n      const room = budget - spent;\n      return `<article class=\"entity-card budget-card\"><div class=\"entity-head\"><div class=\"entity-title\"><span class=\"entity-icon\">${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>Limite mensal</small></div></div><button class=\"entity-menu\" data-edit-category=\"${category.id}\">✎</button></div><div class=\"budget-values\"><strong>${brl.format(spent)}</strong><span>de ${brl.format(budget)}</span></div><div class=\"progress\"><i class=\"${cls}\" style=\"width:${barPercent}%\"></i></div><small>${Math.round(percent)}% utilizado · ${room >= 0 ? `${brl.format(room)} restante` : `${brl.format(Math.abs(room))} acima do limite`}</small></article>`;",
    'budget card overrun',
)
js = once(
    js,
    "return `<div class=\"rank-row\"><span>${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>${percent.toFixed(1).replace('.', ',')}% do limite · ${brl.format(Math.max(0, category.limit - category.spent))} disponível</small></div><b class=\"${percent > 100 ? 'value-expense' : ''}\">${brl.format(category.spent)}</b></div>`;",
    "const room = category.limit - category.spent;\n      return `<div class=\"rank-row\"><span>${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>${percent.toFixed(1).replace('.', ',')}% do limite · ${room >= 0 ? `${brl.format(room)} disponível` : `${brl.format(Math.abs(room))} acima`}</small></div><b class=\"${percent > 100 ? 'value-expense' : ''}\">${brl.format(category.spent)}</b></div>`;",
    'report budget overrun',
)

# Billing: no dead portal button and no duplicate subscription checkout for active users.
old_current_plan = "    $('#current-plan').innerHTML = `<div><span>${escapeHTML(statusText.toUpperCase())}</span><h2>${escapeHTML(headline)}</h2><p>${state.subscription?.cancel_at_period_end ? 'Cancelamento agendado para o fim do período.' : state.profile?.subscription_status === 'trialing' ? `Seu acesso atual segue exatamente as permissões do ${activePlan}.` : 'Você pode gerenciar cobrança e cancelamento no portal seguro.'}</p></div><div><small>Plano atual</small><strong>${escapeHTML(currentLabel)}</strong></div>`;"
new_current_plan = "    const subscriptionStatus = state.profile?.subscription_status || 'none';\n    const planMessage = state.subscription?.cancel_at_period_end\n      ? 'Cancelamento agendado para o fim do período.'\n      : subscriptionStatus === 'trialing'\n        ? `Seu acesso atual segue exatamente as permissões do ${activePlan}.`\n        : subscriptionStatus === 'active'\n          ? 'Use o portal de cobrança para alterar plano, pagamento ou renovação.'\n          : subscriptionStatus === 'past_due'\n            ? 'Atualize o pagamento pelo portal de cobrança para regularizar o acesso.'\n            : subscriptionStatus === 'canceled'\n              ? 'A assinatura anterior foi encerrada. Você pode escolher um novo plano abaixo.'\n              : 'Escolha um plano abaixo quando quiser continuar após o período de experiência.';\n    $('#current-plan').innerHTML = `<div><span>${escapeHTML(statusText.toUpperCase())}</span><h2>${escapeHTML(headline)}</h2><p>${escapeHTML(planMessage)}</p></div><div><small>Plano atual</small><strong>${escapeHTML(currentLabel)}</strong></div>`;\n    const portalAvailable = Boolean(state.subscription?.stripe_subscription_id);\n    $('#billing-portal').hidden = !portalAvailable;\n    const mustUsePortal = ['active', 'past_due'].includes(subscriptionStatus);\n    $$('[data-subscribe]').forEach((button) => {\n      if (!button.dataset.defaultLabel) button.dataset.defaultLabel = button.textContent;\n      button.textContent = mustUsePortal ? 'Alterar no portal' : button.dataset.defaultLabel;\n    });"
js = once(js, old_current_plan, new_current_plan, 'billing portal semantics')
js = once(
    js,
    "$$('[data-subscribe]').forEach((button) => button.addEventListener('click', () => subscribe(button.dataset.subscribe)));",
    "$$('[data-subscribe]').forEach((button) => button.addEventListener('click', () => ['active', 'past_due'].includes(state.profile?.subscription_status) ? openBillingPortal() : subscribe(button.dataset.subscribe)));",
    'billing plan action',
)

css += '''\n\n.goal-source-note{font-size:11px;color:#7d8998;text-align:right;line-height:1.3}\n#tx-goal-amount-wrap[hidden]{display:none!important}\n'''

js_path.write_text(js, encoding='utf-8')
html_path.write_text(html, encoding='utf-8')
css_path.write_text(css, encoding='utf-8')
print('Final semantic review applied.')
