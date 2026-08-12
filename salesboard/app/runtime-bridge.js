(() => {
  'use strict';

  const projectUrl = 'https://azjabgqvkkctgzqacpue.supabase.co';
  const publishableKey = 'sb_publishable_mJ2Hk9XjmGl8RhqCkPzi9w_dq3sqWWF';
  const functionsBase = `${projectUrl}/functions/v1`;
  const nativeFetch = window.fetch.bind(window);

  window.SALESBOARD_RUNTIME = Object.freeze({
    projectUrl,
    publishableKey,
    functionsBase
  });

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
    try {
      const parsed = new URL(url, location.href);
      return parsed.pathname;
    } catch {
      return url;
    }
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
      const proxiedInit = { ...init, headers };
      return nativeFetch(`${functionsBase}/${functionName}`, proxiedInit);
    }

    return nativeFetch(input, init);
  };
})();

(() => {
  'use strict';

  const MONEY_SELECTOR = '.money-field input';
  // Database constraints allow values up to 999,999,999.99.
  const MAX_CENT_DIGITS = 11;
  const allowedControlKeys = new Set([
    'Backspace', 'Delete', 'Tab', 'Enter', 'Escape',
    'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
    'Home', 'End'
  ]);

  function onlyDigits(value) {
    return String(value ?? '').replace(/\D/g, '');
  }

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
      } catch {
        // Some browsers/input implementations do not expose selection APIs.
      }
    });
  }

  function configureMoneyInput(input) {
    if (!(input instanceof HTMLInputElement) || !input.matches(MONEY_SELECTOR)) return;
    input.type = 'text';
    input.inputMode = 'numeric';
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.maxLength = 14; // 999.999.999,99
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
      // Monetary typing behaves like a calculator: new digits always enter from the right.
      if (!(input.selectionStart === 0 && input.selectionEnd === input.value.length)) {
        try {
          const end = input.value.length;
          input.setSelectionRange(end, end);
        } catch {
          // Ignore selection API failures.
        }
      }
      return;
    }

    // Comma, dot, minus sign, letters and other symbols are never typed manually.
    event.preventDefault();
  });

  document.addEventListener('beforeinput', (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || !input.matches(MONEY_SELECTOR)) return;
    if (event.inputType === 'insertText' && event.data && /\D/.test(event.data)) event.preventDefault();
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
    const pasted = event.clipboardData?.getData('text') || '';
    input.value = formatImplicitCents(pasted);
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

  // Entity fields (accounts, categories and goals) are rendered dynamically.
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      mutation.addedNodes.forEach((node) => {
        if (node instanceof Element) configureMoneyInputs(node);
      });
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
