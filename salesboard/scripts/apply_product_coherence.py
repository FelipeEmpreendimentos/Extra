from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

def read(path):
    return (ROOT / path).read_text(encoding='utf-8')

def write(path, text):
    (ROOT / path).write_text(text, encoding='utf-8')

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {count}')
    return text.replace(old, new, 1)

def sub_once(text, pattern, replacement, label):
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 regex match, found {count}')
    return updated

# ---------- app/index.html ----------
path = 'salesboard/app/index.html'
html = read(path)
html = replace_once(
    html,
    '<div class="onboarding-step active" data-step="1"><span class="kicker">Seu espaço</span><h1>Como você vai usar o SalesBoard?</h1><p>Isso só ajusta a linguagem inicial. Você pode mudar depois.</p>',
    '<div class="onboarding-step active" data-step="1"><span class="kicker">Seu espaço</span><h1>Como você vai usar o SalesBoard?</h1><p>Sua escolha define apenas a estrutura inicial de categorias. Depois, tudo pode ser personalizado.</p>',
    'onboarding purpose copy'
)
html = replace_once(
    html,
    '<div class="seed-preview"><span>🏠 Moradia</span><span>🛒 Alimentação</span><span>🚗 Transporte</span><span>💡 Serviços</span><span>❤️ Saúde</span><span>🎮 Lazer</span><span>💼 Trabalho</span><span>💰 Outras entradas</span></div><label class="check"><input id="create-default-budgets" type="checkbox" checked /> Criar limites iniciais sugeridos (você poderá alterar)</label>',
    '<div class="seed-preview" id="seed-preview"><span>🏠 Moradia</span><span>🛒 Alimentação</span><span>🚗 Transporte</span><span>❤️ Saúde</span><span>🎮 Lazer</span><span>💡 Serviços</span><span>💼 Salário</span><span>💰 Renda extra</span></div><small class="onboarding-helper">Os limites mensais começam zerados. Você define seus próprios orçamentos depois.</small>',
    'onboarding seed preview'
)
html = replace_once(
    html,
    '<section class="view" data-page="reports"><div class="page-head"><div><span class="kicker">Análise</span><h1>Relatórios</h1><p>Entenda o que aconteceu, o que mudou e onde sua atenção financeira gera mais resultado.</p></div><button class="button subtle" id="reports-export">Exportar CSV</button></div>',
    '<section class="view" data-page="reports"><div class="page-head"><div><span class="kicker">Análise</span><h1>Relatórios</h1><p>Entenda o que aconteceu, o que mudou e onde sua atenção financeira gera mais resultado.</p></div><div class="page-actions report-actions"><label class="report-month-filter"><span>Mês</span><input id="report-month" type="month" aria-label="Mês do relatório" /></label><button class="button subtle" id="reports-export">Exportar CSV</button></div></div>',
    'report month filter'
)
html = html.replace('Categorias do mês atual', 'Categorias do mês selecionado')
html = replace_once(
    html,
    '<article class="panel"><div class="panel-head"><div><strong>Distribuição por conta</strong><small>Saldo consolidado</small></div></div><div id="report-accounts" class="rank-list compact"></div></article>',
    '<article class="panel"><div class="panel-head"><div><strong>Resultado por conta</strong><small>Movimentação do mês selecionado</small></div></div><div id="report-accounts" class="rank-list compact"></div></article>',
    'report accounts semantics'
)
html = replace_once(html, 'Anual · 2 meses grátis', 'Anual', 'billing annual label')
html = replace_once(
    html,
    '<form id="profile-form" class="form-grid"><label>Nome<input id="settings-name" maxlength="80" /></label><label>Nome do espaço<input id="settings-workspace" maxlength="80" /></label><label>Tipo de uso<select id="settings-type"><option value="personal">Pessoal</option><option value="freelancer">Autônomo</option><option value="business">Negócio</option></select></label><label>Moeda<select id="settings-currency"><option value="BRL">Real brasileiro (BRL)</option></select></label><button class="button primary" type="submit">Salvar alterações</button></form>',
    '<form id="profile-form" class="form-grid"><label>Nome<input id="settings-name" maxlength="80" /></label><label>Nome do espaço<input id="settings-workspace" maxlength="80" /></label><div class="setting-note full"><span>Moeda</span><strong>Real brasileiro (BRL)</strong><small>O SalesBoard trabalha em BRL nesta versão.</small></div><button class="button primary" type="submit">Salvar alterações</button></form>',
    'settings meaningful options'
)
html = replace_once(
    html,
    '<label>Conta<select id="tx-account" required></select></label><label>Status<select id="tx-status"><option value="paid">Pago/recebido</option><option value="pending">Pendente</option></select></label>',
    '<label>Conta<select id="tx-account" required></select></label><label id="tx-goal-wrap">Meta (opcional)<select id="tx-goal"><option value="">Nenhuma meta</option></select><small class="field-help">Quando o lançamento estiver realizado, o valor entra no progresso da meta.</small></label><label>Status<select id="tx-status"><option value="paid">Pago/recebido</option><option value="pending">Pendente</option></select></label>',
    'transaction goal field'
)
write(path, html)

