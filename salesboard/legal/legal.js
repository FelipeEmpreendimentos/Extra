(() => {
  'use strict';

  const $$ = (selector) => [...document.querySelectorAll(selector)];

  function applyText(selector, value, fallback) {
    $$(selector).forEach((element) => {
      element.textContent = value || fallback;
    });
  }

  function applyMail(selector, email, fallback) {
    $$(selector).forEach((element) => {
      const value = email || fallback;
      element.textContent = value;
      if (element.tagName === 'A' && email) element.href = `mailto:${email}`;
    });
  }

  async function loadConfig() {
    try {
      const response = await fetch('/api/config', { headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error('config unavailable');
      const config = await response.json();
      applyText('[data-legal-name]', config.legalEntityName, '[RESPONSÁVEL LEGAL A CONFIGURAR]');
      applyText('[data-legal-id]', config.legalEntityId, '[CPF/CNPJ A CONFIGURAR]');
      applyMail('[data-support-email]', config.supportEmail, '[E-MAIL DE SUPORTE A CONFIGURAR]');
      applyMail('[data-privacy-email]', config.privacyEmail, '[E-MAIL DE PRIVACIDADE A CONFIGURAR]');

      const missingLegal = !config.legalEntityName || !config.legalEntityId || !config.supportEmail || !config.privacyEmail;
      const warning = document.querySelector('#legal-config-warning');
      if (warning) warning.hidden = !missingLegal;
    } catch {
      const warning = document.querySelector('#legal-config-warning');
      if (warning) warning.hidden = false;
    }
  }

  loadConfig();
})();
