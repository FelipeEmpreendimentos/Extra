(() => {
  'use strict';

  const projectUrl = 'https://azjabgqvkkctgzqacpue.supabase.co';
  const publishableKey = 'sb_publishable_mJ2Hk9XjmGl8RhqCkPzi9w_dq3sqWWF';
  const functionsBase = `${projectUrl}/functions/v1`;
  const nativeFetch = window.fetch.bind(window);

  window.SALESBOARD_RUNTIME = Object.freeze({ projectUrl, publishableKey, functionsBase });

  function jsonResponse(body, status = 200) {
    return new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }
    });
  }

  function normalizeUrl(input) {
    if (typeof input === 'string') return input;
    if (input instanceof URL) return input.href;
    return input?.url || '';
  }

  function apiRoute(url) {
    try { return new URL(url, location.href).pathname; }
    catch { return url; }
  }

  function proxyHeaders(initHeaders) {
    const headers = new Headers(initHeaders || {});
    headers.set('apikey', publishableKey);
    headers.set('Accept', 'application/json');
    return headers;
  }

  window.fetch = async (input, init = {}) => {
    const url = normalizeUrl(input);
    const path = apiRoute(url);

    if (path === '/api/config') {
      return jsonResponse({
        configured: true,
        supabaseUrl: projectUrl,
        supabasePublishableKey: publishableKey,
        appName: 'SalesBoard Finance',
        supportEmail: '',
        privacyEmail: '',
        legalEntityName: '',
        legalEntityId: '',
        backend: 'supabase-edge'
      });
    }

    const routes = {
      '/api/checkout': 'salesboard-checkout',
      '/api/billing-portal': 'salesboard-billing-portal',
      '/api/delete-account': 'salesboard-delete-account',
      '/api/health': 'salesboard-health'
    };

    const functionName = routes[path];
    if (functionName) {
      const headers = proxyHeaders(init.headers || (input instanceof Request ? input.headers : undefined));
      return nativeFetch(`${functionsBase}/${functionName}`, { ...init, headers });
    }

    return nativeFetch(input, init);
  };
})();

(() => {
  'use strict';

  const MONEY_SELECTOR = '.money-field input';
  const MAX_CENT_DIGITS = 11;
  const allowedControlKeys = new Set([
    'Backspace', 'Delete', 'Tab', 'Enter', 'Escape',
    'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'
  ]);

  function onlyDigits(value) { return String(value ?? '').replace(/\D/g, ''); }

  function formatImplicitCents(value) {
    let digits = onlyDigits(value);
    digits = digits.replace(/^0+(?=\d)/, '');
    if (!digits) digits = '0';
    if (digits.length > MAX_CENT_DIGITS) digits = digits.slice(0, MAX_CENT_DIGITS);
    const padded = digits.padStart(3, '0');
    const cents = padded.slice(-2);
    let integer = padded.slice(0, -2).replace(/^0+(?=\d)/, '') || '0';
    integer = integer.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    return `${integer},${cents}`;
  }

  function moveCaretToEnd(input) {
    requestAnimationFrame(() => {
      try {
        const end = input.value.length;
        input.setSelectionRange(end, end);
      } catch {}
    });
  }

  function configureMoneyInput(input) {
    if (!(input instanceof HTMLInputElement) || !input.matches(MONEY_SELECTOR)) return;
    input.type = 'text';
    input.inputMode = 'numeric';
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.maxLength = 14;
    input.setAttribute('pattern', '[0-9]*');
    input.setAttribute('data-money-input', 'implicit-cents');
    input.style.fontVariantNumeric = 'tabular-nums';
    input.value = formatImplicitCents(input.value);
  }

  function configureMoneyInputs(root = document) {
    if (root instanceof HTMLInputElement && root.matches(MONEY_SELECTOR)) configureMoneyInput(root);
    if (root?.querySelectorAll) root.querySelectorAll(MONEY_SELECTOR).forEach(configureMoneyInput);
  }

  configureMoneyInputs(document);

  document.addEventListener('keydown', (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || !input.matches(MONEY_SELECTOR)) return;
    const command = event.ctrlKey || event.metaKey;
    if (command && ['a', 'c', 'v', 'x', 'z', 'y'].includes(event.key.toLowerCase())) return;
    if (allowedControlKeys.has(event.key)) return;
    if (/^\d$/.test(event.key)) {
      if (!(input.selectionStart === 0 && input.selectionEnd === input.value.length)) {
        try {
          const end = input.value.length;
          input.setSelectionRange(end, end);
        } catch {}
      }
      return;
    }
    event.preventDefault();
  });

  document.addEventListener('beforeinput', (event) => {
    const input = event.target;
    if (input instanceof HTMLInputElement && input.matches(MONEY_SELECTOR) && event.inputType === 'insertText' && event.data && /\D/.test(event.data)) event.preventDefault();
  });

  document.addEventListener('input', (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || !input.matches(MONEY_SELECTOR)) return;
    input.value = formatImplicitCents(input.value);
    moveCaretToEnd(input);
  });

  document.addEventListener('paste', (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || !input.matches(MONEY_SELECTOR)) return;
    event.preventDefault();
    input.value = formatImplicitCents(event.clipboardData?.getData('text') || '');
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });

  document.addEventListener('focusin', (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || !input.matches(MONEY_SELECTOR)) return;
    configureMoneyInput(input);
    moveCaretToEnd(input);
  });

  document.addEventListener('click', (event) => {
    const input = event.target;
    if (input instanceof HTMLInputElement && input.matches(MONEY_SELECTOR)) moveCaretToEnd(input);
  });

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) mutation.addedNodes.forEach((node) => {
      if (node instanceof Element) configureMoneyInputs(node);
    });
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();

