from pathlib import Path
import re

ROOT = Path('salesboard')
APP_JS = ROOT / 'app' / 'app.js'
INDEX = ROOT / 'app' / 'index.html'
CSS = ROOT / 'app' / 'app.css'
CHECK = Path('.github/workflows/salesboard-production-check.yml')
RUNTIME = ROOT / 'app' / 'runtime-bridge.js'
PRIVACY = ROOT / 'legal' / 'privacidade.html'


def replace_once(text, old, new, label):
    if old not in text:
        if new in text:
            return text
        raise SystemExit(f'Marker not found: {label}')
    return text.replace(old, new, 1)


def regex_once(text, pattern, replacement, label):
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count == 0:
        if replacement.strip() in text:
            return text
        raise SystemExit(f'Regex marker not found: {label}')
    return updated

# ---------- app/index.html ----------
html = INDEX.read_text(encoding='utf-8')
if 'id="trial-plan-screen"' not in html:
    marker = '  <section id="onboarding-screen" class="onboarding-screen" hidden>'
    trial_screen = '''  <section id="trial-plan-screen" class="trial-choice-screen" hidden>
    <div class="trial-choice-shell">
      <header class="trial-choice-brand"><a class="brand" href="../"><span class="brand-mark"><i></i><i></i><i></i></span><span>SalesBoard <b>Finance</b></span></a><button type="button" class="link-button" id="trial-plan-logout">Sair</button></header>
      <div class="trial-choice-intro"><span class="kicker">3 dias para conhecer de verdade</span><h1>Escolha a experiência que combina com você.</h1><p>Seu período começa somente quando você escolher um plano. São 72 horas completas, sem cartão, com os recursos reais daquele plano.</p><div class="trial-choice-note"><span>✓ Sem cartão agora</span><span>✓ Uma única experiência por conta/e-mail</span><span>✓ Seus dados ficam preservados depois</span></div></div>
      <div class="trial-plan-grid">
        <article class="trial-plan-card" data-trial-card="essential">
          <div class="trial-plan-top"><span class="trial-plan-name">Essencial</span><strong>R$ 14,90<small>/mês depois</small></strong></div>
          <p>Para organizar o dia a dia com simplicidade e visão do que entra, sai e está planejado.</p>
          <ul><li>Até 3 contas ativas</li><li>Lançamentos ilimitados</li><li>Categorias e orçamentos personalizados</li><li>Dashboard e relatórios essenciais</li><li>Busca, filtros e exportação CSV</li></ul>
          <button type="button" class="button outline wide" data-start-trial="essential">Testar Essencial por 3 dias</button>
        </article>
        <article class="trial-plan-card featured" data-trial-card="pro">
          <span class="trial-recommended">MAIS COMPLETO</span>
          <div class="trial-plan-top"><span class="trial-plan-name">Pro</span><strong>R$ 24,90<small>/mês depois</small></strong></div>
          <p>Para quem quer uma visão mais profunda, automação e liberdade total para estruturar as finanças.</p>
          <ul><li>Contas ilimitadas</li><li>Tudo do Essencial</li><li>Metas financeiras</li><li>Lançamentos recorrentes</li><li>Relatórios avançados de 12 meses</li><li>Diagnósticos e análises detalhadas</li></ul>
          <button type="button" class="button primary wide" data-start-trial="pro">Testar Pro por 3 dias</button>
        </article>
      </div>
      <p class="trial-choice-footnote">A escolha define os recursos disponíveis durante os 3 dias. O período não reinicia ao trocar de plano depois.</p>
    </div>
  </section>

'''
    html = replace_once(html, marker, trial_screen + marker, 'trial plan screen insert')