# ---------- landing index.html ----------
path = 'salesboard/index.html'
landing = read(path)
landing = replace_once(landing, 'Anual <span>2 meses grátis</span>', 'Anual', 'landing annual label')
landing = replace_once(
    landing,
    'Crie categorias de entrada e saída, escolha ícones e defina limites mensais para aquilo que realmente importa.',
    'Crie categorias de entrada e saída, escolha ícones e defina limites mensais nas categorias de despesas que realmente importam.',
    'landing category limits copy'
)
landing = replace_once(
    landing,
    'No plano anual, a cobrança é feita uma vez por ano. O valor mensal exibido é apenas a equivalência do preço anual.',
    'No anual, o acesso é de 12 meses por R$ 149 no Essencial ou R$ 249 no Pro. O valor mensal exibido é apenas a equivalência; a forma de pagamento disponível será mostrada no checkout.',
    'annual payment promise'
)
landing = replace_once(
    landing,
    'Sim. Você pode criar categorias de entrada e saída, personalizar nome e ícone e definir limites mensais.',
    'Sim. Você pode criar categorias de entrada e saída, personalizar nome e ícone e definir limites mensais nas categorias de despesas.',
    'faq category budget copy'
)
landing = replace_once(
    landing,
    'Sim. Não há fidelidade. A gestão da assinatura é feita pelo portal de cobrança e o acesso pago segue o estado informado pelo Stripe.',
    'Sim. Você pode cancelar a renovação quando quiser. O acesso pago segue até o fim do período já contratado, e a gestão é feita pelo portal de cobrança.',
    'faq cancellation copy'
)
landing = landing.replace('3 dias grátis sem cartão. Depois, escolha mensal ou anual. Sem fidelidade.', '3 dias grátis sem cartão. Depois, escolha mensal ou anual.')
landing = landing.replace('3 dias grátis · sem cartão · sem fidelidade', '3 dias grátis · sem cartão')
write(path, landing)

# ---------- app/app.js ----------
path = 'salesboard/app/app.js'
js = read(path)
js = replace_once(js, "  let categoryType = 'expense';\n", "  let categoryType = 'expense';\n  let reportMonthKey = currentMonthKey();\n  let transactionGoalPreset = null;\n", 'state variables')

js = replace_once(
    js,
    "  function accountById(id) {\n    return state.accounts.find((item) => item.id === id) || { name: 'Conta removida', icon: '▣' };\n  }\n",
    "  function accountById(id) {\n    return state.accounts.find((item) => item.id === id) || { name: 'Conta removida', icon: '▣' };\n  }\n\n  function goalById(id) {\n    return state.goals.find((item) => item.id === id) || null;\n  }\n\n  function goalProgress(goal) {\n    const base = Math.max(0, Number(goal?.current_amount || 0));\n    const linked = paidTransactions().filter((row) => row.goal_id === goal?.id).reduce((sum, row) => sum + Number(row.amount), 0);\n    return Math.min(Number(goal?.target_amount || 0), base + linked);\n  }\n",
    'goal helpers'
)

js = sub_once(
    js,
    r"  function monthSeries\(count = 6\) \{.*?\n  \}\n\n  function friendlyError",
    "  function monthSeries(count = 6, endKey = currentMonthKey()) {\n    const [anchorYear, anchorMonth] = String(endKey).split('-').map(Number);\n    const anchor = new Date(anchorYear, anchorMonth - 1, 1);\n    const output = [];\n    for (let index = count - 1; index >= 0; index -= 1) {\n      const date = new Date(anchor.getFullYear(), anchor.getMonth() - index, 1);\n      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;\n      const total = totalsForMonth(key);\n      output.push({ key, label: new Intl.DateTimeFormat('pt-BR', { month: 'short' }).format(date).replace('.', ''), ...total });\n    }\n    return output;\n  }\n\n  function friendlyError",
    'month series anchor'
)
js = js.replace("    if (message.includes('foreign key')) return 'Este item está sendo usado em lançamentos e não pode ser excluído agora.';", "    if (message.includes('INVALID_GOAL_REFERENCE')) return 'A meta vinculada não existe mais ou não pertence a esta conta.';\n    if (message.includes('CATEGORY_TYPE_MISMATCH')) return 'A categoria escolhida não combina com o tipo do lançamento.';\n    if (message.includes('foreign key')) return 'Este item está sendo usado em lançamentos e não pode ser excluído agora.';")

new_render_transactions = r'''  function renderTransactions() {
    const query = ($('#transaction-search')?.value || '').trim().toLowerCase();
    let rows = [...state.transactions];
    if (transactionFilter !== 'all') rows = rows.filter((row) => row.type === transactionFilter);
    if (query) rows = rows.filter((row) => `${row.description} ${categoryById(row.category_id).name} ${accountById(row.account_id).name} ${goalById(row.goal_id)?.name || ''}`.toLowerCase().includes(query));
    $('#transactions-empty').hidden = rows.length > 0;
    $('#transactions-body').innerHTML = rows.map((row) => {
      const category = categoryById(row.category_id);
      const account = accountById(row.account_id);
      const goal = row.goal_id ? goalById(row.goal_id) : null;
      const details = [row.recurring ? 'Recorrente' : '', goal ? `Meta: ${goal.icon} ${goal.name}` : ''].filter(Boolean).join(' · ');
      return `<tr><td><strong>${escapeHTML(row.description)}</strong>${details ? `<br><small>${escapeHTML(details)}</small>` : ''}</td><td><span class="category-pill">${escapeHTML(category.icon)} ${escapeHTML(category.name)}</span></td><td>${escapeHTML(account.name)}</td><td>${dateBR.format(new Date(`${row.transaction_date}T12:00:00`))}</td><td><span class="status-pill ${row.status === 'pending' ? 'pending' : ''}">${row.status === 'pending' ? 'Pendente' : 'Pago'}</span></td><td class="right ${row.type === 'income' ? 'value-income' : 'value-expense'}"><strong>${row.type === 'income' ? '+' : '−'} ${brl.format(Number(row.amount))}</strong></td><td><div class="table-actions"><button class="row-button" data-edit-transaction="${row.id}" title="Editar">✎</button><button class="row-button" data-delete-transaction="${row.id}" title="Excluir">×</button></div></td></tr>`;
    }).join('');
    $$('[data-edit-transaction]').forEach((button) => button.addEventListener('click', () => openTransactionModal(button.dataset.editTransaction)));
    $$('[data-delete-transaction]').forEach((button) => button.addEventListener('click', () => deleteTransaction(button.dataset.deleteTransaction)));
  }
'''
js = sub_once(js, r"  function renderTransactions\(\) \{.*?\n  \}\n\n  function renderAccounts", new_render_transactions + "\n  function renderAccounts", 'render transactions')

