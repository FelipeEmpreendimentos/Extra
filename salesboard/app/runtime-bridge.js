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