paywall_pattern = r'  <section id="paywall-screen" class="center-screen" hidden>.*?</section>\n\n  <section id="app-shell"'
paywall_replacement = '''  <section id="paywall-screen" class="center-screen" hidden>
    <div class="paywall-card continuation-card">
      <div class="continuation-icon">◇</div>
      <span class="kicker" id="paywall-kicker">Seu espaço continua aqui</span>
      <h1 id="paywall-title">Continue de onde você parou.</h1>
      <p id="paywall-copy">Seus dados permanecem preservados. Ative um plano para retomar sua organização financeira com tudo no lugar.</p>
      <div class="continuation-context"><div><small>Experiência escolhida</small><strong id="paywall-tested-plan">Pro</strong></div><div><small>Seus dados</small><strong>Preservados</strong></div></div>
      <div class="paywall-plans">
        <article data-paywall-card="essential"><span>Essencial</span><strong>R$14,90<small>/mês</small></strong><p>Até 3 contas, lançamentos ilimitados, orçamentos e relatórios essenciais.</p><button class="button outline wide" data-paywall-plan="essential">Continuar com Essencial</button></article>
        <article data-paywall-card="pro"><span>Pro</span><strong>R$24,90<small>/mês</small></strong><p>Contas ilimitadas, metas, recorrências e relatórios avançados de 12 meses.</p><button class="button outline wide" data-paywall-plan="pro">Continuar com Pro</button></article>
      </div>
      <p class="continuation-note">A assinatura é processada com segurança pelo Stripe. Você pode gerenciar cobrança e cancelamento pelo portal do cliente.</p>
      <div class="paywall-actions"><button class="link-button" id="paywall-export">Exportar meus dados</button><button class="link-button" id="paywall-logout">Sair</button></div>
    </div>
  </section>

  <section id="app-shell"'''
html = regex_once(html, paywall_pattern, paywall_replacement, 'paywall replacement')
INDEX.write_text(html, encoding='utf-8')

# ---------- app/app.js ----------
js = APP_JS.read_text(encoding='utf-8')
js = replace_once(
    js,
    "['boot-screen', 'setup-error', 'auth-screen', 'forgot-screen', 'recovery-screen', 'onboarding-screen', 'paywall-screen', 'app-shell']",
    "['boot-screen', 'setup-error', 'auth-screen', 'forgot-screen', 'recovery-screen', 'trial-plan-screen', 'onboarding-screen', 'paywall-screen', 'app-shell']",
    'showOnly screens'
)
js = replace_once(
    js,
    "if (profile.subscription_status === 'trialing' && new Date(profile.trial_ends_at).getTime() > Date.now()) return 'pro';",
    "if (profile.subscription_status === 'trialing' && new Date(profile.trial_ends_at).getTime() > Date.now()) return profile.plan === 'essential' ? 'essential' : 'pro';",
    'trial entitlement matches selected plan'
)

if "TRIAL_ALREADY_USED" not in js:
    js = replace_once(
        js,
        "    if (message.includes('SUBSCRIPTION_REQUIRED')) return 'Seu período de acesso terminou. Escolha um plano para continuar.';",
        "    if (message.includes('SUBSCRIPTION_REQUIRED')) return 'Seu período de acesso terminou. Escolha um plano para continuar.';\n    if (message.includes('TRIAL_ALREADY_USED')) return 'Este e-mail já utilizou o período de experiência. Escolha um plano para continuar.';\n    if (message.includes('TRIAL_ALREADY_STARTED')) return 'Seu período de experiência já foi iniciado em outro plano e não pode ser reiniciado.';\n    if (message.includes('INVALID_TRIAL_PLAN')) return 'Não foi possível identificar o plano escolhido. Atualize a página e tente novamente.';",
        'trial friendly errors'
    )

if 'async function trialEligible()' not in js:
    helpers = '''  async function trialEligible() {
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

'''
    js = replace_once(js, '  async function initializeAuthenticatedUser() {', helpers + '  async function initializeAuthenticatedUser() {', 'insert trial helpers')

init_pattern = r"  async function initializeAuthenticatedUser\(\) \{.*?\n  \}\n\n  async function loadFinancialData"
init_replacement = '''  async function initializeAuthenticatedUser() {
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

  async function loadFinancialData'''
js = regex_once(js, init_pattern, init_replacement, 'initializeAuthenticatedUser')

trial_card_pattern = r"  function renderTrialCard\(\) \{.*?\n  \}\n\n  function renderAll"
trial_card_replacement = '''  function renderTrialCard() {
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

  function renderAll'''
js = regex_once(js, trial_card_pattern, trial_card_replacement, 'renderTrialCard')

billing_pattern = r"  function renderBilling\(\) \{.*?\n  \}\n\n  function renderSelectOptions"
billing_replacement = '''  function renderBilling() {
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
    $('#current-plan').innerHTML = `<div><span>${escapeHTML(statusText.toUpperCase())}</span><h2>${escapeHTML(headline)}</h2><p>${state.subscription?.cancel_at_period_end ? 'Cancelamento agendado para o fim do período.' : state.profile?.subscription_status === 'trialing' ? `Seu acesso atual segue exatamente as permissões do ${activePlan}.` : 'Você pode gerenciar cobrança e cancelamento no portal seguro.'}</p></div><div><small>Plano atual</small><strong>${escapeHTML(currentLabel)}</strong></div>`;
    $$('[data-billing-cycle]').forEach((button) => button.classList.toggle('active', button.dataset.billingCycle === billingCycle));
    $$('[data-price-monthly][data-price-annual]').forEach((price) => {
      const text = price.dataset[`price${billingCycle[0].toUpperCase()}${billingCycle.slice(1)}`];
      price.innerHTML = billingCycle === 'monthly' ? `${escapeHTML(text)}<small>/mês</small>` : escapeHTML(text);
    });
  }

  function renderSelectOptions'''