new_render_goals = r'''  function renderGoals() {
    if (!hasPro()) {
      $('#goals-grid').innerHTML = '<div class="locked-banner">Metas financeiras fazem parte do plano Pro.<button data-view="billing">Ver plano Pro →</button></div>';
      $('#goals-grid [data-view="billing"]').addEventListener('click', () => switchView('billing'));
      return;
    }
    $('#goals-grid').innerHTML = state.goals.length ? state.goals.map((goal) => {
      const target = Number(goal.target_amount);
      const current = goalProgress(goal);
      const percent = target ? Math.min(100, current / target * 100) : 0;
      const linkedCount = paidTransactions().filter((row) => row.goal_id === goal.id).length;
      return `<article class="entity-card goal-card"><div class="goal-top"><span class="goal-icon">${escapeHTML(goal.icon)}</span><div><button class="entity-menu" data-edit-goal="${goal.id}">✎</button><button class="entity-menu" data-delete-goal-row="${goal.id}">×</button></div></div><h3>${escapeHTML(goal.name)}</h3><p>${goal.due_date ? `Prazo: ${dateBR.format(new Date(`${goal.due_date}T12:00:00`))}` : 'Sem prazo definido'}</p><div class="goal-values"><strong>${brl.format(current)}</strong><span>${Math.round(percent)}%</span></div><div class="progress"><i style="width:${percent}%;background:#4f7de8"></i></div><footer><small>Faltam ${brl.format(Math.max(0, target - current))}${linkedCount ? ` · ${linkedCount} ${linkedCount === 1 ? 'lançamento vinculado' : 'lançamentos vinculados'}` : ''}</small><button data-contribute-goal="${goal.id}">+ Aportar</button></footer></article>`;
    }).join('') : emptyState('◎', 'Nenhuma meta ainda', 'Crie uma meta e vincule lançamentos para acompanhar o progresso.');
    $$('[data-edit-goal]').forEach((button) => button.addEventListener('click', () => openEntityModal('goal', button.dataset.editGoal)));
    $$('[data-delete-goal-row]').forEach((button) => button.addEventListener('click', () => deleteEntity('goal', button.dataset.deleteGoalRow)));
    $$('[data-contribute-goal]').forEach((button) => button.addEventListener('click', () => contributeGoal(button.dataset.contributeGoal)));
  }
'''
js = sub_once(js, r"  function renderGoals\(\) \{.*?\n  \}\n\n  function renderReports", new_render_goals + "\n  function renderReports", 'render goals')

