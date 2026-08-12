from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'app' / 'app.js'
text = path.read_text(encoding='utf-8')


def once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {count}')
    text = text.replace(old, new, 1)


once(
    "const linked = paidTransactions().filter((row) => row.goal_id === goal?.id).reduce((sum, row) => sum + Number(row.amount), 0);",
    "const linked = paidTransactions().filter((row) => row.type === 'income' && row.goal_id === goal?.id).reduce((sum, row) => sum + Number(row.amount), 0);",
    'goal progress income only',
)

once(
    "const type = row?.type || 'expense';",
    "const type = row?.type || (transactionGoalPreset ? 'income' : 'expense');",
    'goal preset transaction type',
)

once(
    "goal_id: hasPro() ? ($('#tx-goal').value || null) : null,",
    "goal_id: hasPro() && type === 'income' ? ($('#tx-goal').value || null) : null,",
    'goal payload semantics',
)

old_select = '''  function renderSelectOptions(type = null) {
    const transactionType = type || $('input[name="transaction_type"]:checked')?.value || 'expense';
    $('#tx-category').innerHTML = state.categories.filter((category) => category.type === transactionType).map((category) => `<option value="${category.id}">${escapeHTML(category.icon)} ${escapeHTML(category.name)}</option>`).join('');
    $('#tx-account').innerHTML = state.accounts.map((account) => `<option value="${account.id}">${escapeHTML(account.icon)} ${escapeHTML(account.name)}</option>`).join('');
    const goalSelect = $('#tx-goal');
    if (goalSelect) goalSelect.innerHTML = `<option value="">Nenhuma meta</option>${state.goals.map((goal) => `<option value="${goal.id}">${escapeHTML(goal.icon)} ${escapeHTML(goal.name)}</option>`).join('')}`;
  }
'''
new_select = '''  function renderSelectOptions(type = null) {
    const transactionType = type || $('input[name="transaction_type"]:checked')?.value || 'expense';
    $('#tx-category').innerHTML = state.categories.filter((category) => category.type === transactionType).map((category) => `<option value="${category.id}">${escapeHTML(category.icon)} ${escapeHTML(category.name)}</option>`).join('');
    $('#tx-account').innerHTML = state.accounts.map((account) => `<option value="${account.id}">${escapeHTML(account.icon)} ${escapeHTML(account.name)}</option>`).join('');
    const goalSelect = $('#tx-goal');
    const goalWrap = $('#tx-goal-wrap');
    const canLinkGoal = hasPro() && transactionType === 'income';
    if (goalWrap) goalWrap.hidden = !canLinkGoal;
    if (goalSelect) {
      goalSelect.innerHTML = `<option value="">Nenhuma meta</option>${state.goals.map((goal) => `<option value="${goal.id}">${escapeHTML(goal.icon)} ${escapeHTML(goal.name)}</option>`).join('')}`;
      if (!canLinkGoal) goalSelect.value = '';
    }
  }
'''
once(old_select, new_select, 'goal select visibility')

once(
    "categoryTypeSelect.value = row?.type || categoryType;\n      const budgetLabel",
    "categoryTypeSelect.value = row?.type || categoryType;\n      const categoryIsUsed = Boolean(row && state.transactions.some((transaction) => transaction.category_id === row.id));\n      if (categoryIsUsed) {\n        categoryTypeSelect.disabled = true;\n        categoryTypeSelect.title = 'O tipo não pode mudar porque esta categoria já possui lançamentos.';\n      }\n      const budgetLabel",
    'lock used category type',
)

old_contribute = '''  async function contributeGoal(id) {
    const goal = state.goals.find((item) => item.id === id);
    if (!goal) return;
    transactionGoalPreset = id;
    openTransactionModal();
    if ($('#transaction-modal').hidden) {
      transactionGoalPreset = null;
      return;
    }
    $('#tx-description').value = `Aporte: ${goal.name}`;
    $('#tx-goal').value = id;
    setTimeout(() => $('#tx-amount')?.focus(), 50);
    toast('Meta vinculada ao lançamento', 'Preencha o valor, a conta e a categoria. O progresso será atualizado quando o lançamento estiver realizado.');
  }
'''
new_contribute = '''  async function contributeGoal(id) {
    const goal = state.goals.find((item) => item.id === id);
    if (!goal) return;
    transactionGoalPreset = id;
    openTransactionModal();
    if ($('#transaction-modal').hidden) {
      transactionGoalPreset = null;
      return;
    }
    const incomeRadio = $('input[name="transaction_type"][value="income"]');
    if (incomeRadio) incomeRadio.checked = true;
    renderSelectOptions('income');
    $('#tx-description').value = `Entrada para ${goal.name}`;
    $('#tx-goal').value = id;
    setTimeout(() => $('#tx-amount')?.focus(), 50);
    toast('Meta vinculada à entrada', 'O progresso aumenta quando esta entrada estiver marcada como recebida. Dinheiro que você já tinha guardado deve entrar em “Valor já acumulado” da meta.');
  }
'''
once(old_contribute, new_contribute, 'goal contribute flow')

once(
    "if (message.includes('INVALID_GOAL_REFERENCE')) return 'A meta vinculada não existe mais ou não pertence a esta conta.';",
    "if (message.includes('GOAL_REQUIRES_INCOME')) return 'Metas podem ser vinculadas apenas a entradas. Para dinheiro que você já tinha guardado, use o valor já acumulado da meta.';\n    if (message.includes('INVALID_GOAL_REFERENCE')) return 'A meta vinculada não existe mais ou não pertence a esta conta.';",
    'goal friendly error',
)

once("$('#export-csv').addEventListener('click', exportCSV);", "$('#export-csv').addEventListener('click', () => exportCSV());", 'main export event')
once("$('#settings-export').addEventListener('click', exportCSV);", "$('#settings-export').addEventListener('click', () => exportCSV());", 'settings export event')
once("$('#paywall-export').addEventListener('click', exportCSV);", "$('#paywall-export').addEventListener('click', () => exportCSV());", 'paywall export event')

once(
    "state.categories.filter((row) => row.name.toLowerCase().includes(query)).slice(0, 4).forEach((row) => results.push({ icon: row.icon, title: row.name, subtitle: 'Categoria', view: 'categories' }));",
    "state.categories.filter((row) => row.name.toLowerCase().includes(query)).slice(0, 4).forEach((row) => results.push({ icon: row.icon, title: row.name, subtitle: 'Categoria', view: 'categories' }));\n      if (hasPro()) state.goals.filter((row) => row.name.toLowerCase().includes(query)).slice(0, 4).forEach((row) => results.push({ icon: row.icon, title: row.name, subtitle: 'Meta', view: 'goals' }));",
    'global goal search',
)

path.write_text(text, encoding='utf-8')
print('Final SalesBoard coherence fixes applied.')
