from pathlib import Path


def replace_between(text, start_marker, end_marker, replacement):
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement + text[end:]


# Landing: 3-day trial + coherent plan matrix.
landing = Path('salesboard/index.html')
text = landing.read_text(encoding='utf-8')
text = text.replace('7 dias grátis', '3 dias grátis').replace('7 dias', '3 dias')
pricing_start = '<div class="pricing-grid launch-pricing-grid">'
pricing_end = '      <p class="pricing-footnote">'
pricing = '''<div class="pricing-grid launch-pricing-grid">
        <article class="price-card"><div><span class="plan-tag">Essencial</span><h3>Controle completo para o dia a dia</h3><p>Organize sua rotina financeira com tudo que precisa para acompanhar o mês com clareza.</p></div><div class="price"><small>R$</small><strong data-monthly="14,90" data-annual="12,42">14,90</strong><span>/mês</span></div><a class="btn btn-outline-dark btn-block plan-link" data-plan="essential" href="app/?mode=register&plan=essential&billing=monthly">Começar grátis</a><ul><li>✓ Lançamentos ilimitados</li><li>✓ Até 3 contas ativas</li><li>✓ Categorias personalizadas</li><li>✓ Orçamentos mensais</li><li>✓ Dashboard completo</li><li>✓ Relatórios essenciais</li><li>✓ Busca, filtros e exportação CSV</li></ul></article>
        <article class="price-card popular"><div class="popular-ribbon">Mais completo</div><div><span class="plan-tag">Pro</span><h3>Planejamento e análise avançada</h3><p>Para quem quer transformar dados financeiros em decisões, previsibilidade e evolução.</p></div><div class="price"><small>R$</small><strong data-monthly="24,90" data-annual="20,75">24,90</strong><span>/mês</span></div><a class="btn btn-primary btn-block plan-link" data-plan="pro" href="app/?mode=register&plan=pro&billing=monthly">Testar o Pro grátis</a><ul><li>✓ Tudo do Essencial</li><li>✓ Contas ilimitadas</li><li>✓ Metas financeiras</li><li>✓ Lançamentos recorrentes</li><li>✓ Relatórios avançados de 12 meses</li><li>✓ Comparações, pendências e compromissos</li><li>✓ Diagnósticos de contas e orçamentos</li><li>✓ Insights financeiros avançados</li></ul></article>
      </div>
'''
text = replace_between(text, pricing_start, pricing_end, pricing)
comparison_start = '<section class="comparison-section">'
comparison_end = '    <section class="section-light faq-section"'
comparison = '''<section class="comparison-section"><div class="section-heading center"><span class="eyebrow">Sem letra miúda</span><h2>Você sabe exatamente o que está contratando.</h2></div><div class="comparison-wrap"><table><thead><tr><th>Recurso</th><th>Essencial</th><th>Pro</th></tr></thead><tbody><tr><td>Lançamentos</td><td>Ilimitados</td><td>Ilimitados</td></tr><tr><td>Contas ativas</td><td>Até 3</td><td>Ilimitadas</td></tr><tr><td>Categorias personalizadas</td><td>✓</td><td>✓</td></tr><tr><td>Orçamentos mensais</td><td>✓</td><td>✓</td></tr><tr><td>Dashboard financeiro</td><td>✓</td><td>✓</td></tr><tr><td>Relatórios essenciais</td><td>✓</td><td>✓</td></tr><tr><td>Relatórios avançados e insights</td><td>—</td><td>✓</td></tr><tr><td>Metas financeiras</td><td>—</td><td>✓</td></tr><tr><td>Lançamentos recorrentes</td><td>—</td><td>✓</td></tr><tr><td>Busca e filtros</td><td>✓</td><td>✓</td></tr><tr><td>Exportação CSV</td><td>✓</td><td>✓</td></tr></tbody></table></div></section>

'''
text = replace_between(text, comparison_start, comparison_end, comparison)
landing.write_text(text, encoding='utf-8')