new_render_reports = r'''  function renderReports() {
    const selectedKey = reportMonthKey || currentMonthKey();
    const [selectedYear, selectedMonth] = selectedKey.split('-').map(Number);
    const selectedDate = new Date(selectedYear, selectedMonth - 1, 1);
    const selectedLabel = new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' }).format(selectedDate);
    const input = $('#report-month');
    if (input) {
      input.value = selectedKey;
      input.max = currentMonthKey();
    }

    const totals = totalsForMonth(selectedKey);
    const previousDate = new Date(selectedYear, selectedMonth - 2, 1);
    const previousKey = `${previousDate.getFullYear()}-${String(previousDate.getMonth() + 1).padStart(2, '0')}`;
    const previous = totalsForMonth(previousKey);
    const change = (current, before) => before ? ((current - before) / Math.abs(before)) * 100 : (current ? null : 0);
    const deltaText = (current, before) => {
      const delta = change(current, before);
      if (delta === null) return 'sem base no mês anterior';
      return `${delta >= 0 ? '+' : ''}${delta.toFixed(1).replace('.', ',')}% vs. mês anterior`;
    };

    $('#report-summary').innerHTML = [
      ['Receitas', brl.format(totals.income), deltaText(totals.income, previous.income), 'good'],
      ['Despesas', brl.format(totals.expense), deltaText(totals.expense, previous.expense), totals.expense <= previous.expense ? 'good' : 'bad'],
      ['Resultado', brl.format(totals.net), deltaText(totals.net, previous.net), totals.net >= 0 ? 'good' : 'bad'],
      ['Taxa de economia', `${totals.savingsRate.toFixed(1).replace('.', ',')}%`, `${(totals.savingsRate - previous.savingsRate) >= 0 ? '+' : ''}${(totals.savingsRate - previous.savingsRate).toFixed(1).replace('.', ',')} p.p. vs. mês anterior`, totals.savingsRate >= 0 ? 'good' : 'bad']
    ].map(([label, value, detail, cls]) => `<article class="summary-card"><span>${label}</span><strong>${value}</strong><small class="${cls}">${escapeHTML(detail)}</small></article>`).join('');

    const expenses = state.categories.filter((category) => category.type === 'expense').map((category) => ({ ...category, total: categorySpent(category.id, selectedKey) })).filter((category) => category.total > 0).sort((a, b) => b.total - a.total);
    $('#report-categories').innerHTML = expenses.slice(0, 7).map((category) => `<div class="rank-row"><span>${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>${totals.expense ? (category.total / totals.expense * 100).toFixed(1).replace('.', ',') : 0}% das despesas</small></div><b>${brl.format(category.total)}</b></div>`).join('') || emptyState('⌁', 'Sem despesas', `Não há saídas realizadas em ${selectedLabel}.`);

    $('#report-pro-lock').hidden = hasPro();
    $('#report-pro-details').hidden = !hasPro();
    $('#report-pro-lock [data-view="billing"]')?.addEventListener('click', () => switchView('billing'));
    renderReportChart();
    if (!hasPro()) {
      charts.reportYear?.destroy();
      charts.reportYear = null;
      return;
    }

    const currentRows = monthTransactions(selectedKey);
    const expenseRows = currentRows.filter((row) => row.type === 'expense');
    const allRows = state.transactions;
    const periodRows = allRows.filter((row) => monthKey(row.transaction_date) === selectedKey);
    const pendingIncomeRows = periodRows.filter((row) => row.status === 'pending' && row.type === 'income');
    const pendingExpenseRows = periodRows.filter((row) => row.status === 'pending' && row.type === 'expense');
    const pendingIncome = pendingIncomeRows.reduce((sum, row) => sum + Number(row.amount), 0);
    const pendingExpense = pendingExpenseRows.reduce((sum, row) => sum + Number(row.amount), 0);
    const selectedMonthEnd = new Date(selectedYear, selectedMonth, 0, 23, 59, 59);
    const recurring = allRows.filter((row) => row.recurring && !row.recurrence_source_id && new Date(`${row.transaction_date}T12:00:00`) <= selectedMonthEnd);
    const recurringFactor = (row) => row.recurrence_interval === 'weekly' ? 52 / 12 : row.recurrence_interval === 'yearly' ? 1 / 12 : 1;
    const recurringIncome = recurring.filter((row) => row.type === 'income').reduce((sum, row) => sum + Number(row.amount) * recurringFactor(row), 0);
    const recurringExpense = recurring.filter((row) => row.type === 'expense').reduce((sum, row) => sum + Number(row.amount) * recurringFactor(row), 0);
    const biggestExpense = expenseRows.slice().sort((a, b) => Number(b.amount) - Number(a.amount))[0];
    const daysInMonth = new Date(selectedYear, selectedMonth, 0).getDate();
    const daysElapsed = selectedKey === currentMonthKey() ? Math.max(1, new Date().getDate()) : daysInMonth;
    const averageDailyExpense = totals.expense / Math.max(1, daysElapsed);
    const averageTicket = currentRows.length ? currentRows.reduce((sum, row) => sum + Number(row.amount), 0) / currentRows.length : 0;
    const yearSeries = monthSeries(12, selectedKey);
    const monthsWithExpense = yearSeries.filter((item) => item.expense > 0);
    const lastExpenseMonths = monthsWithExpense.slice(-3);
    const averageMonthlyExpense = lastExpenseMonths.length ? lastExpenseMonths.reduce((sum, item) => sum + item.expense, 0) / lastExpenseMonths.length : 0;
    const bestMonth = yearSeries.slice().sort((a, b) => b.net - a.net)[0];
    const worstMonth = yearSeries.slice().sort((a, b) => a.net - b.net)[0];
    const budgetRows = state.categories.filter((category) => category.type === 'expense' && Number(category.budget) > 0).map((category) => ({ ...category, spent: categorySpent(category.id, selectedKey), limit: Number(category.budget) })).sort((a, b) => (b.spent / b.limit) - (a.spent / a.limit));

    $('#report-comparison').innerHTML = [
      ['Receita vs. mês anterior', brl.format(totals.income - previous.income), deltaText(totals.income, previous.income)],
      ['Despesa vs. mês anterior', brl.format(totals.expense - previous.expense), deltaText(totals.expense, previous.expense)],
      ['Variação do resultado', brl.format(totals.net - previous.net), deltaText(totals.net, previous.net)],
      ['Média de despesas (3m)', brl.format(averageMonthlyExpense), lastExpenseMonths.length ? `${lastExpenseMonths.length} meses com despesas considerados` : 'sem base suficiente']
    ].map(([label, value, detail]) => `<article><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong><small>${escapeHTML(detail)}</small></article>`).join('');

    $('#report-health').innerHTML = [
      ['Lançamentos realizados', String(currentRows.length), selectedLabel],
      ['Ticket médio', brl.format(averageTicket), 'média por lançamento realizado'],
      ['Gasto médio diário', brl.format(averageDailyExpense), `em ${daysElapsed} dias considerados`],
      ['Maior saída', biggestExpense ? brl.format(Number(biggestExpense.amount)) : brl.format(0), biggestExpense?.description || 'sem saídas'],
      ['Melhor mês (12m)', brl.format(bestMonth?.net || 0), bestMonth?.label || '—'],
      ['Pior mês (12m)', brl.format(worstMonth?.net || 0), worstMonth?.label || '—']
    ].map(([label, value, detail]) => `<div class="metric-row"><div><span>${escapeHTML(label)}</span><small>${escapeHTML(detail)}</small></div><strong>${escapeHTML(value)}</strong></div>`).join('');

    $('#report-pending').innerHTML = [
      ['A receber', brl.format(pendingIncome), `${pendingIncomeRows.length} lançamentos em ${selectedLabel}`],
      ['A pagar', brl.format(pendingExpense), `${pendingExpenseRows.length} lançamentos em ${selectedLabel}`],
      ['Saldo pendente', brl.format(pendingIncome - pendingExpense), 'impacto líquido se tudo ocorrer']
    ].map(([label, value, detail]) => `<div class="metric-row"><div><span>${escapeHTML(label)}</span><small>${escapeHTML(detail)}</small></div><strong>${escapeHTML(value)}</strong></div>`).join('');

    $('#report-recurring').innerHTML = [
      ['Entradas recorrentes', brl.format(recurringIncome), 'equivalência mensal cadastrada até o período'],
      ['Saídas recorrentes', brl.format(recurringExpense), 'equivalência mensal cadastrada até o período'],
      ['Resultado recorrente', brl.format(recurringIncome - recurringExpense), `${recurring.length} compromissos considerados`]
    ].map(([label, value, detail]) => `<div class="metric-row"><div><span>${escapeHTML(label)}</span><small>${escapeHTML(detail)}</small></div><strong>${escapeHTML(value)}</strong></div>`).join('');

    const accountMovements = state.accounts.filter((account) => !account.archived).map((account) => {
      const rows = currentRows.filter((row) => row.account_id === account.id);
      const net = rows.reduce((sum, row) => sum + (row.type === 'income' ? Number(row.amount) : -Number(row.amount)), 0);
      return { ...account, net, count: rows.length };
    }).filter((account) => account.count > 0).sort((a, b) => Math.abs(b.net) - Math.abs(a.net));
    $('#report-accounts').innerHTML = accountMovements.map((account) => `<div class="rank-row"><span>${escapeHTML(account.icon)}</span><div><strong>${escapeHTML(account.name)}</strong><small>${account.count} ${account.count === 1 ? 'lançamento' : 'lançamentos'} no mês</small></div><b class="${account.net < 0 ? 'value-expense' : 'value-income'}">${account.net >= 0 ? '+' : '−'} ${brl.format(Math.abs(account.net))}</b></div>`).join('') || emptyState('▣', 'Sem movimentação', `Nenhuma conta teve lançamentos realizados em ${selectedLabel}.`);

    $('#report-budget-analysis').innerHTML = budgetRows.slice(0, 7).map((category) => {
      const percent = category.limit ? category.spent / category.limit * 100 : 0;
      return `<div class="rank-row"><span>${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>${percent.toFixed(1).replace('.', ',')}% do limite · ${brl.format(Math.max(0, category.limit - category.spent))} disponível</small></div><b class="${percent > 100 ? 'value-expense' : ''}">${brl.format(category.spent)}</b></div>`;
    }).join('') || emptyState('◉', 'Sem limites', 'Defina orçamentos para medir eficiência.');

    const biggestCategory = expenses[0];
    const budgetOver = budgetRows.filter((row) => row.spent > row.limit);
    const insights = [
      ['↘', 'Peso das despesas', totals.income ? `As saídas consomem ${(totals.expense / totals.income * 100).toFixed(1).replace('.', ',')}% das receitas de ${selectedLabel}.` : `Não há receita suficiente em ${selectedLabel} para medir o peso das despesas.`],
      ['◎', 'Taxa de economia', totals.income ? `Você preservou ${totals.savingsRate.toFixed(1).replace('.', ',')}% do que entrou. A comparação com o mês anterior é de ${(totals.savingsRate - previous.savingsRate).toFixed(1).replace('.', ',')} p.p.` : 'Registre receitas para calcular sua taxa de economia.'],
      ['◈', 'Concentração de gastos', biggestCategory ? `${biggestCategory.name} representa ${(biggestCategory.total / Math.max(1, totals.expense) * 100).toFixed(1).replace('.', ',')}% das despesas do mês selecionado.` : 'Não há concentração de despesas calculável no mês selecionado.'],
      ['◇', 'Pendências', `Há ${brl.format(pendingIncome)} a receber e ${brl.format(pendingExpense)} a pagar no mês selecionado.`],
      ['↻', 'Base recorrente', `Até esse período, os compromissos recorrentes equivalem a ${brl.format(recurringExpense)} em saídas e ${brl.format(recurringIncome)} em entradas por mês.`],
      ['!', 'Orçamentos', budgetOver.length ? `${budgetOver.length} ${budgetOver.length === 1 ? 'categoria ultrapassou' : 'categorias ultrapassaram'} o limite no mês selecionado.` : 'Nenhum orçamento com limite definido foi ultrapassado no mês selecionado.']
    ];
    $('#insights-grid').innerHTML = insights.map(([icon, title, body]) => `<div class="insight"><span>${icon}</span><strong>${escapeHTML(title)}</strong><p>${escapeHTML(body)}</p></div>`).join('');
    renderYearReportChart(yearSeries);
  }
'''
js = sub_once(js, r"  function renderReports\(\) \{.*?\n  \}\n\n  function renderReportChart", new_render_reports + "\n  function renderReportChart", 'render reports')
js = replace_once(js, '    const series = monthSeries(6);\n    charts.report?.destroy();', '    const series = monthSeries(6, reportMonthKey);\n    charts.report?.destroy();', 'report chart anchor')