js = regex_once(js, billing_pattern, billing_replacement, 'renderBilling')

if "[data-start-trial]" not in js.split('function initStaticEvents()', 1)[-1]:
    js = replace_once(
        js,
        "    $$('[data-subscribe]').forEach((button) => button.addEventListener('click', () => subscribe(button.dataset.subscribe)));",
        "    $$('[data-start-trial]').forEach((button) => button.addEventListener('click', () => startTrial(button.dataset.startTrial, button)));\n    $('#trial-plan-logout')?.addEventListener('click', logout);\n    $$('[data-subscribe]').forEach((button) => button.addEventListener('click', () => subscribe(button.dataset.subscribe)));",
        'trial event listeners'
    )
APP_JS.write_text(js, encoding='utf-8')

# ---------- app/app.css ----------
css = CSS.read_text(encoding='utf-8')
if '/* selectable-trial-flow */' not in css:
    css += r'''

/* selectable-trial-flow */
.trial-choice-screen{min-height:100vh;background:radial-gradient(circle at 50% -15%,rgba(52,211,153,.13),transparent 38%),#f5f8fb;padding:32px 20px 56px;color:#0f172a}
.trial-choice-shell{width:min(1080px,100%);margin:0 auto}.trial-choice-brand{display:flex;align-items:center;justify-content:space-between;margin-bottom:62px}.trial-choice-brand .brand{color:#0f172a;text-decoration:none}.trial-choice-intro{text-align:center;max-width:780px;margin:0 auto 34px}.trial-choice-intro h1{margin:9px 0 14px;font:800 clamp(34px,5vw,56px)/1.02 Manrope,Inter,sans-serif;letter-spacing:-.045em}.trial-choice-intro>p{margin:0 auto;color:#64748b;font:500 16px/1.65 Inter,sans-serif;max-width:680px}.trial-choice-note{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:22px}.trial-choice-note span{padding:8px 11px;border:1px solid #dce5ec;background:#fff;border-radius:999px;color:#475569;font:650 12px Inter,sans-serif}
.trial-plan-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;max-width:900px;margin:0 auto}.trial-plan-card{position:relative;background:#fff;border:1px solid #dfe7ee;border-radius:24px;padding:28px;box-shadow:0 14px 40px rgba(15,23,42,.06);transition:.18s ease}.trial-plan-card:hover{transform:translateY(-2px);box-shadow:0 20px 50px rgba(15,23,42,.09)}.trial-plan-card.featured{border-color:#88e8c3;box-shadow:0 18px 54px rgba(16,185,129,.12)}.trial-plan-card.preferred{outline:3px solid rgba(52,211,153,.12)}.trial-recommended{position:absolute;right:20px;top:18px;padding:6px 9px;border-radius:999px;background:#e9fff7;color:#047857;font:800 10px Inter,sans-serif;letter-spacing:.06em}.trial-plan-top{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:17px}.trial-plan-name{font:800 20px Manrope,Inter,sans-serif}.trial-plan-top strong{font:800 25px Manrope,Inter,sans-serif;white-space:nowrap}.trial-plan-top small{display:block;margin-top:2px;color:#94a3b8;font:600 10px Inter,sans-serif;text-align:right}.trial-plan-card>p{min-height:66px;margin:0 0 18px;color:#64748b;font:500 13px/1.6 Inter,sans-serif}.trial-plan-card ul{list-style:none;padding:0;margin:0 0 24px;display:grid;gap:11px}.trial-plan-card li{position:relative;padding-left:22px;color:#334155;font:600 13px/1.45 Inter,sans-serif}.trial-plan-card li:before{content:'✓';position:absolute;left:0;color:#10b981;font-weight:900}.trial-choice-footnote{text-align:center;color:#7c8797;font:550 12px/1.5 Inter,sans-serif;margin:22px auto 0}
.continuation-card{width:min(820px,calc(100% - 28px));text-align:center}.continuation-icon{width:58px;height:58px;margin:0 auto 16px;border-radius:18px;background:#eafff7;color:#059669;display:grid;place-items:center;font-size:27px;font-weight:900}.continuation-card h1{max-width:650px;margin-left:auto;margin-right:auto}.continuation-card>p{max-width:650px;margin-left:auto;margin-right:auto}.continuation-context{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:22px auto;max-width:520px}.continuation-context>div{padding:14px 16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;text-align:left}.continuation-context small{display:block;color:#94a3b8;font:650 10px Inter,sans-serif;text-transform:uppercase;letter-spacing:.05em}.continuation-context strong{display:block;margin-top:4px;color:#0f172a;font:800 15px Manrope,Inter,sans-serif}.continuation-card .paywall-plans article{transition:.18s}.continuation-card .paywall-plans article.featured{border-color:#72ddb8;box-shadow:0 12px 34px rgba(16,185,129,.11)}.continuation-note{font-size:11px!important;color:#94a3b8!important;margin-top:14px!important}
@media(max-width:760px){.trial-choice-screen{padding:20px 14px 40px}.trial-choice-brand{margin-bottom:38px}.trial-plan-grid{grid-template-columns:1fr}.trial-plan-card{padding:23px}.trial-plan-card>p{min-height:0}.trial-choice-intro h1{font-size:38px}.continuation-context{grid-template-columns:1fr}.continuation-card .paywall-plans{grid-template-columns:1fr}}
'''
CSS.write_text(css, encoding='utf-8')