# App HTML: OAuth, 3-day copy, advanced reports and plan descriptions.
app_html = Path('salesboard/app/index.html')
html = app_html.read_text(encoding='utf-8')
html = html.replace('7 dias grátis', '3 dias grátis').replace('7 dias restantes', '3 dias restantes').replace('7 dias', '3 dias')
tabs = '<div class="auth-tabs"><button data-auth-mode="login" class="active">Entrar</button><button data-auth-mode="register">Criar conta</button></div>'
google = tabs + '''
        <button type="button" class="google-auth-button" id="google-auth-button"><span class="google-g">G</span><span>Continuar com Google</span></button><div class="auth-divider"><span>ou continue com e-mail</span></div>'''
if 'id="google-auth-button"' not in html:
    html = html.replace(tabs, google, 1)
if 'id="oauth-terms-wrap"' not in html:
    html = html.replace('<div class="seed-preview">', '<label class="check oauth-terms" id="oauth-terms-wrap" hidden><input id="oauth-accept-terms" type="checkbox" /> <span>Li e aceito os <a href="../legal/termos.html" target="_blank" rel="noopener">Termos de Uso</a> e a <a href="../legal/privacidade.html" target="_blank" rel="noopener">Política de Privacidade</a>.</span></label><div class="seed-preview">', 1)

reports_start = '        <section class="view" data-page="reports">'
reports_end = '        <section class="view" data-page="billing">'
reports = '''        <section class="view" data-page="reports"><div class="page-head"><div><span class="kicker">Análise</span><h1>Relatórios</h1><p>Entenda o que aconteceu, o que mudou e onde sua atenção financeira gera mais resultado.</p></div><button class="button subtle" id="reports-export">Exportar CSV</button></div><div id="report-summary" class="summary-grid report-summary"></div><div class="dashboard-grid"><article class="panel"><div class="panel-head"><div><strong>Resultado por mês</strong><small>Visão histórica do período</small></div></div><div class="chart-box"><canvas id="report-chart"></canvas></div></article><article class="panel"><div class="panel-head"><div><strong>Maiores despesas</strong><small>Categorias do mês atual</small></div></div><div id="report-categories" class="rank-list"></div></article></div><div id="report-pro-lock" class="locked-banner report-lock" hidden>O Essencial inclui os indicadores e o histórico principal. Comparações profundas, projeções, pendências, recorrências e diagnósticos fazem parte do Pro.<button data-view="billing">Ver plano Pro →</button></div><div id="report-pro-details"><div class="report-section-title"><div><span class="kicker">Pro · análise detalhada</span><h2>Diagnóstico financeiro</h2></div><small>Calculado diretamente a partir dos seus lançamentos</small></div><div id="report-comparison" class="mini-summary report-comparison"></div><div class="dashboard-grid report-deep-grid"><article class="panel"><div class="panel-head"><div><strong>Últimos 12 meses</strong><small>Entradas, saídas e resultado</small></div></div><div class="chart-box tall"><canvas id="report-year-chart"></canvas></div></article><article class="panel"><div class="panel-head"><div><strong>Saúde do período</strong><small>Eficiência, ritmo e concentração</small></div></div><div id="report-health" class="metric-list"></div></article></div><div class="report-detail-grid"><article class="panel"><div class="panel-head"><div><strong>Pendências</strong><small>Valores ainda não realizados</small></div></div><div id="report-pending" class="metric-list compact"></div></article><article class="panel"><div class="panel-head"><div><strong>Compromissos recorrentes</strong><small>Equivalência mensal estimada</small></div></div><div id="report-recurring" class="metric-list compact"></div></article><article class="panel"><div class="panel-head"><div><strong>Distribuição por conta</strong><small>Saldo consolidado</small></div></div><div id="report-accounts" class="rank-list compact"></div></article><article class="panel"><div class="panel-head"><div><strong>Eficiência dos orçamentos</strong><small>Planejado x realizado</small></div></div><div id="report-budget-analysis" class="rank-list compact"></div></article></div><article class="panel insights-panel"><div class="panel-head"><div><strong>Leituras do período</strong><small>Insights calculados a partir dos seus dados</small></div><span class="smart-chip">✦ Análise avançada</span></div><div id="insights-grid" class="insights-grid"></div></article></div></section>

'''
html = replace_between(html, reports_start, reports_end, reports)
html = html.replace('Até 3 contas, categorias, orçamentos e relatórios essenciais.', 'Até 3 contas, lançamentos ilimitados, orçamentos e relatórios essenciais.')
html = html.replace('Contas ilimitadas, metas, recorrências e relatórios avançados.', 'Contas ilimitadas, metas, recorrências e relatórios avançados de 12 meses.')
app_html.write_text(html, encoding='utf-8')

