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
    input.removeAttribute('pattern');
    input.removeAttribute('step');
    input.removeAttribute('min');
    input.removeAttribute('max');
    input.setCustomValidity('');
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

// SB_MODAL_SYSTEM_V2
(() => {
  'use strict';

  const modalSelector = '.modal';
  const formSelector = '.modal form';

  function visibleField(field) {
    if (!(field instanceof HTMLElement) || field.disabled) return false;
    if (field.closest('[hidden]')) return false;
    return true;
  }

  function fieldContainer(field) {
    return field.closest('label') || field.closest('.field') || field.parentElement;
  }

  function clearFieldError(field) {
    if (!(field instanceof HTMLElement)) return;
    field.removeAttribute('aria-invalid');
    const container = fieldContainer(field);
    if (!container) return;
    container.classList.remove('sb-field-invalid');
    const error = container.querySelector(':scope > .sb-field-error');
    if (error) error.remove();
  }

  function setFieldError(field, message) {
    const container = fieldContainer(field);
    if (!container) return;
    clearFieldError(field);
    container.classList.add('sb-field-invalid');
    field.setAttribute('aria-invalid', 'true');
    const error = document.createElement('small');
    error.className = 'sb-field-error';
    error.setAttribute('role', 'alert');
    error.textContent = message;
    container.appendChild(error);
  }

  function valueMissing(field, form) {
    if (!field.required || !visibleField(field)) return false;
    const type = String(field.type || '').toLowerCase();
    if (type === 'checkbox') return !field.checked;
    if (type === 'radio') {
      if (!field.name) return !field.checked;
      return !form.querySelector(`input[type="radio"][name="${CSS.escape(field.name)}"]:checked`);
    }
    return String(field.value ?? '').trim() === '';
  }

  function validateModalForm(form) {
    form.querySelectorAll('.sb-field-error').forEach((node) => node.remove());
    form.querySelectorAll('.sb-field-invalid').forEach((node) => node.classList.remove('sb-field-invalid'));
    form.querySelectorAll('[aria-invalid="true"]').forEach((node) => node.removeAttribute('aria-invalid'));

    let firstInvalid = null;
    const required = [...form.querySelectorAll('[required]')];
    for (const field of required) {
      if (valueMissing(field, form)) {
        setFieldError(field, field.type === 'checkbox' ? 'Confirme esta opção para continuar.' : 'Preencha este campo para continuar.');
        firstInvalid ||= field;
      }
    }

    const transactionAmount = form.querySelector('#tx-amount, [name="amount"]');
    if (transactionAmount && visibleField(transactionAmount)) {
      const digits = String(transactionAmount.value || '').replace(/\D/g, '');
      if (!digits || Number(digits) <= 0) {
        setFieldError(transactionAmount, 'Informe um valor maior que zero.');
        firstInvalid ||= transactionAmount;
      }
    }

    if (firstInvalid) {
      firstInvalid.focus({ preventScroll: true });
      firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return false;
    }
    return true;
  }

  function prepareForm(form) {
    if (!(form instanceof HTMLFormElement)) return;
    form.noValidate = true;
    form.setAttribute('novalidate', 'novalidate');
    form.querySelectorAll('.money-field input').forEach((input) => {
      input.type = 'text';
      input.inputMode = 'numeric';
      input.removeAttribute('pattern');
      input.removeAttribute('step');
      input.removeAttribute('min');
      input.removeAttribute('max');
      input.setCustomValidity('');
    });
  }

  function enhanceModal(modal) {
    if (!(modal instanceof HTMLElement) || !modal.matches(modalSelector)) return;
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.querySelectorAll('form').forEach(prepareForm);
    modal.querySelectorAll('[data-close-modal]').forEach((button) => {
      if (button instanceof HTMLButtonElement) button.type = 'button';
      if (!button.getAttribute('aria-label')) button.setAttribute('aria-label', 'Fechar janela');
    });
  }

  function focusOpenedModal(modal) {
    if (modal.hidden) return;
    requestAnimationFrame(() => {
      const target = modal.querySelector('[autofocus], input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled])');
      target?.focus({ preventScroll: true });
    });
  }

  document.querySelectorAll(modalSelector).forEach((modal) => {
    enhanceModal(modal);
    if (!modal.hidden) focusOpenedModal(modal);
  });

  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.matches(formSelector)) return;
    prepareForm(form);
    if (!validateModalForm(form)) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);

  document.addEventListener('input', (event) => {
    const field = event.target;
    if (field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement) clearFieldError(field);
  }, true);

  document.addEventListener('change', (event) => {
    const field = event.target;
    if (field instanceof HTMLInputElement || field instanceof HTMLSelectElement) clearFieldError(field);
  }, true);

  document.addEventListener('invalid', (event) => {
    const field = event.target;
    if (!(field instanceof HTMLElement) || !field.closest('.modal')) return;
    event.preventDefault();
  }, true);

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const modal = [...document.querySelectorAll(modalSelector)].reverse().find((item) => !item.hidden);
    const close = modal?.querySelector('[data-close-modal]');
    close?.click();
  });

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === 'attributes' && mutation.target instanceof HTMLElement && mutation.target.matches(modalSelector)) {
        enhanceModal(mutation.target);
        if (!mutation.target.hidden) focusOpenedModal(mutation.target);
      }
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof Element)) return;
        if (node.matches(modalSelector)) {
          enhanceModal(node);
          if (!node.hidden) focusOpenedModal(node);
        }
        node.querySelectorAll?.(modalSelector).forEach(enhanceModal);
        node.querySelectorAll?.(formSelector).forEach(prepareForm);
      });
    }
  });

  observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden'] });
})();