new_render_selects = r'''  function renderSelectOptions(type = null) {
    const transactionType = type || $('input[name="transaction_type"]:checked')?.value || 'expense';
    $('#tx-category').innerHTML = state.categories.filter((category) => category.type === transactionType).map((category) => `<option value="${category.id}">${escapeHTML(category.icon)} ${escapeHTML(category.name)}</option>`).join('');
    $('#tx-account').innerHTML = state.accounts.map((account) => `<option value="${account.id}">${escapeHTML(account.icon)} ${escapeHTML(account.name)}</option>`).join('');
    const goalSelect = $('#tx-goal');
    if (goalSelect) goalSelect.innerHTML = `<option value="">Nenhuma meta</option>${state.goals.map((goal) => `<option value="${goal.id}">${escapeHTML(goal.icon)} ${escapeHTML(goal.name)}</option>`).join('')}`;
  }
'''
js = sub_once(js, r"  function renderSelectOptions\(type = null\) \{.*?\n  \}\n\n  function renderFeatureLocks", new_render_selects + "\n  function renderFeatureLocks", 'render select options')
js = replace_once(js, "    $('#tx-recurring').disabled = !hasPro();\n", "    $('#tx-recurring').disabled = !hasPro();\n    if ($('#tx-goal-wrap')) $('#tx-goal-wrap').hidden = !hasPro();\n", 'goal feature lock')