# App JS: demo = active Pro, Google OAuth, OAuth terms and detailed reports.
app_js = Path('salesboard/app/app.js')
js = app_js.read_text(encoding='utf-8')
js = js.replace("    const trialEnd = new Date(now.getTime() + 7 * 86400000).toISOString();", "    const trialEnd = new Date(now.getTime() + 3 * 86400000).toISOString();")
old_profile = "    state.profile = { id: 'demo-user', full_name: 'Conta demonstração', workspace_name: 'Meu espaço financeiro', workspace_type: 'personal', plan: 'pro', subscription_status: 'trialing', trial_ends_at: trialEnd, onboarded: true, currency: 'BRL' };"
new_profile = "    state.profile = { id: 'demo-user', full_name: 'Conta demonstração', workspace_name: 'Demonstração Pro', workspace_type: 'business', plan: 'pro', subscription_status: 'active', trial_ends_at: trialEnd, onboarded: true, currency: 'BRL', terms_accepted_at: new Date().toISOString() };"
js = js.replace(old_profile, new_profile)
js = js.replace('    for (let monthOffset = 1; monthOffset <= 5; monthOffset += 1) {', '    for (let monthOffset = 1; monthOffset <= 11; monthOffset += 1) {')
js = js.replace('    state.subscription = null;\n    enterApp();', "    state.subscription = { plan: 'pro', status: 'active', billing_cycle: 'annual', cancel_at_period_end: false, current_period_end: new Date(now.getFullYear() + 1, now.getMonth(), now.getDate()).toISOString() };\n    enterApp();", 1)

setup_old = "  function setupOnboarding() {\n    $('#workspace-name-input').value = state.profile?.workspace_name || 'Meu espaço';\n    onboardingStep = 1;\n    updateOnboardingStep();\n  }"
setup_new = "  function setupOnboarding() {\n    $('#workspace-name-input').value = state.profile?.workspace_name || 'Meu espaço';\n    const oauthTerms = $('#oauth-terms-wrap');\n    if (oauthTerms) {\n      oauthTerms.hidden = Boolean(state.profile?.terms_accepted_at);\n      const checkbox = $('#oauth-accept-terms');\n      if (checkbox) checkbox.checked = Boolean(state.profile?.terms_accepted_at);\n    }\n    onboardingStep = 1;\n    updateOnboardingStep();\n  }"
if setup_old not in js:
    raise SystemExit('setupOnboarding marker changed')
js = js.replace(setup_old, setup_new, 1)

finish_marker = "    try {\n      const workspaceType = $('input[name=\"workspace_type\"]:checked').value;"
finish_injection = "    try {\n      const needsTerms = !state.profile?.terms_accepted_at;\n      if (needsTerms && !$('#oauth-accept-terms')?.checked) throw new Error('Aceite os Termos de Uso e a Política de Privacidade para continuar.');\n      const workspaceType = $('input[name=\"workspace_type\"]:checked').value;"
if finish_marker not in js:
    raise SystemExit('finishOnboarding marker changed')
js = js.replace(finish_marker, finish_injection, 1)
profile_update_old = "      const { data: profile, error: profileError } = await supabaseClient.from('profiles').update({ workspace_type: workspaceType, workspace_name: workspaceName, onboarded: true }).eq('id', state.user.id).select().single();"
profile_update_new = "      const profilePayload = { workspace_type: workspaceType, workspace_name: workspaceName, onboarded: true };\n      if (!state.profile?.terms_accepted_at) { profilePayload.terms_accepted_at = new Date().toISOString(); profilePayload.terms_version = '2026-08-12'; }\n      const { data: profile, error: profileError } = await supabaseClient.from('profiles').update(profilePayload).eq('id', state.user.id).select().single();"
if profile_update_old not in js:
    raise SystemExit('profile onboarding update marker changed')
