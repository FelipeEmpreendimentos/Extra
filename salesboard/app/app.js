(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
  const dateBR = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
  const shortDateBR = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short' });
  const params = new URLSearchParams(location.search);
  const demoMode = params.get('demo') === '1';
  const requestedPlan = ['essential', 'pro'].includes(params.get('plan')) ? params.get('plan') : 'pro';
  let billingCycle = params.get('billing') === 'annual' ? 'annual' : 'monthly';
  let supabaseClient = null;
  let publicConfig = null;
  let session = null;
  let currentView = 'dashboard';
  let transactionFilter = 'all';
  let categoryType = 'expense';
  let reportMonthKey = currentMonthKey();
  let transactionGoalPreset = null;
  let onboardingStep = 1;
  let editingTransactionId = null;
  let entityMode = null;
  let editingEntityId = null;
  let charts = {};
  let state = {
    user: null,
    profile: null,
    subscription: null,
    accounts: [],
    categories: [],
    accountCatalog: [],
    categoryCatalog: [],
    transactions: [],
    goals: []
  };

  const COLORS = ['#34d399', '#4f7de8', '#8b5cf6', '#f59e0b', '#e65b67', '#ec4899', '#06b6d4', '#84cc16'];

  function escapeHTML(value) {
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  }

  function parseMoney(value) {
    if (typeof value === 'number') return value;
    const text = String(value ?? '').trim().replace(/[^0-9,.-]/g, '');
    if (!text) return 0;
    const normalized = text.includes(',') ? text.replace(/\./g, '').replace(',', '.') : text;
    const parsed = Number(normalized);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function isoDate(date = new Date()) {
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return local.toISOString().slice(0, 10);
  }

  function monthKey(dateValue) {
    const date = new Date(`${dateValue}T12:00:00`);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
  }

  function currentMonthKey() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  }

  function initials(name) {
    return String(name || 'SB').split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'SB';
  }

  function showOnly(id) {
    ['boot-screen', 'setup-error', 'auth-screen', 'forgot-screen', 'recovery-screen', 'trial-plan-screen', 'onboarding-screen', 'paywall-screen', 'app-shell'].forEach((screenId) => {
      const element = document.getElementById(screenId);
      if (element) element.hidden = screenId !== id;
    });
  }

  function toast(title, message = '', type = 'success') {
    const stack = $('#toast-stack');
    if (!stack) return;
    const item = document.createElement('div');
    item.className = `toast ${type}`;
    item.innerHTML = `<span>${type === 'error' ? '!' : '✓'}</span><div><strong>${escapeHTML(title)}</strong>${message ? `<p>${escapeHTML(message)}</p>` : ''}</div><button aria-label="Fechar">×</button>`;
    item.querySelector('button').addEventListener('click', () => item.remove());
    stack.appendChild(item);
    setTimeout(() => item.remove(), 4800);
  }

  let confirmationState = null;

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

  function setAuthMessage(message, error = false) {
    const box = $('#auth-message');
    if (!message) {
      box.hidden = true;
      box.textContent = '';
      return;
    }
    box.hidden = false;
    box.classList.toggle('error', error);
    box.textContent = message;
  }

  function setButtonLoading(button, loading, label) {
    if (!button) return;
    if (loading) {
      button.dataset.originalText = button.textContent;
      button.disabled = true;
      button.textContent = label || 'Aguarde...';
    } else {
      button.disabled = false;
      button.textContent = button.dataset.originalText || button.textContent;
      delete button.dataset.originalText;
    }
  }

  function appBaseUrl(query = '') {
    const url = new URL('./', location.href);
    url.search = query ? (query.startsWith('?') ? query : `?${query}`) : '';
    url.hash = '';
    return url.href;
  }

  function authErrorMessage(error) {
    const code = String(error?.code || '').toLowerCase();
    const message = String(error?.message || error || '').toLowerCase();
    if (code === 'email_not_confirmed' || message.includes('email not confirmed')) return 'Seu e-mail ainda não foi confirmado. Abra o e-mail enviado pelo SalesBoard e confirme sua conta antes de entrar.';
    if (code === 'invalid_credentials' || message.includes('invalid login credentials')) return 'E-mail ou senha incorretos. Confira os dados e tente novamente.';
    if (code === 'over_email_send_rate_limit' || message.includes('after 45 seconds') || message.includes('rate limit')) return 'Aguarde alguns segundos antes de pedir outro e-mail. Isso protege sua conta contra abuso.';
    if (message.includes('provider is not enabled')) return 'O login com Google ainda não foi ativado no servidor. Use e-mail e senha por enquanto.';
    if (code === 'user_already_exists' || message.includes('already registered') || message.includes('already exists')) return 'Já existe uma conta com este e-mail. Entre normalmente ou use “Esqueci a senha”.';
    if (message.includes('password should be')) return 'A senha não atende aos requisitos de segurança. Use pelo menos 8 caracteres.';
    return friendlyError(error);
  }

  function setInlineMessage(selector, message, error = false) {
    const box = $(selector);
    if (!box) return;
    box.hidden = !message;
    box.textContent = message || '';
    box.classList.toggle('error', Boolean(error));
  }

  async function waitForBillingSync(attempts = 8) {
    if (demoMode || !supabaseClient || !state.user) return;
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      const { data } = await supabaseClient.from('profiles').select('*').eq('id', state.user.id).maybeSingle();
      if (data) state.profile = data;
      if (data?.subscription_status === 'active') return;
      await new Promise((resolve) => setTimeout(resolve, 750));
    }
  }

  function profileEntitlement() {
    if (demoMode) return 'pro';
    const profile = state.profile;
    if (!profile) return 'none';
    if (profile.subscription_status === 'active') return profile.plan === 'essential' ? 'essential' : 'pro';
    if (profile.subscription_status === 'trialing' && new Date(profile.trial_ends_at).getTime() > Date.now()) return profile.plan === 'essential' ? 'essential' : 'pro';
    return 'none';
  }

  function hasPro() {
    return profileEntitlement() === 'pro';
  }

  function isPaid() {
    return state.profile?.subscription_status === 'active';
  }

  function allCategories() {
    return state.categoryCatalog?.length ? state.categoryCatalog : state.categories;
  }

  function allAccounts() {
    return state.accountCatalog?.length ? state.accountCatalog : state.accounts;
  }

  function categoryById(id) {
    return allCategories().find((item) => item.id === id) || { name: 'Categoria indisponível', icon: '•', color: '#94a3b8' };
  }

  function accountById(id) {
    return allAccounts().find((item) => item.id === id) || { name: 'Conta indisponível', icon: '▣' };
  }

  function goalById(id) {
    return state.goals.find((item) => item.id === id) || null;
  }

  function goalProgress(goal) {
    const base = Math.max(0, Number(goal?.current_amount || 0));
    const linked = paidTransactions().filter((row) => row.type === 'income' && row.goal_id === goal?.id).reduce((sum, row) => sum + Number(row.goal_amount || row.amount), 0);
    return base + linked;
  }

  function paidTransactions() {
    return state.transactions.filter((item) => item.status === 'paid');
  }

  function monthTransactions(key = currentMonthKey()) {
    return paidTransactions().filter((item) => monthKey(item.transaction_date) === key);
  }

  function totalsForMonth(key = currentMonthKey()) {
    const rows = monthTransactions(key);
    const income = rows.filter((row) => row.type === 'income').reduce((sum, row) => sum + Number(row.amount), 0);
    const expense = rows.filter((row) => row.type === 'expense').reduce((sum, row) => sum + Number(row.amount), 0);
    return { income, expense, net: income - expense, savingsRate: income > 0 ? ((income - expense) / income) * 100 : 0 };
  }

  function accountBalance(accountId) {
    const account = accountById(accountId);
    const delta = paidTransactions().filter((row) => row.account_id === accountId).reduce((sum, row) => sum + (row.type === 'income' ? Number(row.amount) : -Number(row.amount)), 0);
    return Number(account.opening_balance || 0) + delta;
  }

  function totalBalance() {
    return state.accounts.filter((account) => !account.archived).reduce((sum, account) => sum + accountBalance(account.id), 0);
  }

  function categorySpent(categoryId, key = currentMonthKey()) {
    return monthTransactions(key).filter((row) => row.type === 'expense' && row.category_id === categoryId).reduce((sum, row) => sum + Number(row.amount), 0);
  }

  function monthSeries(count = 6, endKey = currentMonthKey()) {
    const [anchorYear, anchorMonth] = String(endKey).split('-').map(Number);
    const anchor = new Date(anchorYear, anchorMonth - 1, 1);
    const output = [];
    for (let index = count - 1; index >= 0; index -= 1) {
      const date = new Date(anchor.getFullYear(), anchor.getMonth() - index, 1);
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const total = totalsForMonth(key);
      output.push({ key, label: new Intl.DateTimeFormat('pt-BR', { month: 'short' }).format(date).replace('.', ''), ...total });
    }
    return output;
  }

  function friendlyError(error) {
    const message = String(error?.message || error || 'Erro inesperado.');
    if (message.includes('PLAN_LIMIT_ACCOUNTS')) return 'O plano Essencial permite até 3 contas. Faça upgrade para o Pro para adicionar mais.';
    if (message.includes('PLAN_REQUIRED_PRO')) return 'Este recurso faz parte do plano Pro.';
    if (message.includes('SUBSCRIPTION_REQUIRED')) return 'Seu período de acesso terminou. Escolha um plano para continuar.';
    if (message.includes('TRIAL_ALREADY_USED')) return 'Este e-mail já utilizou o período de experiência. Escolha um plano para continuar.';
    if (message.includes('TRIAL_ALREADY_STARTED')) return 'Seu período de experiência já foi iniciado em outro plano e não pode ser reiniciado.';
    if (message.includes('INVALID_TRIAL_PLAN')) return 'Não foi possível identificar o plano escolhido. Atualize a página e tente novamente.';
    if (message.includes('duplicate key') || error?.code === '23505') return 'Já existe um item com essas informações.';
    if (message.includes('INVALID_GOAL_AMOUNT')) return 'O valor destinado à meta precisa ser maior que zero e não pode ultrapassar o valor da entrada.';
    if (message.includes('GOAL_REQUIRES_INCOME')) return 'Metas podem ser vinculadas apenas a entradas. Para dinheiro que você já tinha guardado, use o valor já acumulado da meta.';
    if (message.includes('INVALID_GOAL_REFERENCE')) return 'A meta vinculada não existe mais ou não pertence a esta conta.';
    if (message.includes('CATEGORY_TYPE_MISMATCH')) return 'A categoria escolhida não combina com o tipo do lançamento.';
    if (message.includes('foreign key')) return 'Este item está sendo usado em lançamentos e não pode ser excluído agora.';
    return message.length > 180 ? 'Não foi possível concluir a operação. Tente novamente.' : message;
  }

  async function fetchConfig() {
    try {
      const response = await fetch('/api/config', { headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error('Configuração pública indisponível.');
      return await response.json();
    } catch (error) {
      return { configured: false, missing: ['SUPABASE_URL', 'SUPABASE_PUBLISHABLE_KEY'], error: error.message };
    }
  }

  async function initialize() {
    initStaticEvents();
    if (demoMode) {
      initDemo();
      return;
    }

    publicConfig = await fetchConfig();
    if (!publicConfig.configured || !window.supabase?.createClient) {
      $('#setup-missing').innerHTML = (publicConfig.missing || []).map((item) => `<code>${escapeHTML(item)}</code>`).join('');
      showOnly('setup-error');
      return;
    }

    supabaseClient = window.supabase.createClient(publicConfig.supabaseUrl, publicConfig.supabasePublishableKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
    });

    supabaseClient.auth.onAuthStateChange((event, nextSession) => {
      session = nextSession;
      if (event === 'PASSWORD_RECOVERY') showOnly('recovery-screen');
    });

    const { data, error } = await supabaseClient.auth.getSession();
    if (error) console.error(error);
    session = data?.session || null;

    if (params.get('recovery') === '1' && session) {
      showOnly('recovery-screen');
      return;
    }

    if (!session) {
      showAuth(params.get('mode') === 'register' ? 'register' : 'login');
      return;
    }

    await initializeAuthenticatedUser();
  }

  function showAuth(mode = 'login') {
    showOnly('auth-screen');
    setAuthMode(mode);
  }

  function setAuthMode(mode) {
    const login = mode !== 'register';
    $$('[data-auth-mode]').forEach((button) => button.classList.toggle('active', button.dataset.authMode === (login ? 'login' : 'register')));
    $('#auth-login-pane').hidden = !login;
    $('#auth-register-pane').hidden = login;
    setAuthMessage('');
  }

  async function trialEligible() {
    if (demoMode || !supabaseClient) return false;
    const { data, error } = await supabaseClient.rpc('salesboard_trial_eligible');
    if (error) throw error;
    return data === true;
  }

  function renderTrialPlanScreen() {
    $$('[data-trial-card]').forEach((card) => {
      const preferred = card.dataset.trialCard === requestedPlan;
      card.classList.toggle('preferred', preferred);
    });
  }

  async function startTrial(plan, button) {
    if (!['essential', 'pro'].includes(plan) || demoMode) return;
    const buttons = $$('[data-start-trial]');
    buttons.forEach((item) => { item.disabled = true; });
    setButtonLoading(button, true, 'Preparando seu acesso...');
    try {
      const { error } = await supabaseClient.rpc('start_salesboard_trial', { p_plan: plan });
      if (error) throw error;
      const { data: profile, error: profileError } = await supabaseClient.from('profiles').select('*').eq('id', state.user.id).single();
      if (profileError) throw profileError;
      state.profile = profile;
      if (state.profile.onboarded) {
        await loadFinancialData();
        enterApp();
      } else {
        setupOnboarding();
        showOnly('onboarding-screen');
      }
      toast(`Plano ${plan === 'essential' ? 'Essencial' : 'Pro'} liberado`, 'Seus 3 dias começaram agora. Aproveite para configurar seu espaço e testar os recursos do plano.');
    } catch (error) {
      if (String(error?.message || '').includes('TRIAL_ALREADY_USED')) {
        const { data: profile } = await supabaseClient.from('profiles').select('*').eq('id', state.user.id).single();
        if (profile) state.profile = profile;
        renderPaywallExperience();
        showOnly('paywall-screen');
      } else {
        toast('Não foi possível iniciar sua experiência', friendlyError(error), 'error');
      }
    } finally {
      buttons.forEach((item) => { item.disabled = false; });
      setButtonLoading(button, false);
    }
  }

  function renderPaywallExperience() {
    const testedPlan = state.profile?.plan === 'essential' ? 'Essencial' : 'Pro';
    const onboarded = Boolean(state.profile?.onboarded);
    const title = $('#paywall-title');
    const copy = $('#paywall-copy');
    const tested = $('#paywall-tested-plan');
    const kicker = $('#paywall-kicker');
    const exportButton = $('#paywall-export');

    if (tested) tested.textContent = testedPlan;
    if (exportButton) exportButton.hidden = !onboarded;
    if (onboarded) {
      if (kicker) kicker.textContent = 'Seu espaço continua aqui';
      if (title) title.textContent = 'Continue com a visão financeira que você construiu.';
      if (copy) copy.textContent = `Seu período no ${testedPlan} foi concluído, mas seu espaço, histórico e configurações permanecem preservados. Escolha como quer continuar e retome exatamente de onde parou.`;
    } else {
      if (kicker) kicker.textContent = 'Pronto para começar';
      if (title) title.textContent = 'Escolha o plano que acompanha sua rotina.';
      if (copy) copy.textContent = 'Este e-mail já utilizou a experiência inicial do SalesBoard. Ative um plano para criar seu espaço financeiro e começar com todos os recursos da opção escolhida.';
    }

    $$('[data-paywall-card]').forEach((card) => {
      const isTested = card.dataset.paywallCard === state.profile?.plan;
      card.classList.toggle('featured', isTested);
      const button = card.querySelector('[data-paywall-plan]');
      if (button) {
        button.classList.toggle('primary', isTested);
        button.classList.toggle('outline', !isTested);
        button.textContent = isTested ? `Continuar com ${testedPlan}` : `Escolher ${card.dataset.paywallCard === 'essential' ? 'Essencial' : 'Pro'}`;
      }
    });
  }

  async function initializeAuthenticatedUser() {
    showOnly('boot-screen');
    state.user = session.user;
    const { data: profile, error } = await supabaseClient.from('profiles').select('*').eq('id', session.user.id).single();
    if (error || !profile) {
      console.error(error);
      $('#setup-missing').innerHTML = '<code>Execute supabase/schema.sql no projeto Supabase</code>';
      showOnly('setup-error');
      return;
    }
    state.profile = profile;

    if (params.get('checkout') === 'success') await waitForBillingSync();

    const trialActive = state.profile.subscription_status === 'trialing' && new Date(state.profile.trial_ends_at).getTime() > Date.now();
    const canUseProduct = state.profile.subscription_status === 'active' || trialActive;

    if (!state.profile.onboarded) {
      if (canUseProduct) {
        setupOnboarding();
        showOnly('onboarding-screen');
        return;
      }

      const eligible = await trialEligible();
      if (eligible) {
        renderTrialPlanScreen();
        showOnly('trial-plan-screen');
        return;
      }

      renderPaywallExperience();
      showOnly('paywall-screen');
      return;
    }

    await loadFinancialData();
    const entitlement = profileEntitlement();
    if (entitlement === 'none') {
      renderIdentity();
      renderPaywallExperience();
      showOnly('paywall-screen');
      return;
    }

    enterApp();
  }

  async function loadFinancialData() {
    if (demoMode) return;
    const userId = state.user.id;
    const [accounts, categories, transactions, goals, subscription] = await Promise.all([
      supabaseClient.from('accounts').select('*').eq('user_id', userId).order('created_at'),
      supabaseClient.from('categories').select('*').eq('user_id', userId).order('type').order('name'),
      supabaseClient.from('transactions').select('*').eq('user_id', userId).order('transaction_date', { ascending: false }).order('created_at', { ascending: false }),
      supabaseClient.from('goals').select('*').eq('user_id', userId).order('created_at'),
      supabaseClient.from('subscriptions').select('*').eq('user_id', userId).maybeSingle()
    ]);
    const firstError = [accounts, categories, transactions, goals, subscription].find((result) => result.error)?.error;
    if (firstError) throw firstError;
    state.accountCatalog = accounts.data || [];
    state.categoryCatalog = categories.data || [];
    state.accounts = state.accountCatalog.filter((row) => !row.archived);
    state.categories = state.categoryCatalog.filter((row) => !row.archived);
    state.transactions = transactions.data || [];
    state.goals = goals.data || [];
    state.subscription = subscription.data || null;
  }

  function demoDate(daysAgo) {
    const date = new Date();
    date.setDate(date.getDate() - daysAgo);
    return isoDate(date);
  }

  function initDemo() {
    const now = new Date();
    const trialEnd = new Date(now.getTime() + 3 * 86400000).toISOString();
    state.user = { id: 'demo-user', email: 'demo@salesboard.finance' };
    state.profile = { id: 'demo-user', full_name: 'Conta demonstração', workspace_name: 'Demonstração Pro', workspace_type: 'business', plan: 'pro', subscription_status: 'active', trial_ends_at: trialEnd, onboarded: true, currency: 'BRL', terms_accepted_at: new Date().toISOString() };
    state.accounts = [
      { id: 'a1', name: 'Conta principal', type: 'bank', opening_balance: 5200, icon: '◈', color: '#8b5cf6' },
      { id: 'a2', name: 'Carteira digital', type: 'wallet', opening_balance: 1350, icon: '◆', color: '#34d399' },
      { id: 'a3', name: 'Investimentos', type: 'investment', opening_balance: 3900, icon: '↗', color: '#4f7de8' }
    ];
    state.categories = [
      { id: 'c1', name: 'Trabalho', type: 'income', icon: '💼', color: '#34d399', budget: 0 },
      { id: 'c2', name: 'Outras entradas', type: 'income', icon: '💰', color: '#4f7de8', budget: 0 },
      { id: 'c3', name: 'Moradia', type: 'expense', icon: '🏠', color: '#8b5cf6', budget: 1600 },
      { id: 'c4', name: 'Alimentação', type: 'expense', icon: '🛒', color: '#34d399', budget: 1100 },
      { id: 'c5', name: 'Transporte', type: 'expense', icon: '🚗', color: '#4f7de8', budget: 700 },
      { id: 'c6', name: 'Serviços', type: 'expense', icon: '💡', color: '#f59e0b', budget: 500 },
      { id: 'c7', name: 'Lazer', type: 'expense', icon: '🎮', color: '#e65b67', budget: 450 }
    ];
    state.transactions = [
      { id: 't1', description: 'Projeto freelancer', type: 'income', amount: 2800, transaction_date: demoDate(1), status: 'paid', recurring: false, account_id: 'a1', category_id: 'c1' },
      { id: 't2', description: 'Supermercado', type: 'expense', amount: 486.72, transaction_date: demoDate(2), status: 'paid', recurring: false, account_id: 'a2', category_id: 'c4' },
      { id: 't3', description: 'Aluguel', type: 'expense', amount: 1250, transaction_date: demoDate(4), status: 'paid', recurring: true, recurrence_interval: 'monthly', account_id: 'a1', category_id: 'c3' },
      { id: 't4', description: 'Cliente recorrente', type: 'income', amount: 1920, transaction_date: demoDate(5), status: 'paid', recurring: false, account_id: 'a1', category_id: 'c1' },
      { id: 't5', description: 'Combustível', type: 'expense', amount: 238.4, transaction_date: demoDate(6), status: 'paid', recurring: false, account_id: 'a2', category_id: 'c5' },
      { id: 't6', description: 'Ferramentas online', type: 'expense', amount: 174.9, transaction_date: demoDate(7), status: 'paid', recurring: true, recurrence_interval: 'monthly', account_id: 'a1', category_id: 'c6' },
      { id: 't7', description: 'Restaurante', type: 'expense', amount: 162.8, transaction_date: demoDate(8), status: 'paid', recurring: false, account_id: 'a2', category_id: 'c4' }
    ];
    for (let monthOffset = 1; monthOffset <= 11; monthOffset += 1) {
      const date = new Date(now.getFullYear(), now.getMonth() - monthOffset, 12);
      state.transactions.push({ id: `hist-in-${monthOffset}`, description: 'Receitas do período', type: 'income', amount: 5800 + monthOffset * 420, transaction_date: isoDate(date), status: 'paid', recurring: false, account_id: 'a1', category_id: 'c1' });
      state.transactions.push({ id: `hist-out-${monthOffset}`, description: 'Despesas do período', type: 'expense', amount: 3300 + monthOffset * 160, transaction_date: isoDate(new Date(date.getFullYear(), date.getMonth(), 18)), status: 'paid', recurring: false, account_id: 'a1', category_id: 'c3' });
    }
    state.goals = [
      { id: 'g1', name: 'Reserva de emergência', icon: '🛡️', target_amount: 10000, current_amount: 7200, due_date: isoDate(new Date(now.getFullYear(), now.getMonth() + 5, 28)) },
      { id: 'g2', name: 'Notebook novo', icon: '💻', target_amount: 7000, current_amount: 3100, due_date: isoDate(new Date(now.getFullYear() + 1, 0, 31)) }
    ];
    state.subscription = { plan: 'pro', status: 'active', billing_cycle: 'annual', cancel_at_period_end: false, current_period_end: new Date(now.getFullYear() + 1, now.getMonth(), now.getDate()).toISOString() };
    state.accountCatalog = [...state.accounts];
    state.categoryCatalog = [...state.categories];
    enterApp();
    $('#demo-badge').hidden = false;
    toast('Modo demonstração', 'Os dados desta tela são fictícios e não são enviados para um servidor.');
  }

  function enterApp() {
    showOnly('app-shell');
    renderIdentity();
    renderAll();
    switchView(currentView);
    const checkout = params.get('checkout');
    if (checkout === 'success') toast('Checkout concluído', 'A assinatura será liberada assim que o Stripe confirmar o evento.');
    if (checkout === 'cancelled') toast('Checkout cancelado', 'Nenhuma cobrança foi concluída.', 'error');
  }

  function renderIdentity() {
    const name = state.profile?.full_name || state.user?.email?.split('@')[0] || 'Usuário';
    const workspace = state.profile?.workspace_name || 'Meu espaço';
    const init = initials(name);
    $('#workspace-label').textContent = workspace;
    $('#workspace-avatar').textContent = initials(workspace);
    $('#user-name').textContent = name;
    $('#user-email').textContent = state.user?.email || '';
    $('#user-initials').textContent = init;
    $('#hello-title').textContent = `Olá, ${name.split(' ')[0]} 👋`;
    $('#today-label').textContent = new Intl.DateTimeFormat('pt-BR', { weekday: 'long', day: '2-digit', month: 'long' }).format(new Date());
    $('#settings-name').value = name;
    $('#settings-workspace').value = workspace;
    renderTrialCard();
  }

  function renderTrialCard() {
    const card = $('#trial-card');
    if (!card) return;
    const planName = state.profile?.plan === 'essential' ? 'Essencial' : 'Pro';
    if (isPaid()) {
      card.hidden = false;
      card.innerHTML = `<span>PLANO ATIVO</span><strong>${planName}</strong><p>Sua assinatura está ativa.</p><button data-view="billing">Gerenciar plano →</button>`;
      card.querySelector('button').addEventListener('click', () => switchView('billing'));
      return;
    }
    if (state.profile?.subscription_status === 'trialing' && new Date(state.profile.trial_ends_at).getTime() > Date.now()) {
      card.hidden = false;
      const remaining = Math.max(0, Math.ceil((new Date(state.profile.trial_ends_at).getTime() - Date.now()) / 86400000));
      card.innerHTML = `<span>EXPERIÊNCIA ${planName.toUpperCase()}</span><strong>${remaining} ${remaining === 1 ? 'dia restante' : 'dias restantes'}</strong><p>Você está usando os recursos do plano ${planName}.</p><button data-view="billing">Ver plano →</button>`;
      card.querySelector('button').addEventListener('click', () => switchView('billing'));
      return;
    }
    card.hidden = true;
  }

  function renderAll() {
    renderSummary();
    renderTransactions();
    renderAccounts();
    renderCategories();
    renderBudgets();
    renderGoals();
    renderReports();
    renderBilling();
    renderSelectOptions();
    renderFeatureLocks();
  }

  function renderSummary() {
    const totals = totalsForMonth();
    const balance = totalBalance();
    const pending = state.transactions.filter((row) => row.status === 'pending').reduce((sum, row) => sum + (row.type === 'income' ? Number(row.amount) : -Number(row.amount)), 0);
    const cards = [
      ['Saldo atual', brl.format(balance), `${state.accounts.length} ${state.accounts.length === 1 ? 'conta ativa' : 'contas ativas'}`, ''],
      ['Entradas do mês', brl.format(totals.income), `${monthTransactions().filter((row) => row.type === 'income').length} recebimentos`, 'good'],
      ['Saídas do mês', brl.format(totals.expense), totals.income ? `${(totals.expense / totals.income * 100).toFixed(1).replace('.', ',')}% da receita` : 'Sem receita registrada', 'bad'],
      ['Resultado', brl.format(totals.net), pending ? `${brl.format(Math.abs(pending))} em pendências líquidas` : `${Math.max(0, totals.savingsRate).toFixed(1).replace('.', ',')}% de economia`, totals.net >= 0 ? 'good' : 'bad']
    ];
    $('#summary-grid').innerHTML = cards.map(([label, value, detail, cls]) => `<article class="summary-card"><span>${label}</span><strong>${value}</strong><small class="${cls}">${escapeHTML(detail)}</small></article>`).join('');
    renderRecentTransactions();
    renderBudgetPreview();
    renderDashboardCharts();
  }

  function renderRecentTransactions() {
    const rows = state.transactions.slice(0, 6);
    $('#recent-transactions').innerHTML = rows.length ? rows.map((row) => {
      const category = categoryById(row.category_id);
      return `<div class="transaction-row"><span class="transaction-icon">${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(row.description)}</strong><small>${escapeHTML(category.name)} · ${shortDateBR.format(new Date(`${row.transaction_date}T12:00:00`))}</small></div><b class="${row.type === 'income' ? 'value-income' : 'value-expense'}">${row.type === 'income' ? '+' : '−'} ${brl.format(Number(row.amount))}</b></div>`;
    }).join('') : emptyState('⇄', 'Nenhum lançamento ainda', 'Adicione sua primeira entrada ou saída.');
  }

  function renderBudgetPreview() {
    const budgets = state.categories.filter((category) => category.type === 'expense' && Number(category.budget) > 0).slice(0, 5);
    $('#budget-preview').innerHTML = budgets.length ? budgets.map((category) => {
      const spent = categorySpent(category.id);
      const budget = Number(category.budget);
      const percent = budget ? Math.min(100, spent / budget * 100) : 0;
      const cls = percent >= 95 ? 'danger' : percent >= 75 ? 'warning' : '';
      return `<div class="budget-item"><header><strong>${escapeHTML(category.icon)} ${escapeHTML(category.name)}</strong><span>${brl.format(spent)} / ${brl.format(budget)}</span></header><div class="progress"><i class="${cls}" style="width:${percent}%"></i></div></div>`;
    }).join('') : emptyState('◉', 'Sem limites definidos', 'Adicione um limite mensal em uma categoria de saída.');
  }

  function chartDefaults() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 450 },
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#8b96a5', font: { size: 9 } }, border: { display: false } },
        y: { grid: { color: '#eef1f4' }, ticks: { color: '#8b96a5', font: { size: 9 }, callback: (value) => `R$ ${Number(value / 1000).toFixed(0)}k` }, border: { display: false } }
      }
    };
  }

  function renderDashboardCharts() {
    if (!window.Chart) return;
    const series = monthSeries();
    charts.cashflow?.destroy();
    charts.cashflow = new Chart($('#cashflow-chart'), {
      type: 'bar',
      data: { labels: series.map((item) => item.label), datasets: [
        { label: 'Entradas', data: series.map((item) => item.income), backgroundColor: '#34d399', borderRadius: 6, borderSkipped: false },
        { label: 'Saídas', data: series.map((item) => item.expense), backgroundColor: '#71849b', borderRadius: 6, borderSkipped: false }
      ] },
      options: { ...chartDefaults(), plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${brl.format(context.raw)}` } } } }
    });

    const categories = allCategories().filter((category) => category.type === 'expense').map((category) => ({ ...category, total: categorySpent(category.id) })).filter((category) => category.total > 0).sort((a, b) => b.total - a.total);
    charts.category?.destroy();
    charts.category = new Chart($('#category-chart'), {
      type: 'doughnut',
      data: { labels: categories.map((item) => item.name), datasets: [{ data: categories.map((item) => item.total), backgroundColor: categories.map((item) => item.color || COLORS[0]), borderWidth: 0, hoverOffset: 4 }] },
      options: { responsive: true, maintainAspectRatio: false, cutout: '72%', plugins: { legend: { display: false }, tooltip: { callbacks: { label: (context) => `${context.label}: ${brl.format(context.raw)}` } } } }
    });
    const totalExpense = categories.reduce((sum, item) => sum + item.total, 0);
    $('#donut-total').textContent = brl.format(totalExpense);
    $('#category-legend').innerHTML = categories.slice(0, 6).map((item) => `<div class="legend-row"><i style="background:${item.color}"></i><span>${escapeHTML(item.name)}</span><strong>${brl.format(item.total)}</strong></div>`).join('') || '<small style="color:#8a96a5">Sem despesas no mês.</small>';
  }

  function renderTransactions() {
    const query = ($('#transaction-search')?.value || '').trim().toLowerCase();
    let rows = [...state.transactions];
    if (transactionFilter !== 'all') rows = rows.filter((row) => row.type === transactionFilter);
    if (query) rows = rows.filter((row) => `${row.description} ${categoryById(row.category_id).name} ${accountById(row.account_id).name} ${goalById(row.goal_id)?.name || ''}`.toLowerCase().includes(query));
    $('#transactions-empty').hidden = rows.length > 0;
    $('#transactions-body').innerHTML = rows.map((row) => {
      const category = categoryById(row.category_id);
      const account = accountById(row.account_id);
      const goal = row.goal_id ? goalById(row.goal_id) : null;
      const details = [row.recurring ? 'Recorrente' : '', goal ? `Meta: ${goal.icon} ${goal.name} (${brl.format(Number(row.goal_amount || row.amount))})` : ''].filter(Boolean).join(' · ');
      return `<tr><td><strong>${escapeHTML(row.description)}</strong>${details ? `<br><small>${escapeHTML(details)}</small>` : ''}</td><td><span class="category-pill">${escapeHTML(category.icon)} ${escapeHTML(category.name)}</span></td><td>${escapeHTML(account.name)}</td><td>${dateBR.format(new Date(`${row.transaction_date}T12:00:00`))}</td><td><span class="status-pill ${row.status === 'pending' ? 'pending' : ''}">${row.status === 'pending' ? 'Pendente' : 'Pago'}</span></td><td class="right ${row.type === 'income' ? 'value-income' : 'value-expense'}"><strong>${row.type === 'income' ? '+' : '−'} ${brl.format(Number(row.amount))}</strong></td><td><div class="table-actions"><button class="row-button" data-edit-transaction="${row.id}" title="Editar">✎</button><button class="row-button" data-delete-transaction="${row.id}" title="Excluir">×</button></div></td></tr>`;
    }).join('');
    $$('[data-edit-transaction]').forEach((button) => button.addEventListener('click', () => openTransactionModal(button.dataset.editTransaction)));
    $$('[data-delete-transaction]').forEach((button) => button.addEventListener('click', () => deleteTransaction(button.dataset.deleteTransaction)));
  }

  function renderAccounts() {
    const balances = state.accounts.map((account) => accountBalance(account.id));
    const total = balances.reduce((sum, value) => sum + value, 0);
    const investments = state.accounts.filter((account) => account.type === 'investment').reduce((sum, account) => sum + accountBalance(account.id), 0);
    $('#accounts-summary').innerHTML = `<article><span>Saldo consolidado</span><strong>${brl.format(total)}</strong></article><article><span>Contas ativas</span><strong>${state.accounts.length}</strong></article><article><span>Investimentos</span><strong>${brl.format(investments)}</strong></article>`;
    $('#accounts-grid').innerHTML = state.accounts.length ? state.accounts.map((account) => `<article class="entity-card"><div class="entity-head"><div class="entity-title"><span class="entity-icon" style="background:${account.color}18;color:${account.color}">${escapeHTML(account.icon)}</span><div><strong>${escapeHTML(account.name)}</strong><small>${accountTypeLabel(account.type)}</small></div></div><div><button class="entity-menu" data-edit-account="${account.id}">✎</button><button class="entity-menu" data-delete-account-row="${account.id}">×</button></div></div><strong class="entity-value">${brl.format(accountBalance(account.id))}</strong><small>Saldo atual · inicial ${brl.format(Number(account.opening_balance || 0))}</small></article>`).join('') : emptyState('▣', 'Nenhuma conta', 'Adicione uma conta para começar.');
    $$('[data-edit-account]').forEach((button) => button.addEventListener('click', () => openEntityModal('account', button.dataset.editAccount)));
    $$('[data-delete-account-row]').forEach((button) => button.addEventListener('click', () => deleteEntity('account', button.dataset.deleteAccountRow)));
  }

  function accountTypeLabel(type) {
    return ({ bank: 'Conta bancária', cash: 'Dinheiro', wallet: 'Carteira digital', investment: 'Investimento' })[type] || 'Conta';
  }

  function renderCategories() {
    $$('.category-tabs [data-category-type]').forEach((button) => button.classList.toggle('active', button.dataset.categoryType === categoryType));
    const rows = state.categories.filter((category) => category.type === categoryType);
    $('#categories-grid').innerHTML = rows.length ? rows.map((category) => {
      const total = category.type === 'expense' ? categorySpent(category.id) : monthTransactions().filter((row) => row.type === 'income' && row.category_id === category.id).reduce((sum, row) => sum + Number(row.amount), 0);
      const budget = Number(category.budget || 0);
      const percent = category.type === 'expense' && budget ? Math.min(100, total / budget * 100) : 0;
      return `<article class="entity-card"><div class="entity-head"><div class="entity-title"><span class="entity-icon" style="background:${category.color}18;color:${category.color}">${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>${category.type === 'expense' ? 'Saída' : 'Entrada'}</small></div></div><div><button class="entity-menu" data-edit-category="${category.id}">✎</button><button class="entity-menu" data-delete-category-row="${category.id}">×</button></div></div><strong class="entity-value">${brl.format(total)}</strong><small>${category.type === 'expense' && budget ? `Limite ${brl.format(budget)}` : 'Total no mês'}</small>${category.type === 'expense' && budget ? `<div class="progress"><i style="width:${percent}%;background:${category.color}"></i></div>` : ''}</article>`;
    }).join('') : emptyState('◫', 'Nenhuma categoria', 'Crie uma categoria personalizada.');
    $$('[data-edit-category]').forEach((button) => button.addEventListener('click', () => openEntityModal('category', button.dataset.editCategory)));
    $$('[data-delete-category-row]').forEach((button) => button.addEventListener('click', () => deleteEntity('category', button.dataset.deleteCategoryRow)));
  }

  function renderBudgets() {
    const rows = state.categories.filter((category) => category.type === 'expense' && Number(category.budget) > 0);
    const budgetTotal = rows.reduce((sum, category) => sum + Number(category.budget), 0);
    const spentTotal = rows.reduce((sum, category) => sum + categorySpent(category.id), 0);
    const budgetRoom = budgetTotal - spentTotal;
    $('#budget-summary').innerHTML = `<article><span>Limite planejado</span><strong>${brl.format(budgetTotal)}</strong></article><article><span>Gasto até agora</span><strong>${brl.format(spentTotal)}</strong></article><article><span>${budgetRoom >= 0 ? 'Disponível' : 'Acima do limite'}</span><strong class="${budgetRoom < 0 ? 'value-expense' : ''}">${brl.format(Math.abs(budgetRoom))}</strong></article>`;
    $('#budgets-grid').innerHTML = rows.length ? rows.map((category) => {
      const spent = categorySpent(category.id);
      const budget = Number(category.budget);
      const percent = spent / budget * 100;
      const barPercent = Math.min(100, percent);
      const cls = percent >= 95 ? 'danger' : percent >= 75 ? 'warning' : '';
      const room = budget - spent;
      return `<article class="entity-card budget-card"><div class="entity-head"><div class="entity-title"><span class="entity-icon">${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>Limite mensal</small></div></div><button class="entity-menu" data-edit-category="${category.id}">✎</button></div><div class="budget-values"><strong>${brl.format(spent)}</strong><span>de ${brl.format(budget)}</span></div><div class="progress"><i class="${cls}" style="width:${barPercent}%"></i></div><small>${Math.round(percent)}% utilizado · ${room >= 0 ? `${brl.format(room)} restante` : `${brl.format(Math.abs(room))} acima do limite`}</small></article>`;
    }).join('') : emptyState('◉', 'Nenhum orçamento', 'Defina um limite em uma categoria de saída.');
    $$('#budgets-grid [data-edit-category]').forEach((button) => button.addEventListener('click', () => openEntityModal('category', button.dataset.editCategory)));
  }

  function renderGoals() {
    if (!hasPro()) {
      $('#goals-grid').innerHTML = '<div class="locked-banner">Metas financeiras fazem parte do plano Pro.<button data-view="billing">Ver plano Pro →</button></div>';
      $('#goals-grid [data-view="billing"]').addEventListener('click', () => switchView('billing'));
      return;
    }
    $('#goals-grid').innerHTML = state.goals.length ? state.goals.map((goal) => {
      const target = Number(goal.target_amount);
      const current = goalProgress(goal);
      const percent = target ? Math.min(100, current / target * 100) : 0;
      const linkedCount = paidTransactions().filter((row) => row.type === 'income' && row.goal_id === goal.id).length;
      return `<article class="entity-card goal-card"><div class="goal-top"><span class="goal-icon">${escapeHTML(goal.icon)}</span><div><button class="entity-menu" data-edit-goal="${goal.id}">✎</button><button class="entity-menu" data-delete-goal-row="${goal.id}">×</button></div></div><h3>${escapeHTML(goal.name)}</h3><p>${goal.due_date ? `Prazo: ${dateBR.format(new Date(`${goal.due_date}T12:00:00`))}` : 'Sem prazo definido'}</p><div class="goal-values"><strong>${brl.format(current)}</strong><span>${Math.round(percent)}%</span></div><div class="progress"><i style="width:${percent}%;background:#4f7de8"></i></div><footer><small>Faltam ${brl.format(Math.max(0, target - current))}${linkedCount ? ` · ${linkedCount} ${linkedCount === 1 ? 'entrada vinculada' : 'entradas vinculadas'}` : ''}</small><span class="goal-source-note">Vincule entradas em Novo lançamento</span></footer></article>`;
    }).join('') : emptyState('◎', 'Nenhuma meta ainda', 'Crie uma meta e vincule lançamentos para acompanhar o progresso.');
    $$('[data-edit-goal]').forEach((button) => button.addEventListener('click', () => openEntityModal('goal', button.dataset.editGoal)));
    $$('[data-delete-goal-row]').forEach((button) => button.addEventListener('click', () => deleteEntity('goal', button.dataset.deleteGoalRow)));
  }

  function renderReports() {
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

    const expenses = allCategories().filter((category) => category.type === 'expense').map((category) => ({ ...category, total: categorySpent(category.id, selectedKey) })).filter((category) => category.total > 0).sort((a, b) => b.total - a.total);
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

    const accountMovements = allAccounts().map((account) => {
      const rows = currentRows.filter((row) => row.account_id === account.id);
      const net = rows.reduce((sum, row) => sum + (row.type === 'income' ? Number(row.amount) : -Number(row.amount)), 0);
      return { ...account, net, count: rows.length };
    }).filter((account) => account.count > 0).sort((a, b) => Math.abs(b.net) - Math.abs(a.net));
    $('#report-accounts').innerHTML = accountMovements.map((account) => `<div class="rank-row"><span>${escapeHTML(account.icon)}</span><div><strong>${escapeHTML(account.name)}</strong><small>${account.count} ${account.count === 1 ? 'lançamento' : 'lançamentos'} no mês</small></div><b class="${account.net < 0 ? 'value-expense' : 'value-income'}">${account.net >= 0 ? '+' : '−'} ${brl.format(Math.abs(account.net))}</b></div>`).join('') || emptyState('▣', 'Sem movimentação', `Nenhuma conta teve lançamentos realizados em ${selectedLabel}.`);

    $('#report-budget-analysis').innerHTML = budgetRows.slice(0, 7).map((category) => {
      const percent = category.limit ? category.spent / category.limit * 100 : 0;
      const room = category.limit - category.spent;
      return `<div class="rank-row"><span>${escapeHTML(category.icon)}</span><div><strong>${escapeHTML(category.name)}</strong><small>${percent.toFixed(1).replace('.', ',')}% do limite · ${room >= 0 ? `${brl.format(room)} disponível` : `${brl.format(Math.abs(room))} acima`}</small></div><b class="${percent > 100 ? 'value-expense' : ''}">${brl.format(category.spent)}</b></div>`;
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

  function renderReportChart() {
    if (!window.Chart) return;
    const series = monthSeries(6, reportMonthKey);
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

  function renderBilling() {
    const activePlan = state.profile?.plan === 'essential' ? 'Essencial' : 'Pro';
    let statusText = 'Sem assinatura';
    if (state.profile?.subscription_status === 'trialing') {
      const remaining = Math.max(0, Math.ceil((new Date(state.profile.trial_ends_at).getTime() - Date.now()) / 86400000));
      statusText = `Experiência ${activePlan} · ${remaining} ${remaining === 1 ? 'dia restante' : 'dias restantes'}`;
    } else if (state.profile?.subscription_status === 'active') statusText = 'Assinatura ativa';
    else if (state.profile?.subscription_status === 'past_due') statusText = 'Pagamento pendente';
    else if (state.profile?.subscription_status === 'canceled') statusText = 'Assinatura encerrada';

    const headline = state.profile?.subscription_status === 'active' ? activePlan : state.profile?.subscription_status === 'trialing' ? `Experiência ${activePlan}` : 'Sem plano ativo';
    const currentLabel = state.profile?.subscription_status === 'active' ? activePlan : state.profile?.subscription_status === 'trialing' ? activePlan : '—';
    const subscriptionStatus = state.profile?.subscription_status || 'none';
    const planMessage = state.subscription?.cancel_at_period_end
      ? 'Cancelamento agendado para o fim do período.'
      : subscriptionStatus === 'trialing'
        ? `Seu acesso atual segue exatamente as permissões do ${activePlan}.`
        : subscriptionStatus === 'active'
          ? 'Use o portal de cobrança para alterar plano, pagamento ou renovação.'
          : subscriptionStatus === 'past_due'
            ? 'Atualize o pagamento pelo portal de cobrança para regularizar o acesso.'
            : subscriptionStatus === 'canceled'
              ? 'A assinatura anterior foi encerrada. Você pode escolher um novo plano abaixo.'
              : 'Escolha um plano abaixo quando quiser continuar após o período de experiência.';
    $('#current-plan').innerHTML = `<div><span>${escapeHTML(statusText.toUpperCase())}</span><h2>${escapeHTML(headline)}</h2><p>${escapeHTML(planMessage)}</p></div><div><small>Plano atual</small><strong>${escapeHTML(currentLabel)}</strong></div>`;
    const portalAvailable = Boolean(state.subscription?.stripe_subscription_id);
    $('#billing-portal').hidden = !portalAvailable;
    const mustUsePortal = ['active', 'past_due'].includes(subscriptionStatus);
    $$('[data-subscribe]').forEach((button) => {
      if (!button.dataset.defaultLabel) button.dataset.defaultLabel = button.textContent;
      button.textContent = mustUsePortal ? 'Alterar no portal' : button.dataset.defaultLabel;
    });
    $$('[data-billing-cycle]').forEach((button) => button.classList.toggle('active', button.dataset.billingCycle === billingCycle));
    $$('[data-price-monthly][data-price-annual]').forEach((price) => {
      const text = price.dataset[`price${billingCycle[0].toUpperCase()}${billingCycle.slice(1)}`];
      price.innerHTML = billingCycle === 'monthly' ? `${escapeHTML(text)}<small>/mês</small>` : escapeHTML(text);
    });
  }

  function syncGoalAllocationField() {
    const wrap = $('#tx-goal-amount-wrap');
    const input = $('#tx-goal-amount');
    const selectedType = $('input[name="transaction_type"]:checked')?.value || 'expense';
    const visible = hasPro() && selectedType === 'income' && Boolean($('#tx-goal')?.value);
    if (wrap) wrap.hidden = !visible;
    if (!visible && input) input.value = '';
  }

  function renderSelectOptions(type = null) {
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
    syncGoalAllocationField();
  }

  function renderFeatureLocks() {
    $$('[data-pro-feature]').forEach((button) => button.classList.toggle('locked', !hasPro()));
    $('#tx-recurring').disabled = !hasPro();
    syncGoalAllocationField();
  }

  function emptyState(icon, title, text) {
    return `<div class="empty-state"><span>${icon}</span><strong>${escapeHTML(title)}</strong><p>${escapeHTML(text)}</p></div>`;
  }

  function switchView(view) {
    if (view === 'goals' && !hasPro()) {
      toast('Recurso Pro', 'Metas financeiras fazem parte do plano Pro.', 'error');
      view = 'billing';
    }
    currentView = view;
    $$('.view').forEach((section) => section.classList.toggle('active', section.dataset.page === view));
    $$('[data-view]').forEach((button) => button.classList.toggle('active', button.dataset.view === view && button.closest('nav')));
    const labels = { dashboard: ['Visão geral', 'Dashboard'], transactions: ['Movimentações', 'Lançamentos'], accounts: ['Seu dinheiro', 'Contas'], categories: ['Organização', 'Categorias'], budgets: ['Planejamento', 'Orçamentos'], goals: ['Planejamento', 'Metas'], reports: ['Análise', 'Relatórios'], billing: ['Conta', 'Plano e cobrança'], settings: ['Conta', 'Configurações'] };
    const [kicker, title] = labels[view] || ['', 'SalesBoard'];
    $('#breadcrumb-kicker').textContent = kicker;
    $('#breadcrumb-title').textContent = title;
    closeSidebar();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function openModal(id) {
    document.body.classList.add('modal-open');
    document.getElementById(id).hidden = false;
  }

  function closeModals() {
    document.body.classList.remove('modal-open');
    $$('.modal').forEach((modal) => { modal.hidden = true; });
  }

  function openTransactionModal(id = null) {
    if (profileEntitlement() === 'none') {
      showOnly('paywall-screen');
      return;
    }
    if (!state.accounts.length || !state.categories.length) {
      toast('Configure sua estrutura', 'Crie ao menos uma conta e uma categoria antes de lançar.', 'error');
      return;
    }
    editingTransactionId = id;
    const row = id ? state.transactions.find((item) => item.id === id) : null;
    const type = row?.type || (transactionGoalPreset ? 'income' : 'expense');
    $(`input[name="transaction_type"][value="${type}"]`).checked = true;
    renderSelectOptions(type);
    $('#tx-description').value = row?.description || '';
    $('#tx-amount').value = row ? Number(row.amount).toFixed(2).replace('.', ',') : '';
    $('#tx-date').value = row?.transaction_date || isoDate();
    $('#tx-category').value = row?.category_id || $('#tx-category').options[0]?.value || '';
    $('#tx-account').value = row?.account_id || $('#tx-account').options[0]?.value || '';
    $('#tx-goal').value = row?.goal_id || transactionGoalPreset || '';
    $('#tx-goal-amount').value = row?.goal_amount ? Number(row.goal_amount).toFixed(2).replace('.', ',') : '';
    syncGoalAllocationField();
    transactionGoalPreset = null;
    $('#tx-status').value = row?.status || 'paid';
    $('#tx-recurring').checked = Boolean(row?.recurring);
    $('#tx-recurrence').value = row?.recurrence_interval || 'monthly';
    $('#recurrence-wrap').hidden = !$('#tx-recurring').checked;
    $('#tx-notes').value = row?.notes || '';
    $('#transaction-modal h2').textContent = row ? 'Editar lançamento' : 'Novo lançamento';
    openModal('transaction-modal');
  }

  async function saveTransaction(event) {
    event.preventDefault();
    const button = $('#transaction-form button[type="submit"]');
    setButtonLoading(button, true, 'Salvando...');
    try {
      const type = $('input[name="transaction_type"]:checked').value;
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
        recurring: $('#tx-recurring').checked,
        recurrence_interval: $('#tx-recurring').checked ? $('#tx-recurrence').value : null,
        notes: $('#tx-notes').value.trim() || null
      };
      if (!payload.description || payload.amount <= 0) throw new Error('Preencha descrição e valor corretamente.');
      if (!payload.category_id) throw new Error('Crie ou selecione uma categoria compatível com este lançamento.');
      if (payload.goal_amount != null && (payload.goal_amount <= 0 || payload.goal_amount > payload.amount)) throw new Error('INVALID_GOAL_AMOUNT');
      if (payload.recurring && !hasPro()) throw new Error('PLAN_REQUIRED_PRO');
      if (demoMode) {
        if (editingTransactionId) Object.assign(state.transactions.find((item) => item.id === editingTransactionId), payload);
        else state.transactions.unshift({ ...payload, id: `demo-${Date.now()}` });
      } else if (editingTransactionId) {
        const { error } = await supabaseClient.from('transactions').update(payload).eq('id', editingTransactionId).eq('user_id', state.user.id);
        if (error) throw error;
      } else {
        const { error } = await supabaseClient.from('transactions').insert(payload);
        if (error) throw error;
      }
      if (!demoMode) await loadFinancialData();
      closeModals();
      renderAll();
      toast(editingTransactionId ? 'Lançamento atualizado' : 'Lançamento salvo');
    } catch (error) {
      toast('Não foi possível salvar', friendlyError(error), 'error');
    } finally {
      setButtonLoading(button, false);
    }
  }

  async function deleteTransaction(id) {
    const row = state.transactions.find((item) => item.id === id);
    const confirmed = await requestConfirmation({
      title: 'Excluir lançamento?',
      message: row ? `“${row.description}” será removido do histórico e dos cálculos financeiros.` : 'Este lançamento será removido do histórico e dos cálculos financeiros.',
      confirmLabel: 'Excluir lançamento',
      details: row?.goal_id ? ['O valor destinado à meta também deixará de contar no progresso.'] : []
    });
    if (!confirmed) return;
    try {
      if (demoMode) state.transactions = state.transactions.filter((row) => row.id !== id);
      else {
        const { error } = await supabaseClient.from('transactions').delete().eq('id', id).eq('user_id', state.user.id);
        if (error) throw error;
        await loadFinancialData();
      }
      renderAll();
      toast('Lançamento excluído');
    } catch (error) {
      toast('Não foi possível excluir', friendlyError(error), 'error');
    }
  }

  function openEntityModal(mode, id = null) {
    if (profileEntitlement() === 'none') {
      showOnly('paywall-screen');
      return;
    }
    if (mode === 'goal' && !hasPro()) {
      toast('Recurso Pro', 'Metas financeiras fazem parte do plano Pro.', 'error');
      switchView('billing');
      return;
    }
    entityMode = mode;
    editingEntityId = id;
    const fields = $('#entity-fields');
    const title = $('#entity-title');
    const kicker = $('#entity-kicker');
    if (mode === 'account') {
      const row = id ? state.accounts.find((item) => item.id === id) : null;
      title.textContent = row ? 'Editar conta' : 'Nova conta';
      kicker.textContent = 'Contas';
      fields.innerHTML = `<label class="full">Nome<input name="name" maxlength="80" required value="${escapeHTML(row?.name || '')}" placeholder="Ex: Conta principal" /></label><label>Tipo<select name="type"><option value="bank">Conta bancária</option><option value="cash">Dinheiro</option><option value="wallet">Carteira digital</option><option value="investment">Investimento</option></select></label><label>Saldo inicial<div class="money-field"><span>R$</span><input name="opening_balance" inputmode="decimal" required value="${row ? Number(row.opening_balance).toFixed(2).replace('.', ',') : '0,00'}" /></div></label><label>Ícone<input name="icon" maxlength="8" value="${escapeHTML(row?.icon || '▣')}" /></label><label>Cor<input name="color" type="color" value="${escapeHTML(row?.color || '#34d399')}" /></label>`;
      fields.querySelector('[name="type"]').value = row?.type || 'bank';
    } else if (mode === 'category') {
      const row = id ? state.categories.find((item) => item.id === id) : null;
      title.textContent = row ? 'Editar categoria' : 'Nova categoria';
      kicker.textContent = 'Categorias';
      fields.innerHTML = `<label class="full">Nome<input name="name" maxlength="80" required value="${escapeHTML(row?.name || '')}" placeholder="Ex: Mercado" /></label><label>Tipo<select name="type"><option value="expense">Saída</option><option value="income">Entrada</option></select></label><label>Limite mensal<div class="money-field"><span>R$</span><input name="budget" inputmode="decimal" value="${row ? Number(row.budget || 0).toFixed(2).replace('.', ',') : '0,00'}" /></div><small class="field-help">Disponível apenas para categorias de saída.</small></label><label>Ícone<input name="icon" maxlength="8" value="${escapeHTML(row?.icon || '•')}" /></label><label>Cor<input name="color" type="color" value="${escapeHTML(row?.color || '#4f7de8')}" /></label>`;
      const categoryTypeSelect = fields.querySelector('[name="type"]');
      categoryTypeSelect.value = row?.type || categoryType;
      const categoryIsUsed = Boolean(row && state.transactions.some((transaction) => transaction.category_id === row.id));
      if (categoryIsUsed) {
        categoryTypeSelect.disabled = true;
        categoryTypeSelect.title = 'O tipo não pode mudar porque esta categoria já possui lançamentos.';
      }
      const budgetLabel = fields.querySelector('[name="budget"]')?.closest('label');
      const syncBudgetVisibility = () => {
        const expense = categoryTypeSelect.value === 'expense';
        if (budgetLabel) budgetLabel.hidden = !expense;
        if (!expense) fields.querySelector('[name="budget"]').value = '0,00';
      };
      categoryTypeSelect.addEventListener('change', syncBudgetVisibility);
      syncBudgetVisibility();
    } else if (mode === 'goal') {
      const row = id ? state.goals.find((item) => item.id === id) : null;
      title.textContent = row ? 'Editar meta' : 'Nova meta';
      kicker.textContent = 'Metas';
      fields.innerHTML = `<label class="full">Nome<input name="name" maxlength="100" required value="${escapeHTML(row?.name || '')}" placeholder="Ex: Reserva de emergência" /></label><label>Valor alvo<div class="money-field"><span>R$</span><input name="target_amount" inputmode="decimal" required value="${row ? Number(row.target_amount).toFixed(2).replace('.', ',') : ''}" /></div></label><label>Valor já acumulado<div class="money-field"><span>R$</span><input name="current_amount" inputmode="decimal" value="${row ? Number(row.current_amount).toFixed(2).replace('.', ',') : '0,00'}" /></div><small class="field-help">Use aqui somente o valor que já existia antes dos lançamentos vinculados.</small></label><label>Prazo<input name="due_date" type="date" value="${row?.due_date || ''}" /></label><label>Ícone<input name="icon" maxlength="8" value="${escapeHTML(row?.icon || '◎')}" /></label>`;
    }
    openModal('entity-modal');
  }

  async function saveEntity(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const button = $('#entity-form button[type="submit"]');
    setButtonLoading(button, true, 'Salvando...');
    try {
      if (entityMode === 'account') {
        const payload = { user_id: state.user.id, name: form.get('name').trim(), type: form.get('type'), opening_balance: parseMoney(form.get('opening_balance')), icon: form.get('icon').trim() || '▣', color: form.get('color') || COLORS[0] };
        await persistEntity('accounts', payload, editingEntityId);
      } else if (entityMode === 'category') {
        const payload = { user_id: state.user.id, name: form.get('name').trim(), type: form.get('type'), budget: form.get('type') === 'expense' ? Math.max(0, parseMoney(form.get('budget'))) : 0, icon: form.get('icon').trim() || '•', color: form.get('color') || COLORS[1] };
        await persistEntity('categories', payload, editingEntityId);
      } else if (entityMode === 'goal') {
        const payload = { user_id: state.user.id, name: form.get('name').trim(), target_amount: parseMoney(form.get('target_amount')), current_amount: Math.max(0, parseMoney(form.get('current_amount'))), due_date: form.get('due_date') || null, icon: form.get('icon').trim() || '◎' };
        if (payload.target_amount <= 0) throw new Error('Defina um valor alvo maior que zero.');
        await persistEntity('goals', payload, editingEntityId);
      }
      if (!demoMode) await loadFinancialData();
      closeModals();
      renderAll();
      toast('Alterações salvas');
    } catch (error) {
      toast('Não foi possível salvar', friendlyError(error), 'error');
    } finally {
      setButtonLoading(button, false);
    }
  }

  async function persistEntity(table, payload, id) {
    if (demoMode) {
      const key = table === 'accounts' ? 'accounts' : table === 'categories' ? 'categories' : 'goals';
      if (id) Object.assign(state[key].find((row) => row.id === id), payload);
      else state[key].push({ ...payload, id: `demo-${Date.now()}-${Math.random().toString(16).slice(2)}` });
      return;
    }
    const query = id ? supabaseClient.from(table).update(payload).eq('id', id).eq('user_id', state.user.id) : supabaseClient.from(table).insert(payload);
    const { error } = await query;
    if (error) throw error;
  }

  async function deleteEntity(mode, id) {
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

  function exportCSV(monthFilter = null) {
    const source = monthFilter ? state.transactions.filter((row) => monthKey(row.transaction_date) === monthFilter) : state.transactions;
    const rows = [['Descrição', 'Tipo', 'Categoria', 'Conta', 'Meta', 'Valor na meta', 'Data', 'Status', 'Recorrente', 'Valor'], ...source.map((row) => [row.description, row.type === 'income' ? 'Entrada' : 'Saída', categoryById(row.category_id).name, accountById(row.account_id).name, goalById(row.goal_id)?.name || '', row.goal_id ? Number(row.goal_amount || row.amount).toFixed(2).replace('.', ',') : '', row.transaction_date, row.status === 'paid' ? 'Pago' : 'Pendente', row.recurring ? 'Sim' : 'Não', Number(row.amount).toFixed(2).replace('.', ',')])];
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

  async function subscribe(plan) {
    if (demoMode) {
      toast('Demonstração', 'A cobrança real fica disponível somente no ambiente de produção.');
      return;
    }
    try {
      const { data } = await supabaseClient.auth.getSession();
      const token = data.session?.access_token;
      if (!token) throw new Error('Sua sessão expirou. Entre novamente.');
      const response = await fetch('/api/checkout', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ plan, billingCycle, requestId: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}` }) });
      const payload = await response.json();
      if (response.status === 409 && payload.code === 'SUBSCRIPTION_EXISTS') {
        toast('Assinatura já existente', payload.error, 'error');
        return;
      }
      if (!response.ok || !payload.url) throw new Error(payload.error || 'Checkout indisponível.');
      location.href = payload.url;
    } catch (error) {
      toast('Não foi possível abrir o checkout', friendlyError(error), 'error');
    }
  }

  async function openBillingPortal() {
    if (demoMode) {
      toast('Demonstração', 'O portal de cobrança é ativado no ambiente de produção.');
      return;
    }
    try {
      const { data } = await supabaseClient.auth.getSession();
      const token = data.session?.access_token;
      const response = await fetch('/api/billing-portal', { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      const payload = await response.json();
      if (!response.ok || !payload.url) throw new Error(payload.error || 'Portal indisponível.');
      location.href = payload.url;
    } catch (error) {
      toast('Não foi possível abrir a cobrança', friendlyError(error), 'error');
    }
  }

  async function refreshAll() {
    if (demoMode) {
      toast('Demonstração atualizada');
      return;
    }
    const button = $('#refresh-data');
    setButtonLoading(button, true, 'Atualizando...');
    try {
      const { data: profile, error } = await supabaseClient.from('profiles').select('*').eq('id', state.user.id).single();
      if (error) throw error;
      state.profile = profile;
      await loadFinancialData();
      renderIdentity();
      renderAll();
      toast('Dados atualizados');
    } catch (error) {
      toast('Falha ao atualizar', friendlyError(error), 'error');
    } finally {
      setButtonLoading(button, false);
    }
  }

  function setupOnboarding() {
    $('#workspace-name-input').value = state.profile?.workspace_name || 'Meu espaço';
    const oauthTerms = $('#oauth-terms-wrap');
    if (oauthTerms) {
      oauthTerms.hidden = Boolean(state.profile?.terms_accepted_at);
      const checkbox = $('#oauth-accept-terms');
      if (checkbox) checkbox.checked = Boolean(state.profile?.terms_accepted_at);
    }
    onboardingStep = 1;
    updateOnboardingTemplatePreview();
    updateOnboardingStep();
  }

  function updateOnboardingTemplatePreview() {
    const type = $('input[name="workspace_type"]:checked')?.value || 'personal';
    const templates = {
      personal: ['🏠 Moradia', '🛒 Alimentação', '🚗 Transporte', '❤️ Saúde', '🎮 Lazer', '💡 Serviços', '💼 Salário', '💰 Renda extra'],
      freelancer: ['🧰 Ferramentas', '🧾 Impostos', '📣 Marketing', '🚗 Transporte', '💡 Serviços', '• Outras despesas', '💼 Clientes', '💰 Outras receitas'],
      business: ['📦 Fornecedores', '⚙️ Operação', '📣 Marketing', '🧾 Impostos', '💡 Serviços', '• Outras despesas', '💼 Vendas e serviços', '💰 Outras receitas']
    };
    const preview = $('#seed-preview');
    if (preview) preview.innerHTML = templates[type].map((item) => `<span>${escapeHTML(item)}</span>`).join('');
  }

  function updateOnboardingStep() {
    $$('.onboarding-step').forEach((section) => section.classList.toggle('active', Number(section.dataset.step) === onboardingStep));
    $('#onboarding-step-label').textContent = `Etapa ${onboardingStep} de 3`;
    $('#onboarding-progress').style.width = `${onboardingStep / 3 * 100}%`;
    $('#onboarding-back').disabled = onboardingStep === 1;
    $('#onboarding-next').hidden = onboardingStep === 3;
    $('#onboarding-finish').hidden = onboardingStep !== 3;
  }

  async function finishOnboarding(event) {
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

  async function saveProfile(event) {
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

  async function logout() {
    if (demoMode) {
      location.href = '../';
      return;
    }
    await supabaseClient.auth.signOut();
    location.href = './?mode=login';
  }

  async function deleteAccountPermanently() {
    if (demoMode) {
      toast('Demonstração', 'A exclusão real só existe no ambiente de produção.');
      return;
    }
    const confirmed = await requestConfirmation({
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
    try {
      const { data } = await supabaseClient.auth.getSession();
      const response = await fetch('/api/delete-account', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${data.session?.access_token}` }, body: JSON.stringify({ confirmation }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Falha na exclusão.');
      await supabaseClient.auth.signOut({ scope: 'local' });
      location.href = '../?account=deleted';
    } catch (error) {
      toast('Não foi possível excluir a conta', friendlyError(error), 'error');
    }
  }

  function renderGlobalSearch() {
    const query = $('#global-search-input').value.trim().toLowerCase();
    const results = [];
    if (query) {
      state.transactions.filter((row) => row.description.toLowerCase().includes(query)).slice(0, 5).forEach((row) => results.push({ icon: categoryById(row.category_id).icon, title: row.description, subtitle: `${brl.format(Number(row.amount))} · Lançamento`, view: 'transactions' }));
      state.accounts.filter((row) => row.name.toLowerCase().includes(query)).slice(0, 4).forEach((row) => results.push({ icon: row.icon, title: row.name, subtitle: `${brl.format(accountBalance(row.id))} · Conta`, view: 'accounts' }));
      state.categories.filter((row) => row.name.toLowerCase().includes(query)).slice(0, 4).forEach((row) => results.push({ icon: row.icon, title: row.name, subtitle: 'Categoria', view: 'categories' }));
      if (hasPro()) state.goals.filter((row) => row.name.toLowerCase().includes(query)).slice(0, 4).forEach((row) => results.push({ icon: row.icon, title: row.name, subtitle: 'Meta', view: 'goals' }));
    }
    $('#global-search-results').innerHTML = query ? (results.length ? results.map((result) => `<button class="search-result" data-search-view="${result.view}"><span>${escapeHTML(result.icon)}</span><div><strong>${escapeHTML(result.title)}</strong><small>${escapeHTML(result.subtitle)}</small></div><b>→</b></button>`).join('') : emptyState('⌕', 'Nada encontrado', 'Tente outro termo.')) : '<div class="empty-state"><span>⌕</span><strong>Busca global</strong><p>Procure lançamentos, contas, categorias ou metas.</p></div>';
    $$('[data-search-view]').forEach((button) => button.addEventListener('click', () => { closeModals(); switchView(button.dataset.searchView); }));
  }

  function openSearch() {
    openModal('search-modal');
    $('#global-search-input').value = '';
    renderGlobalSearch();
    setTimeout(() => $('#global-search-input').focus(), 50);
  }

  function openSidebar() {
    $('#sidebar').classList.add('open');
    $('#sidebar-overlay').classList.add('open');
  }

  function closeSidebar() {
    $('#sidebar').classList.remove('open');
    $('#sidebar-overlay').classList.remove('open');
  }

  async function googleProviderAvailable() {
    try {
      const response = await fetch(`${publicConfig.supabaseUrl}/auth/v1/settings`, {
        headers: { apikey: publicConfig.supabasePublishableKey, Accept: 'application/json' },
        cache: 'no-store'
      });
      if (!response.ok) return null;
      const settings = await response.json();
      return settings?.external?.google === true;
    } catch (error) {
      console.warn('Não foi possível verificar o provedor Google.', error);
      return null;
    }
  }

  async function signInWithGoogle() {
    const button = $('#google-auth-button');
    if (!supabaseClient) return;
    setButtonLoading(button, true, 'Verificando Google...');
    setAuthMessage('');
    try {
      const available = await googleProviderAvailable();
      if (available !== true) {
        const message = available === false
          ? 'O login com Google ainda não está habilitado. Use e-mail e senha por enquanto; estamos finalizando essa configuração.'
          : 'Não foi possível verificar o login com Google agora. Tente novamente ou use e-mail e senha.';
        setAuthMessage(message, true);
        return;
      }

      setButtonLoading(button, true, 'Abrindo Google...');
      sessionStorage.setItem('salesboard_oauth_intent', JSON.stringify({ plan: requestedPlan, billing: billingCycle, createdAt: Date.now() }));
      const { data, error } = await supabaseClient.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo: appBaseUrl('oauth=google'), skipBrowserRedirect: true, queryParams: { prompt: 'select_account' } }
      });
      if (error) throw error;
      if (!data?.url) throw new Error('Não foi possível iniciar o login com Google.');
      location.assign(data.url);
    } catch (error) {
      setAuthMessage(authErrorMessage(error), true);
    } finally {
      setButtonLoading(button, false);
    }
  }

  function initStaticEvents() {
    $('#google-auth-button')?.addEventListener('click', signInWithGoogle);
    $$('[data-auth-mode]').forEach((button) => button.addEventListener('click', () => setAuthMode(button.dataset.authMode)));
    $$('[data-toggle-password]').forEach((button) => button.addEventListener('click', () => {
      const input = document.getElementById(button.dataset.togglePassword);
      input.type = input.type === 'password' ? 'text' : 'password';
    }));
    $('#login-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = event.currentTarget.querySelector('button[type="submit"]');
      setButtonLoading(button, true, 'Entrando...');
      setAuthMessage('');
      try {
        const { data, error } = await supabaseClient.auth.signInWithPassword({ email: $('#login-email').value.trim(), password: $('#login-password').value });
        if (error) throw error;
        session = data.session;
        await initializeAuthenticatedUser();
      } catch (error) {
        setAuthMessage(authErrorMessage(error), true);
      } finally {
        setButtonLoading(button, false);
      }
    });
    $('#register-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = event.currentTarget.querySelector('button[type="submit"]');
      if (!$('#accept-terms').checked) return;
      setButtonLoading(button, true, 'Criando conta...');
      setAuthMessage('');
      try {
        const email = $('#register-email').value.trim();
        const { data, error } = await supabaseClient.auth.signUp({
          email,
          password: $('#register-password').value,
          options: {
            emailRedirectTo: `${location.origin}${location.pathname}`,
            data: {
              full_name: $('#register-name').value.trim(),
              selected_plan: requestedPlan,
              terms_accepted_at: new Date().toISOString(),
              terms_version: '2026-08-12'
            }
          }
        });
        if (error) throw error;
        if (data.session) {
          session = data.session;
          await initializeAuthenticatedUser();
        } else {
          setAuthMessage(`Conta criada. Enviamos uma confirmação para ${email}. Confirme o e-mail e depois entre no SalesBoard.`);
          setAuthMode('login');
          $('#login-email').value = email;
        }
      } catch (error) {
        setAuthMessage(authErrorMessage(error), true);
      } finally {
        setButtonLoading(button, false);
      }
    });
    $('#forgot-password').addEventListener('click', () => {
      $('#forgot-email').value = $('#login-email').value.trim();
      setInlineMessage('#forgot-status', '');
      showOnly('forgot-screen');
    });
    $('#forgot-back').addEventListener('click', () => showAuth('login'));
    $('#forgot-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = event.currentTarget.querySelector('button[type="submit"]');
      const email = $('#forgot-email').value.trim();
      setButtonLoading(button, true, 'Enviando...');
      setInlineMessage('#forgot-status', '');
      try {
        const { error } = await supabaseClient.auth.resetPasswordForEmail(email, { redirectTo: appBaseUrl('recovery=1') });
        if (error) throw error;
        setInlineMessage('#forgot-status', 'Se este e-mail estiver cadastrado, o link de recuperação foi enviado. Confira também a caixa de spam.');
      } catch (error) {
        setInlineMessage('#forgot-status', authErrorMessage(error), true);
      } finally {
        setButtonLoading(button, false);
      }
    });
    $('#resend-confirmation').addEventListener('click', async (event) => {
      const button = event.currentTarget;
      const email = button.dataset.email || $('#register-email').value.trim();
      if (!email) return;
      setButtonLoading(button, true, 'Reenviando...');
      try {
        const { error } = await supabaseClient.auth.resend({ type: 'signup', email, options: { emailRedirectTo: appBaseUrl() } });
        if (error) throw error;
        setAuthMessage('Novo e-mail de confirmação enviado. Aguarde pelo menos 45 segundos antes de pedir outro.');
      } catch (error) {
        setAuthMessage(authErrorMessage(error), true);
      } finally {
        setTimeout(() => setButtonLoading(button, false), 45000);
      }
    });
    const updateRecoveryRules = () => {
      const password = $('#recovery-password').value;
      const confirmPassword = $('#recovery-password-confirm').value;
      $('#rule-length').textContent = `${password.length >= 8 ? '✓' : '○'} 8 ou mais caracteres`;
      $('#rule-match').textContent = `${password && password === confirmPassword ? '✓' : '○'} As duas senhas são iguais`;
    };
    $('#recovery-password').addEventListener('input', updateRecoveryRules);
    $('#recovery-password-confirm').addEventListener('input', updateRecoveryRules);
    $('#recovery-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = event.currentTarget.querySelector('button[type="submit"]');
      const password = $('#recovery-password').value;
      const confirmPassword = $('#recovery-password-confirm').value;
      if (password.length < 8) return setInlineMessage('#recovery-message', 'Use pelo menos 8 caracteres.', true);
      if (password !== confirmPassword) return setInlineMessage('#recovery-message', 'As duas senhas precisam ser iguais.', true);
      setButtonLoading(button, true, 'Salvando...');
      setInlineMessage('#recovery-message', '');
      try {
        const email = session?.user?.email || '';
        const { error } = await supabaseClient.auth.updateUser({ password });
        if (error) throw error;
        await supabaseClient.auth.signOut();
        session = null;
        history.replaceState({}, '', appBaseUrl());
        showAuth('login');
        if (email) $('#login-email').value = email;
        setAuthMessage('Senha atualizada com sucesso. Entre novamente usando sua nova senha.');
      } catch (error) {
        setInlineMessage('#recovery-message', authErrorMessage(error), true);
      } finally {
        setButtonLoading(button, false);
      }
    });
    $('#onboarding-next').addEventListener('click', () => { if (onboardingStep < 3) { onboardingStep += 1; updateOnboardingStep(); } });
    $('#onboarding-back').addEventListener('click', () => { if (onboardingStep > 1) { onboardingStep -= 1; updateOnboardingStep(); } });
    $('#onboarding-form').addEventListener('submit', finishOnboarding);
    $$('[data-view]').forEach((button) => button.addEventListener('click', () => switchView(button.dataset.view)));
    $$('[data-open-transaction]').forEach((button) => button.addEventListener('click', () => openTransactionModal()));
    $('#quick-add').addEventListener('click', () => openTransactionModal());
    $$('[data-close-modal]').forEach((button) => button.addEventListener('click', closeModals));
    $$('.modal').forEach((modal) => modal.addEventListener('click', (event) => { if (event.target === modal) closeModals(); }));
    $('#transaction-form').addEventListener('submit', saveTransaction);
    $$('input[name="transaction_type"]').forEach((radio) => radio.addEventListener('change', () => renderSelectOptions(radio.value)));
    $$('input[name="workspace_type"]').forEach((radio) => radio.addEventListener('change', updateOnboardingTemplatePreview));
    $('#tx-recurring').addEventListener('change', () => { $('#recurrence-wrap').hidden = !$('#tx-recurring').checked; });
    $('#entity-form').addEventListener('submit', saveEntity);
    $('#add-account').addEventListener('click', () => openEntityModal('account'));
    $('#add-category').addEventListener('click', () => openEntityModal('category'));
    $('#add-goal').addEventListener('click', () => openEntityModal('goal'));
    $$('.category-tabs [data-category-type]').forEach((button) => button.addEventListener('click', () => { categoryType = button.dataset.categoryType; renderCategories(); }));
    $$('#transaction-filters [data-filter]').forEach((button) => button.addEventListener('click', () => { transactionFilter = button.dataset.filter; $$('#transaction-filters button').forEach((item) => item.classList.toggle('active', item === button)); renderTransactions(); }));
    $('#transaction-search').addEventListener('input', renderTransactions);
    $('#report-month').addEventListener('change', (event) => { reportMonthKey = event.target.value || currentMonthKey(); renderReports(); });
    $('#tx-goal').addEventListener('change', syncGoalAllocationField);
    $('#export-csv').addEventListener('click', () => exportCSV());
    $('#reports-export').addEventListener('click', () => exportCSV(reportMonthKey));
    $('#settings-export').addEventListener('click', () => exportCSV());
    $('#paywall-export').addEventListener('click', () => exportCSV());
    $('#profile-form').addEventListener('submit', saveProfile);
    $('#logout-button').addEventListener('click', logout);
    $('#paywall-logout').addEventListener('click', logout);
    $('#delete-account').addEventListener('click', deleteAccountPermanently);
    $$('[data-start-trial]').forEach((button) => button.addEventListener('click', () => startTrial(button.dataset.startTrial, button)));
    $('#trial-plan-logout')?.addEventListener('click', logout);
    $$('[data-subscribe]').forEach((button) => button.addEventListener('click', () => ['active', 'past_due'].includes(state.profile?.subscription_status) ? openBillingPortal() : subscribe(button.dataset.subscribe)));
    $$('[data-paywall-plan]').forEach((button) => button.addEventListener('click', () => subscribe(button.dataset.paywallPlan)));
    $$('[data-billing-cycle]').forEach((button) => button.addEventListener('click', () => { billingCycle = button.dataset.billingCycle; renderBilling(); }));
    $('#billing-portal').addEventListener('click', openBillingPortal);
    $('#refresh-data').addEventListener('click', refreshAll);
    $('#search-button').addEventListener('click', openSearch);
    $('#global-search-input').addEventListener('input', renderGlobalSearch);
    $('#menu-button').addEventListener('click', openSidebar);
    $('#sidebar-close').addEventListener('click', closeSidebar);
    $('#sidebar-overlay').addEventListener('click', closeSidebar);
    document.addEventListener('keydown', (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); openSearch(); }
      if (event.key === 'Escape') { if (confirmationState) closeConfirmation(false); else closeModals(); closeSidebar(); }
    });
  }

  initialize().catch((error) => {
    console.error(error);
    $('#setup-missing').innerHTML = `<code>${escapeHTML(friendlyError(error))}</code>`;
    showOnly('setup-error');
  });
})();