js = replace_once(
    js,
    "    $('#tx-account').value = row?.account_id || $('#tx-account').options[0]?.value || '';\n    $('#tx-status').value = row?.status || 'paid';",
    "    $('#tx-account').value = row?.account_id || $('#tx-account').options[0]?.value || '';\n    $('#tx-goal').value = row?.goal_id || transactionGoalPreset || '';\n    transactionGoalPreset = null;\n    $('#tx-status').value = row?.status || 'paid';",
    'transaction goal selection'
)
js = replace_once(
    js,
    "        account_id: $('#tx-account').value,\n        status: $('#tx-status').value,",
    "        account_id: $('#tx-account').value,\n        goal_id: hasPro() ? ($('#tx-goal').value || null) : null,\n        status: $('#tx-status').value,",
    'transaction goal payload'
)

js = replace_once(
    js,
    "      fields.innerHTML = `<label class=\"full\">Nome<input name=\"name\" maxlength=\"80\" required value=\"${escapeHTML(row?.name || '')}\" placeholder=\"Ex: Mercado\" /></label><label>Tipo<select name=\"type\"><option value=\"expense\">Saída</option><option value=\"income\">Entrada</option></select></label><label>Limite mensal<div class=\"money-field\"><span>R$</span><input name=\"budget\" inputmode=\"decimal\" value=\"${row ? Number(row.budget || 0).toFixed(2).replace('.', ',') : '0,00'}\" /></div></label><label>Ícone<input name=\"icon\" maxlength=\"8\" value=\"${escapeHTML(row?.icon || '•')}\" /></label><label>Cor<input name=\"color\" type=\"color\" value=\"${escapeHTML(row?.color || '#4f7de8')}\" /></label>`;\n      fields.querySelector('[name=\"type\"]').value = row?.type || categoryType;",
    "      fields.innerHTML = `<label class=\"full\">Nome<input name=\"name\" maxlength=\"80\" required value=\"${escapeHTML(row?.name || '')}\" placeholder=\"Ex: Mercado\" /></label><label>Tipo<select name=\"type\"><option value=\"expense\">Saída</option><option value=\"income\">Entrada</option></select></label><label>Limite mensal<div class=\"money-field\"><span>R$</span><input name=\"budget\" inputmode=\"decimal\" value=\"${row ? Number(row.budget || 0).toFixed(2).replace('.', ',') : '0,00'}\" /></div><small class=\"field-help\">Disponível apenas para categorias de saída.</small></label><label>Ícone<input name=\"icon\" maxlength=\"8\" value=\"${escapeHTML(row?.icon || '•')}\" /></label><label>Cor<input name=\"color\" type=\"color\" value=\"${escapeHTML(row?.color || '#4f7de8')}\" /></label>`;\n      const categoryTypeSelect = fields.querySelector('[name=\"type\"]');\n      categoryTypeSelect.value = row?.type || categoryType;\n      const budgetLabel = fields.querySelector('[name=\"budget\"]')?.closest('label');\n      const syncBudgetVisibility = () => {\n        const expense = categoryTypeSelect.value === 'expense';\n        if (budgetLabel) budgetLabel.hidden = !expense;\n        if (!expense) fields.querySelector('[name=\"budget\"]').value = '0,00';\n      };\n      categoryTypeSelect.addEventListener('change', syncBudgetVisibility);\n      syncBudgetVisibility();",
    'category budget relevance'
)
js = js.replace('Valor atual<div class="money-field">', 'Valor já acumulado<div class="money-field">')
js = js.replace("<input name=\"current_amount\" inputmode=\"decimal\" value=\"${row ? Number(row.current_amount).toFixed(2).replace('.', ',') : '0,00'}\" /></div></label><label>Prazo", "<input name=\"current_amount\" inputmode=\"decimal\" value=\"${row ? Number(row.current_amount).toFixed(2).replace('.', ',') : '0,00'}\" /></div><small class=\"field-help\">Use aqui somente o valor que já existia antes dos lançamentos vinculados.</small></label><label>Prazo")
js = replace_once(
    js,
    "        const payload = { user_id: state.user.id, name: form.get('name').trim(), type: form.get('type'), budget: Math.max(0, parseMoney(form.get('budget'))), icon: form.get('icon').trim() || '•', color: form.get('color') || COLORS[1] };",
    "        const payload = { user_id: state.user.id, name: form.get('name').trim(), type: form.get('type'), budget: form.get('type') === 'expense' ? Math.max(0, parseMoney(form.get('budget'))) : 0, icon: form.get('icon').trim() || '•', color: form.get('color') || COLORS[1] };",
    'category save budget'
)