js = js.replace(profile_update_old, profile_update_new, 1)

google_fn_marker = '  function initStaticEvents() {'
google_fn = '''  async function signInWithGoogle() {
    const button = $('#google-auth-button');
    if (!supabaseClient) return;
    setButtonLoading(button, true, 'Abrindo Google...');
    setAuthMessage('');
    try {
      const redirectTo = `${location.origin}${location.pathname}?oauth=google`;
      const { error } = await supabaseClient.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo, queryParams: { prompt: 'select_account' } }
      });
      if (error) throw error;
    } catch (error) {
      setButtonLoading(button, false);
      const message = String(error?.message || error || '');
      setAuthMessage(message.toLowerCase().includes('provider') ? 'O login com Google ainda precisa ser ativado no Supabase Auth. Use e-mail e senha enquanto a configuração externa não estiver concluída.' : friendlyError(error), true);
    }
  }

'''
if 'async function signInWithGoogle()' not in js:
    js = js.replace(google_fn_marker, google_fn + google_fn_marker, 1)
listener_marker = "  function initStaticEvents() {\n    $$('[data-auth-mode]').forEach((button) => button.addEventListener('click', () => setAuthMode(button.dataset.authMode)));"
listener_new = "  function initStaticEvents() {\n    $('#google-auth-button')?.addEventListener('click', signInWithGoogle);\n    $$('[data-auth-mode]').forEach((button) => button.addEventListener('click', () => setAuthMode(button.dataset.authMode)));"
if listener_marker not in js:
    raise SystemExit('initStaticEvents marker changed')
js = js.replace(listener_marker, listener_new, 1)

