(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  let billingCycle = 'monthly';

  function initMobileMenu() {
    const button = $('#mobile-menu-btn');
    const menu = $('#mobile-menu');
    if (!button || !menu) return;

    button.addEventListener('click', () => {
      const open = menu.hidden;
      menu.hidden = !open;
      button.setAttribute('aria-expanded', String(open));
    });

    $$('#mobile-menu a').forEach((link) => {
      link.addEventListener('click', () => {
        menu.hidden = true;
        button.setAttribute('aria-expanded', 'false');
      });
    });
  }

  function initBillingToggle() {
    const buttons = $$('[data-billing]');
    if (!buttons.length) return;

    buttons.forEach((button) => {
      button.addEventListener('click', () => {
        billingCycle = button.dataset.billing;
        buttons.forEach((item) => item.classList.toggle('active', item === button));

        $$('[data-monthly][data-annual]').forEach((price) => {
          price.textContent = price.dataset[billingCycle];
        });

        $$('.plan-link[data-plan]').forEach((link) => {
          const url = new URL(link.href);
          url.searchParams.set('billing', billingCycle);
          link.href = url.href;
        });
      });
    });
  }

  function initFaq() {
    $$('.faq-list details').forEach((details) => {
      details.addEventListener('toggle', () => {
        if (!details.open) return;
        $$('.faq-list details').forEach((other) => {
          if (other !== details) other.open = false;
        });
      });
    });
  }

  function initHeader() {
    const header = $('#marketing-header');
    if (!header) return;
    const sync = () => header.classList.toggle('scrolled', window.scrollY > 20);
    sync();
    window.addEventListener('scroll', sync, { passive: true });
  }

  function initProductionLinks() {
    // GitHub Pages is the public demonstration. Authentication/billing run on the production host.
    if (!location.hostname.endsWith('github.io')) return;

    $$('a[href^="app/?mode="]').forEach((link) => {
      const original = new URL(link.href);
      const demo = new URL('app/', location.href);
      demo.searchParams.set('demo', '1');
      if (original.searchParams.get('plan')) demo.searchParams.set('plan', original.searchParams.get('plan'));
      demo.searchParams.set('billing', original.searchParams.get('billing') || billingCycle);
      link.href = demo.href;
      link.title = 'No GitHub Pages, este botão abre a demonstração. O cadastro real roda no ambiente de produção.';
    });
  }

  function initSmoothAnchors() {
    $$('a[href^="#"]').forEach((link) => {
      link.addEventListener('click', (event) => {
        const target = $(link.getAttribute('href'));
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  initMobileMenu();
  initBillingToggle();
  initFaq();
  initHeader();
  initProductionLinks();
  initSmoothAnchors();
})();