# ---------- runtime deletion copy ----------
runtime = RUNTIME.read_text(encoding='utf-8')
runtime = runtime.replace(
    'o teste grátis de 3 dias é concedido uma única vez por e-mail. Se você criar outra conta com este mesmo e-mail no futuro, o trial não será aplicado novamente.',
    'se este e-mail já iniciou um período de experiência, ele não poderá receber outro no futuro. Excluir uma conta antes de escolher um plano não consome o direito ao teste.'
)
RUNTIME.write_text(runtime, encoding='utf-8')

# ---------- privacy copy ----------
privacy = PRIVACY.read_text(encoding='utf-8')
privacy = privacy.replace(
    'um identificador criptográfico irreversível derivado do e-mail, usado exclusivamente para registrar se aquele e-mail já recebeu o teste gratuito.',
    'quando um período de experiência é iniciado, um identificador criptográfico irreversível derivado do e-mail, usado exclusivamente para registrar que aquele e-mail já utilizou essa experiência.'
)
privacy = privacy.replace(
    'Para impedir múltiplas concessões do teste gratuito, após a exclusão podemos conservar o identificador criptográfico irreversível derivado do e-mail.',
    'Para impedir múltiplas concessões do período de experiência, quando o teste é iniciado podemos conservar o identificador criptográfico irreversível derivado do e-mail mesmo após a exclusão da conta.'
)
PRIVACY.write_text(privacy, encoding='utf-8')

# ---------- CI ----------
check = CHECK.read_text(encoding='utf-8')
if '006_trial_once_per_email.sql' not in check:
    check = replace_once(check, '          test -f salesboard/supabase/005_lock_entitlement_rpc.sql\n', '          test -f salesboard/supabase/005_lock_entitlement_rpc.sql\n          test -f salesboard/supabase/006_trial_once_per_email.sql\n          test -f salesboard/supabase/007_choose_trial_plan_once.sql\n', 'migration checks')
if 'start_salesboard_trial' not in check:
    check = replace_once(check, "          grep -Fq 'google-auth-button' salesboard/app/index.html\n", "          grep -Fq 'google-auth-button' salesboard/app/index.html\n          grep -Fq 'trial-plan-screen' salesboard/app/index.html\n          grep -Fq 'data-start-trial=\"essential\"' salesboard/app/index.html\n          grep -Fq 'data-start-trial=\"pro\"' salesboard/app/index.html\n          grep -Fq 'start_salesboard_trial' salesboard/app/app.js\n          grep -Fq 'salesboard_trial_eligible' salesboard/app/app.js\n          grep -Fq \"return profile.plan === 'essential' ? 'essential' : 'pro'\" salesboard/app/app.js\n          grep -Fq 'start_salesboard_trial' salesboard/supabase/007_choose_trial_plan_once.sql\n", 'trial flow CI checks')
CHECK.write_text(check, encoding='utf-8')

print('Selectable trial plan flow patched successfully.')