reports_js_start = '  function renderReports() {'
reports_js_end = '  function renderBilling() {'
reports_js = r'''  function renderReports() {
    const totals = totalsForMonth();
    const now = new Date();
    const previousDate = new Date(now.getFullYear(), now.getMonth() - 1, 1);
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

    const expenses = state.categories.filter((category) => category.type === 'expense').map((category) => ({ ...category, total: categorySpent(category.id) })).filter((category) => category.total > 0).sort((a, b) => b.total - a.total);
    $('#report-categories').innerHTML = expenses.slice(0, 7).map((category) => `<div class="rank-row"><span>${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>${totals.expense ? (category.total / totals.expense * 100).toFixed(1).replace('.', ',') : 0}% das despesas</small></div><b>${brl.format(category.total)}</b></div>`).join('') || emptyState('⌁', 'Sem despesas', 'Registre saídas para gerar a análise.');

    $('#report-pro-lock').hidden = hasPro();
    $('#report-pro-details').hidden = !hasPro();
    $('#report-pro-lock [data-view="billing"]')?.addEventListener('click', () => switchView('billing'));
    renderReportChart();
    if (!hasPro()) {
      charts.reportYear?.destroy();
      charts.reportYear = null;
      return;
    }

    const currentRows = monthTransactions();
    const expenseRows = currentRows.filter((row) => row.type === 'expense');
    const allRows = state.transactions;
    const pendingIncomeRows = allRows.filter((row) => row.status === 'pending' && row.type === 'income');
    const pendingExpenseRows = allRows.filter((row) => row.status === 'pending' && row.type === 'expense');
    const pendingIncome = pendingIncomeRows.reduce((sum, row) => sum + Number(row.amount), 0);
    const pendingExpense = pendingExpenseRows.reduce((sum, row) => sum + Number(row.amount), 0);
    const recurring = allRows.filter((row) => row.recurring && !row.recurrence_source_id);
    const recurringFactor = (row) => row.recurrence_interval === 'weekly' ? 52 / 12 : row.recurrence_interval === 'yearly' ? 1 / 12 : 1;
    const recurringIncome = recurring.filter((row) => row.type === 'income').reduce((sum, row) => sum + Number(row.amount) * recurringFactor(row), 0);
    const recurringExpense = recurring.filter((row) => row.type === 'expense').reduce((sum, row) => sum + Number(row.amount) * recurringFactor(row), 0);
    const biggestExpense = expenseRows.slice().sort((a, b) => Number(b.amount) - Number(a.amount))[0];
    const daysElapsed = Math.max(1, now.getDate());
    const averageDailyExpense = totals.expense / daysElapsed;
    const averageTicket = currentRows.length ? currentRows.reduce((sum, row) => sum + Number(row.amount), 0) / currentRows.length : 0;
    const yearSeries = monthSeries(12);
    const monthsWithExpense = yearSeries.filter((item) => item.expense > 0);
    const lastExpenseMonths = monthsWithExpense.slice(-3);
    const averageMonthlyExpense = lastExpenseMonths.length ? lastExpenseMonths.reduce((sum, item) => sum + item.expense, 0) / lastExpenseMonths.length : 0;
    const runway = averageMonthlyExpense > 0 ? totalBalance() / averageMonthlyExpense : null;
    const bestMonth = yearSeries.slice().sort((a, b) => b.net - a.net)[0];
    const worstMonth = yearSeries.slice().sort((a, b) => a.net - b.net)[0];
    const budgetRows = state.categories.filter((category) => category.type === 'expense' && Number(category.budget) > 0).map((category) => ({ ...category, spent: categorySpent(category.id), limit: Number(category.budget) })).sort((a, b) => (b.spent / b.limit) - (a.spent / a.limit));

    $('#report-comparison').innerHTML = [
      ['Receita vs. mês anterior', brl.format(totals.income - previous.income), deltaText(totals.income, previous.income)],
      ['Despesa vs. mês anterior', brl.format(totals.expense - previous.expense), deltaText(totals.expense, previous.expense)],
      ['Variação do resultado', brl.format(totals.net - previous.net), deltaText(totals.net, previous.net)],
      ['Saldo consolidado', brl.format(totalBalance()), runway === null ? 'sem base para estimativa' : `≈ ${runway.toFixed(1).replace('.', ',')} meses de despesas médias`]
    ].map(([label, value, detail]) => `<article><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong><small>${escapeHTML(detail)}</small></article>`).join('');

    $('#report-health').innerHTML = [
      ['Lançamentos realizados', String(currentRows.length), 'no mês atual'],
      ['Ticket médio', brl.format(averageTicket), 'média por lançamento'],
      ['Gasto médio diário', brl.format(averageDailyExpense), `em ${daysElapsed} dias do mês`],
      ['Maior saída', biggestExpense ? brl.format(Number(biggestExpense.amount)) : brl.format(0), biggestExpense?.description || 'sem saídas'],
      ['Melhor mês (12m)', brl.format(bestMonth?.net || 0), bestMonth?.label || '—'],
      ['Pior mês (12m)', brl.format(worstMonth?.net || 0), worstMonth?.label || '—']
    ].map(([label, value, detail]) => `<div class="metric-row"><div><span>${escapeHTML(label)}</span><small>${escapeHTML(detail)}</small></div><strong>${escapeHTML(value)}</strong></div>`).join('');

    $('#report-pending').innerHTML = [
      ['A receber', brl.format(pendingIncome), `${pendingIncomeRows.length} lançamentos`],
      ['A pagar', brl.format(pendingExpense), `${pendingExpenseRows.length} lançamentos`],
      ['Saldo pendente', brl.format(pendingIncome - pendingExpense), 'impacto líquido se tudo ocorrer']
    ].map(([label, value, detail]) => `<div class="metric-row"><div><span>${label}</span><small>${detail}</small></div><strong>${value}</strong></div>`).join('');

    $('#report-recurring').innerHTML = [
      ['Entradas recorrentes', brl.format(recurringIncome), 'equivalência mensal'],
      ['Saídas recorrentes', brl.format(recurringExpense), 'equivalência mensal'],
      ['Resultado recorrente', brl.format(recurringIncome - recurringExpense), `${recurring.length} compromissos cadastrados`]
    ].map(([label, value, detail]) => `<div class="metric-row"><div><span>${label}</span><small>${detail}</small></div><strong>${value}</strong></div>`).join('');

    const balances = state.accounts.filter((account) => !account.archived).map((account) => ({ ...account, balance: accountBalance(account.id) })).sort((a, b) => b.balance - a.balance);
    $('#report-accounts').innerHTML = balances.map((account) => `<div class="rank-row"><span>${escapeHTML(account.icon)}</span><div><strong>${escapeHTML(account.name)}</strong><small>${escapeHTML(accountTypeLabel(account.type))}</small></div><b>${brl.format(account.balance)}</b></div>`).join('') || emptyState('▣', 'Sem contas', 'Adicione uma conta para analisar a distribuição.');

    $('#report-budget-analysis').innerHTML = budgetRows.slice(0, 7).map((category) => {
      const percent = category.limit ? category.spent / category.limit * 100 : 0;
      return `<div class="rank-row"><span>${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>${percent.toFixed(1).replace('.', ',')}% do limite · ${brl.format(Math.max(0, category.limit - category.spent))} disponível</small></div><b class="${percent > 100 ? 'value-expense' : ''}">${brl.format(category.spent)}</b></div>`;
    }).join('') || emptyState('◉', 'Sem limites', 'Defina orçamentos para medir eficiência.');

    const biggestCategory = expenses[0];
    const budgetOver = budgetRows.filter((row) => row.spent > row.limit);
    const insights = [
      ['↘', 'Peso das despesas', totals.income ? `As saídas consomem ${(totals.expense / totals.income * 100).toFixed(1).replace('.', ',')}% das receitas deste mês.` : 'Não há receita suficiente no período para medir o peso das despesas.'],
      ['◎', 'Taxa de economia', totals.income ? `Você preservou ${totals.savingsRate.toFixed(1).replace('.', ',')}% do que entrou. A comparação com o mês anterior é de ${(totals.savingsRate - previous.savingsRate).toFixed(1).replace('.', ',')} p.p.` : 'Registre receitas para calcular sua taxa de economia.'],
      ['◈', 'Concentração de gastos', biggestCategory ? `${biggestCategory.name} representa ${(biggestCategory.total / Math.max(1, totals.expense) * 100).toFixed(1).replace('.', ',')}% das despesas do mês.` : 'Não há concentração de despesas calculável neste mês.'],
      ['◇', 'Pendências', `Há ${brl.format(pendingIncome)} a receber e ${brl.format(pendingExpense)} a pagar em lançamentos pendentes.`],
      ['↻', 'Base recorrente', `Seus compromissos recorrentes equivalem a ${brl.format(recurringExpense)} em saídas e ${brl.format(recurringIncome)} em entradas por mês.`],
      ['!', 'Orçamentos', budgetOver.length ? `${budgetOver.length} ${budgetOver.length === 1 ? 'categoria ultrapassou' : 'categorias ultrapassaram'} o limite neste mês.` : 'Nenhum orçamento com limite definido foi ultrapassado neste mês.']
    ];
    $('#insights-grid').innerHTML = insights.map(([icon, title, body]) => `<div class="insight"><span>${icon}</span><strong>${escapeHTML(title)}</strong><p>${escapeHTML(body)}</p></div>`).join('');
    renderYearReportChart(yearSeries);
  }

  function renderReportChart() {
    if (!window.Chart) return;
    const series = monthSeries(6);
    charts.report?.destroy();
    charts.report = new Chart($('#report-chart'), {
      type: 'line',
      data: { labels: series.map((item) => item.label), datasets: [{ label: 'Resultado', data: series.map((item) => item.net), borderColor: '#34d399', backgroundColor: 'rgba(52,211,153,.18)', fill: hasPro(), tension: .35, pointRadius: 3, borderWidth: 2 }] },
      options: { ...chartDefaults(), plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `Resultado: ${brl.format(context.raw)}` } } } }
    });
  }

  function renderYearReportChart(series) {
    if (!window.Chart || !$('#report-year-chart')) return;
    charts.reportYear?.destroy();
    charts.reportYear = new Chart($('#report-year-chart'), {
      type: 'bar',
      data: { labels: series.map((item) => item.label), datasets: [
        { label: 'Entradas', data: series.map((item) => item.income), backgroundColor: 'rgba(52,211,153,.72)', borderRadius: 5 },
        { label: 'Saídas', data: series.map((item) => item.expense), backgroundColor: 'rgba(230,91,103,.65)', borderRadius: 5 }
      ] },
      options: { ...chartDefaults(), plugins: { legend: { display: true, labels: { usePointStyle: true, boxWidth: 8 } }, tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${brl.format(context.raw)}` } } } }
    });
  }

'''
js = replace_between(js, reports_js_start, reports_js_end, reports_js)
app_js.write_text(js, encoding='utf-8')