new_contribute = r'''  async function contributeGoal(id) {
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
js = sub_once(js, r"  async function contributeGoal\(id\) \{.*?\n  \}\n\n  function exportCSV", new_contribute + "\n  function exportCSV", 'goal contribution flow')

new_export = r'''  function exportCSV(monthFilter = null) {
    const source = monthFilter ? state.transactions.filter((row) => monthKey(row.transaction_date) === monthFilter) : state.transactions;
    const rows = [['Descrição', 'Tipo', 'Categoria', 'Conta', 'Meta', 'Data', 'Status', 'Recorrente', 'Valor'], ...source.map((row) => [row.description, row.type === 'income' ? 'Entrada' : 'Saída', categoryById(row.category_id).name, accountById(row.account_id).name, goalById(row.goal_id)?.name || '', row.transaction_date, row.status === 'paid' ? 'Pago' : 'Pendente', row.recurring ? 'Sim' : 'Não', Number(row.amount).toFixed(2).replace('.', ',')])];
    const csv = '\uFEFF' + rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(';')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = monthFilter ? `salesboard-relatorio-${monthFilter}.csv` : `salesboard-lancamentos-${isoDate()}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    toast('Exportação concluída', monthFilter ? `O CSV de ${monthFilter} foi preparado.` : 'Seu arquivo CSV foi preparado.');
  }
'''
js = sub_once(js, r"  function exportCSV\(\) \{.*?\n  \}\n\n  async function subscribe", new_export + "\n  async function subscribe", 'csv month filter')

js = replace_once(
    js,
    "    $('#settings-type').value = state.profile?.workspace_type || 'personal';\n    $('#settings-currency').value = state.profile?.currency || 'BRL';\n",
    '',
    'remove meaningless settings bindings'
)

js = replace_once(
    js,
    "    onboardingStep = 1;\n    updateOnboardingStep();",
    "    onboardingStep = 1;\n    updateOnboardingTemplatePreview();\n    updateOnboardingStep();",
    'onboarding preview init'
)

preview_function = r'''  function updateOnboardingTemplatePreview() {
    const type = $('input[name="workspace_type"]:checked')?.value || 'personal';
    const templates = {
      personal: ['🏠 Moradia', '🛒 Alimentação', '🚗 Transporte', '❤️ Saúde', '🎮 Lazer', '💡 Serviços', '💼 Salário', '💰 Renda extra'],
      freelancer: ['🧰 Ferramentas', '🧾 Impostos', '📣 Marketing', '🚗 Transporte', '💡 Serviços', '• Outras despesas', '💼 Clientes', '💰 Outras receitas'],
      business: ['📦 Fornecedores', '⚙️ Operação', '📣 Marketing', '🧾 Impostos', '💡 Serviços', '• Outras despesas', '💼 Vendas e serviços', '💰 Outras receitas']
    };
    const preview = $('#seed-preview');
    if (preview) preview.innerHTML = templates[type].map((item) => `<span>${escapeHTML(item)}</span>`).join('');
  }

'''
js = replace_once(js, '  function updateOnboardingStep() {\n', preview_function + '  function updateOnboardingStep() {\n', 'onboarding template function')

new_finish = r'''  async function finishOnboarding(event) {
    event.preventDefault();
    const button = $('#onboarding-finish');
    setButtonLoading(button, true, 'Criando seu espaço...');
    try {
      const needsTerms = !state.profile?.terms_accepted_at;
      if (needsTerms && !$('#oauth-accept-terms')?.checked) throw new Error('Aceite os Termos de Uso e a Política de Privacidade para continuar.');
      const workspaceType = $('input[name="workspace_type"]:checked').value;
      const workspaceName = $('#workspace-name-input').value.trim() || 'Meu espaço';
      const { error } = await supabaseClient.rpc('complete_salesboard_onboarding', {
        p_workspace_type: workspaceType,
        p_workspace_name: workspaceName,
        p_account_name: $('#first-account-name').value.trim() || 'Conta principal',
        p_account_type: $('#first-account-type').value,
        p_opening_balance: parseMoney($('#first-account-balance').value),
        p_create_budgets: false,
        p_accept_terms: needsTerms ? Boolean($('#oauth-accept-terms')?.checked) : false
      });
      if (error) throw error;
      const { data: profile, error: profileError } = await supabaseClient.from('profiles').select('*').eq('id', state.user.id).single();
      if (profileError) throw profileError;
      state.profile = profile;
      await loadFinancialData();
      enterApp();
      toast('Seu espaço está pronto', 'Agora registre sua primeira movimentação e defina seus próprios limites quando quiser.');
    } catch (error) {
      toast('Não foi possível concluir', friendlyError(error), 'error');
    } finally {
      setButtonLoading(button, false);
    }
  }
'''
js = sub_once(js, r"  async function finishOnboarding\(event\) \{.*?\n  \}\n\n  async function saveProfile", new_finish + "\n  async function saveProfile", 'atomic onboarding frontend')

new_save_profile = r'''  async function saveProfile(event) {
    event.preventDefault();
    if (demoMode) {
      state.profile.full_name = $('#settings-name').value.trim();
      state.profile.workspace_name = $('#settings-workspace').value.trim();
      renderIdentity();
      toast('Configurações atualizadas na demonstração');
      return;
    }
    try {
      const payload = { full_name: $('#settings-name').value.trim(), workspace_name: $('#settings-workspace').value.trim() };
      const { data, error } = await supabaseClient.from('profiles').update(payload).eq('id', state.user.id).select().single();
      if (error) throw error;
      state.profile = data;
      renderIdentity();
      toast('Perfil atualizado');
    } catch (error) {
      toast('Não foi possível atualizar', friendlyError(error), 'error');
    }
  }
'''
js = sub_once(js, r"  async function saveProfile\(event\) \{.*?\n  \}\n\n  async function logout", new_save_profile + "\n  async function logout", 'save profile options')

js = replace_once(
    js,
    "    $$('input[name=\"transaction_type\"]').forEach((radio) => radio.addEventListener('change', () => renderSelectOptions(radio.value)));\n",
    "    $$('input[name=\"transaction_type\"]').forEach((radio) => radio.addEventListener('change', () => renderSelectOptions(radio.value)));\n    $$('input[name=\"workspace_type\"]').forEach((radio) => radio.addEventListener('change', updateOnboardingTemplatePreview));\n",
    'onboarding type listener'
)
js = replace_once(js, "    $('#reports-export').addEventListener('click', exportCSV);", "    $('#reports-export').addEventListener('click', () => exportCSV(reportMonthKey));", 'report export filter')
js = replace_once(
    js,
    "    $('#transaction-search').addEventListener('input', renderTransactions);\n",
    "    $('#transaction-search').addEventListener('input', renderTransactions);\n    $('#report-month').addEventListener('change', (event) => { reportMonthKey = event.target.value || currentMonthKey(); renderReports(); });\n",
    'report month listener'
)
write(path, js)

# ---------- app/quality.css ----------
path = 'salesboard/app/quality.css'
css = read(path)
css += '''\n\n/* Product-coherence controls */\n.report-actions{display:flex;align-items:flex-end;gap:10px;flex-wrap:wrap}\n.report-month-filter{display:grid;gap:5px;font-size:12px;color:#6f7d8f;font-weight:700}\n.report-month-filter input{min-height:40px;border:1px solid #dbe2ea;border-radius:10px;background:#fff;color:#172130;padding:8px 10px;font:inherit}\n.field-help{display:block;margin-top:6px;color:#7d8998;font-size:11px;line-height:1.35;font-weight:500}\n.setting-note{padding:12px 14px;border:1px solid #e2e7ed;border-radius:12px;background:#f8fafb;display:grid;gap:3px}\n.setting-note span{font-size:12px;color:#7b8796}\n.setting-note strong{font-size:14px;color:#172130}\n.setting-note small,.onboarding-helper{color:#7d8998;line-height:1.45}\n\n@media(max-width:680px){\n  .report-actions{width:100%;display:grid;grid-template-columns:1fr auto}\n  .report-month-filter{min-width:0}\n  .report-month-filter input{width:100%;min-width:0}\n}\n\n@media(max-width:360px){\n  .report-actions{grid-template-columns:1fr}\n  .report-actions .button{width:100%}\n}\n'''
write(path, css)

# ---------- README ----------
path = 'salesboard/README.md'
readme = read(path)
readme = readme.replace('- orçamentos e metas;\n', '- orçamentos e metas vinculáveis a lançamentos;\n')
readme = readme.replace('- relatórios essenciais/avançados conforme entitlement;\n', '- relatórios essenciais/avançados conforme entitlement, com filtro mensal simples;\n')
readme = readme.replace('- onboarding transacional;\n', '- onboarding transacional, com categorias iniciais coerentes com Pessoal/Autônomo/Negócio e sem orçamentos monetários arbitrários;\n')
readme = readme.replace('- referências conta/categoria/recorrência validadas no banco;\n', '- referências conta/categoria/meta/recorrência validadas no banco;\n')
write(path, readme)

# ---------- production CI ----------
path = '.github/workflows/salesboard-production-check.yml'
ci = read(path)
ci = replace_once(ci, '010_profile_security_defaults; do', '010_profile_security_defaults 011_product_coherence; do', 'ci migration list')
ci = replace_once(
    ci,
    "          grep -Fq 'revoke execute on function public.current_entitlement(uuid)' salesboard/supabase/005_lock_entitlement_rpc.sql\n",
    "          grep -Fq 'revoke execute on function public.current_entitlement(uuid)' salesboard/supabase/005_lock_entitlement_rpc.sql\n          grep -Fq 'goal_id' salesboard/supabase/011_product_coherence.sql\n          grep -Fq 'categories_income_budget_zero' salesboard/supabase/011_product_coherence.sql\n",
    'ci coherence migration checks'
)
ci = replace_once(
    ci,
    "          grep -Fq 'Gerenciar cobrança' salesboard/app/index.html\n",
    "          grep -Fq 'Gerenciar cobrança' salesboard/app/index.html\n          grep -Fq 'id=\"report-month\"' salesboard/app/index.html\n          grep -Fq 'id=\"tx-goal\"' salesboard/app/index.html\n          if grep -Fq '2 meses grátis' salesboard/index.html salesboard/app/index.html; then echo 'Annual plan must not be advertised as extra free trial time'; exit 1; fi\n",
    'ci product copy checks'
)
write(path, ci)

print('SalesBoard product coherence patch applied successfully.')