(() => {
  'use strict';

  const { projectUrl, publishableKey } = window.SALESBOARD_RUNTIME;
  let modal = null;
  let deleting = false;

  function ensureStyles() {
    if (document.getElementById('sb-delete-account-styles')) return;
    const style = document.createElement('style');
    style.id = 'sb-delete-account-styles';
    style.textContent = `
      .sb-delete-overlay{position:fixed;inset:0;z-index:99999;background:rgba(2,8,23,.62);backdrop-filter:blur(7px);display:grid;place-items:center;padding:20px;animation:sbFade .16s ease}
      .sb-delete-dialog{width:min(520px,100%);background:#fff;border:1px solid #e2e8f0;border-radius:24px;box-shadow:0 28px 90px rgba(2,8,23,.28);overflow:hidden;animation:sbPop .18s ease}
      .sb-delete-head{padding:26px 28px 18px;display:flex;gap:16px;align-items:flex-start}.sb-delete-icon{width:48px;height:48px;flex:0 0 48px;border-radius:15px;display:grid;place-items:center;background:#fff1f2;color:#dc2626;font-size:23px;font-weight:900}
      .sb-delete-head h2{margin:1px 0 7px;color:#0f172a;font:800 22px/1.18 Manrope,Inter,sans-serif}.sb-delete-head p{margin:0;color:#64748b;font:500 14px/1.55 Inter,sans-serif}
      .sb-delete-body{padding:0 28px 26px}.sb-delete-list{margin:0 0 20px;padding:17px 18px;list-style:none;background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;display:grid;gap:11px}.sb-delete-list li{display:flex;gap:10px;color:#334155;font:550 13px/1.45 Inter,sans-serif}.sb-delete-list li:before{content:'•';color:#dc2626;font-weight:900}
      .sb-delete-trial{margin:0 0 20px;padding:13px 15px;border:1px solid #fecaca;background:#fff7f7;border-radius:13px;color:#991b1b;font:650 13px/1.48 Inter,sans-serif}
      .sb-delete-label{display:block;color:#334155;font:700 13px/1.4 Inter,sans-serif}.sb-delete-label b{color:#0f172a}.sb-delete-input{width:100%;box-sizing:border-box;margin-top:8px;padding:13px 14px;border:1px solid #cbd5e1;border-radius:12px;background:#fff;color:#0f172a;font:650 14px Inter,sans-serif;outline:none;transition:.15s}.sb-delete-input:focus{border-color:#ef4444;box-shadow:0 0 0 3px rgba(239,68,68,.1)}
      .sb-delete-status{min-height:20px;margin-top:9px;color:#dc2626;font:600 12px/1.4 Inter,sans-serif}.sb-delete-actions{padding:18px 28px 24px;border-top:1px solid #e2e8f0;display:flex;justify-content:flex-end;gap:10px;background:#fbfdff}
      .sb-delete-btn{border:0;border-radius:12px;padding:12px 17px;font:750 13px Inter,sans-serif;cursor:pointer;transition:.15s}.sb-delete-cancel{background:#eef2f7;color:#334155}.sb-delete-confirm{background:#dc2626;color:#fff;box-shadow:0 6px 18px rgba(220,38,38,.18)}.sb-delete-confirm:disabled{background:#cbd5e1;color:#64748b;box-shadow:none;cursor:not-allowed}.sb-delete-btn:not(:disabled):hover{transform:translateY(-1px)}
      @keyframes sbFade{from{opacity:0}to{opacity:1}}@keyframes sbPop{from{opacity:0;transform:translateY(8px) scale(.985)}to{opacity:1;transform:none}}
      @media(max-width:560px){.sb-delete-overlay{padding:12px;align-items:end}.sb-delete-dialog{border-radius:22px}.sb-delete-head,.sb-delete-body{padding-left:20px;padding-right:20px}.sb-delete-actions{padding:16px 20px}.sb-delete-actions .sb-delete-btn{flex:1}}
    `;
    document.head.appendChild(style);
  }

  function closeModal() {
    if (deleting || !modal) return;
    modal.remove();
    modal = null;
  }

  function openModal() {
    if (modal) return;
    ensureStyles();
    modal = document.createElement('div');
    modal.className = 'sb-delete-overlay';
    modal.innerHTML = `
      <div class="sb-delete-dialog" role="dialog" aria-modal="true" aria-labelledby="sb-delete-title">
        <div class="sb-delete-head">
          <div class="sb-delete-icon">!</div>
          <div><h2 id="sb-delete-title">Excluir conta permanentemente?</h2><p>Essa ação não pode ser desfeita. Revise o que acontecerá antes de confirmar.</p></div>
        </div>
        <div class="sb-delete-body">
          <ul class="sb-delete-list">
            <li>Contas, categorias, lançamentos, metas e demais dados financeiros serão apagados.</li>
            <li>Se houver uma assinatura ativa, ela será cancelada antes da exclusão.</li>
            <li>Você perderá o acesso ao histórico e às configurações deste espaço.</li>
          </ul>
          <div class="sb-delete-trial"><strong>Importante:</strong> o teste grátis de 3 dias é concedido uma única vez por e-mail. Se você criar outra conta com este mesmo e-mail no futuro, o trial não será aplicado novamente.</div>
          <label class="sb-delete-label">Para confirmar, digite <b>EXCLUIR</b>
            <input class="sb-delete-input" id="sb-delete-confirmation" autocomplete="off" spellcheck="false" placeholder="EXCLUIR" />
          </label>
          <div class="sb-delete-status" id="sb-delete-status" aria-live="polite"></div>
        </div>
        <div class="sb-delete-actions">
          <button type="button" class="sb-delete-btn sb-delete-cancel">Manter minha conta</button>
          <button type="button" class="sb-delete-btn sb-delete-confirm" disabled>Excluir permanentemente</button>
        </div>
      </div>`;
    document.body.appendChild(modal);

    const input = modal.querySelector('#sb-delete-confirmation');
    const confirm = modal.querySelector('.sb-delete-confirm');
    const cancel = modal.querySelector('.sb-delete-cancel');
    const status = modal.querySelector('#sb-delete-status');

    input.addEventListener('input', () => {
      input.value = input.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 7);
      confirm.disabled = input.value !== 'EXCLUIR' || deleting;
      status.textContent = '';
    });
    cancel.addEventListener('click', closeModal);
    modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(); });

    confirm.addEventListener('click', async () => {
      if (input.value !== 'EXCLUIR' || deleting) return;
      deleting = true;
      confirm.disabled = true;
      cancel.disabled = true;
      input.disabled = true;
      confirm.textContent = 'Excluindo...';
      status.textContent = 'Cancelando cobrança e removendo seus dados com segurança...';
      status.style.color = '#64748b';

      try {
        if (!window.supabase?.createClient) throw new Error('Serviço de autenticação indisponível. Atualize a página e tente novamente.');
        const client = window.supabase.createClient(projectUrl, publishableKey, {
          auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
        });
        const { data, error } = await client.auth.getSession();
        if (error || !data?.session?.access_token) throw new Error('Sua sessão expirou. Entre novamente antes de excluir a conta.');

        const response = await fetch('/api/delete-account', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${data.session.access_token}` },
          body: JSON.stringify({ confirmation: 'EXCLUIR' })
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.error || 'Não foi possível excluir a conta.');

        try { await client.auth.signOut({ scope: 'local' }); } catch {}
        localStorage.removeItem(`sb-${new URL(projectUrl).hostname.split('.')[0]}-auth-token`);
        location.replace('../?account=deleted');
      } catch (error) {
        deleting = false;
        confirm.disabled = input.value !== 'EXCLUIR';
        cancel.disabled = false;
        input.disabled = false;
        confirm.textContent = 'Excluir permanentemente';
        status.style.color = '#dc2626';
        status.textContent = error?.message || 'Não foi possível excluir a conta.';
      }
    });

    setTimeout(() => input.focus(), 60);
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal) closeModal();
  });

  document.addEventListener('click', (event) => {
    const button = event.target instanceof Element ? event.target.closest('#delete-account') : null;
    if (!button) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (new URLSearchParams(location.search).get('demo') === '1') return;
    openModal();
  }, true);
})();