# UI styles.
app_css = Path('salesboard/app/app.css')
css = app_css.read_text(encoding='utf-8')
marker = '/* SalesBoard product upgrade 2026-08 */'
if marker not in css:
    css += '''

/* SalesBoard product upgrade 2026-08 */
.google-auth-button{width:100%;height:46px;border:1px solid #d9e0e8;background:#fff;color:#253044;border-radius:10px;display:flex;align-items:center;justify-content:center;gap:10px;font-weight:750;margin:-12px 0 16px;box-shadow:0 2px 8px rgba(10,24,44,.03)}.google-auth-button:hover{background:#f8fafc;border-color:#cbd5e1}.google-g{width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-weight:900;color:#4285f4;background:#fff;border:1px solid #e5e7eb}.auth-divider{display:flex;align-items:center;gap:12px;color:#98a2b3;font-size:10px;margin:0 0 22px}.auth-divider:before,.auth-divider:after{content:"";height:1px;background:#e6ebf0;flex:1}.auth-divider span{white-space:nowrap}.oauth-terms{border:1px solid #dfe7ee;background:#f8fafc;padding:12px 14px;border-radius:10px;margin:18px 0}.report-section-title{display:flex;align-items:end;justify-content:space-between;gap:20px;margin:28px 0 14px}.report-section-title h2{font:800 22px var(--display);letter-spacing:-.03em;margin:0}.report-section-title small{color:var(--muted);font-size:10px}.report-comparison article{min-height:104px}.report-comparison article small{display:block;margin-top:6px;color:var(--muted);line-height:1.4}.report-deep-grid{margin-top:14px}.chart-box.tall{height:320px}.report-detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:14px 0}.metric-list{display:grid;gap:0}.metric-row{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:13px 0;border-bottom:1px solid var(--line)}.metric-row:last-child{border-bottom:0}.metric-row span{display:block;font-size:10px;font-weight:750;color:#344054}.metric-row small{display:block;color:var(--muted);font-size:9px;margin-top:4px}.metric-row strong{font:800 12px var(--display);text-align:right}.rank-list.compact .rank-row{padding:10px 0}.report-lock{margin:14px 0}.report-lock button{margin-left:auto}.value-expense{color:var(--red)!important}@media(max-width:900px){.report-detail-grid{grid-template-columns:1fr}.report-section-title{align-items:flex-start;flex-direction:column}.chart-box.tall{height:270px}}@media(max-width:600px){.google-auth-button{margin-top:-8px}.report-comparison{grid-template-columns:1fr 1fr}.metric-row{align-items:flex-start}}
'''
    app_css.write_text(css, encoding='utf-8')

# Repository schema mirrors production 3-day rules.
schema = Path('salesboard/supabase/schema.sql')
sql = schema.read_text(encoding='utf-8')
sql = sql.replace("default (now() + interval '7 days')", "default (now() + interval '3 days')")
sql = sql.replace('Trial users receive Pro capabilities for seven days.', 'Trial users receive Pro capabilities for three days from account creation.')
h_start = 'create or replace function public.handle_new_user()'
h_end = 'drop trigger if exists on_auth_user_created on auth.users;'
h_fn = '''create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  requested_plan text;
  accepted_at timestamptz;
begin
  requested_plan := lower(coalesce(new.raw_user_meta_data->>'selected_plan', 'pro'));
  if requested_plan not in ('essential','pro') then requested_plan := 'pro'; end if;
  begin
    accepted_at := nullif(new.raw_user_meta_data->>'terms_accepted_at','')::timestamptz;
  exception when others then accepted_at := null;
  end;
  insert into public.profiles (id, full_name, workspace_name, plan, subscription_status, trial_ends_at, terms_accepted_at, terms_version)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name',''), coalesce(nullif(new.raw_user_meta_data->>'workspace_name',''),'Meu espaço'), requested_plan, 'trialing', new.created_at + interval '3 days', accepted_at, nullif(new.raw_user_meta_data->>'terms_version',''))
  on conflict (id) do nothing;
  return new;
end;
$$;

revoke all on function public.handle_new_user() from public, anon, authenticated;

'''
sql = replace_between(sql, h_start, h_end, h_fn)
e_start = 'create or replace function public.enforce_financial_write()'
e_end = 'drop trigger if exists accounts_require_access on public.accounts;'
e_fn = '''create or replace function public.enforce_financial_write()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  entitlement text;
  target_user uuid;
  account_count integer;
begin
  target_user := new.user_id;
  entitlement := public.current_entitlement(target_user);
  if entitlement = 'none' then raise exception 'SUBSCRIPTION_REQUIRED' using errcode = 'P0001'; end if;
  if tg_table_name = 'accounts' and entitlement = 'essential' and new.archived = false then
    if tg_op = 'INSERT' or (tg_op = 'UPDATE' and old.archived = true) then
      select count(*) into account_count from public.accounts where user_id = target_user and archived = false;
      if account_count >= 3 then raise exception 'PLAN_LIMIT_ACCOUNTS' using errcode = 'P0001'; end if;
    end if;
  end if;
  if tg_table_name = 'goals' and entitlement = 'essential' then raise exception 'PLAN_REQUIRED_PRO' using errcode = 'P0001'; end if;
  if tg_table_name = 'transactions' and coalesce(new.recurring,false) and entitlement = 'essential' then raise exception 'PLAN_REQUIRED_PRO' using errcode = 'P0001'; end if;
  return new;
end;
$$;

revoke all on function public.enforce_financial_write() from public, anon, authenticated;

'''
sql = replace_between(sql, e_start, e_end, e_fn)
schema.write_text(sql, encoding='utf-8')

migration = Path('salesboard/supabase/004_three_day_trial.sql')
migration.write_text('''-- SalesBoard Finance v3 - 3-day Pro trial and stricter plan guards
-- Run after 003_recurring.sql.

alter table public.profiles alter column trial_ends_at set default (now() + interval '3 days');

update public.profiles p
set trial_ends_at = u.created_at + interval '3 days', updated_at = now()
from auth.users u
where p.id = u.id
  and p.subscription_status = 'trialing'
  and p.trial_ends_at is distinct from (u.created_at + interval '3 days');

-- The full function replacements are mirrored in schema.sql and were applied to production
-- by migration salesboard_three_day_trial_and_plan_limits.
''', encoding='utf-8')

readme = Path('salesboard/README.md')
r = readme.read_text(encoding='utf-8').replace('trial Pro de 7 dias sem cartão', 'trial Pro de 3 dias sem cartão')
if '- login com Google via Supabase Auth' not in r:
    r = r.replace('- cadastro e login reais via Supabase Auth;\n', '- cadastro e login reais via Supabase Auth;\n- login com Google via Supabase Auth (frontend pronto; requer credenciais Google no provedor);\n')
r = r.replace('- relatórios e insights;\n', '- relatórios essenciais no Essencial e relatórios avançados de 12 meses no Pro;\n')
readme.write_text(r, encoding='utf-8')

assert '3 dias grátis' in landing.read_text(encoding='utf-8')
assert 'google-auth-button' in app_html.read_text(encoding='utf-8')
assert 'report-year-chart' in app_html.read_text(encoding='utf-8')
assert "subscription_status: 'active'" in app_js.read_text(encoding='utf-8')
assert "interval '3 days'" in schema.read_text(encoding='utf-8')
