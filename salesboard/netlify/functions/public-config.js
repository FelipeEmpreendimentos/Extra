'use strict';

const { json } = require('./_shared');

exports.handler = async (event) => {
  if (event.httpMethod !== 'GET') {
    return json(405, { error: 'Método não permitido.' }, { Allow: 'GET' });
  }

  const required = ['SUPABASE_URL', 'SUPABASE_PUBLISHABLE_KEY'];
  const missing = required.filter((name) => !process.env[name]);

  return json(200, {
    configured: missing.length === 0,
    missing,
    appName: process.env.APP_NAME || 'SalesBoard Finance',
    supabaseUrl: process.env.SUPABASE_URL || '',
    supabasePublishableKey: process.env.SUPABASE_PUBLISHABLE_KEY || '',
    supportEmail: process.env.SUPPORT_EMAIL || '',
    privacyEmail: process.env.PRIVACY_EMAIL || process.env.SUPPORT_EMAIL || '',
    legalEntityName: process.env.LEGAL_ENTITY_NAME || '',
    legalEntityId: process.env.LEGAL_ENTITY_ID || '',
    environment: process.env.CONTEXT || 'local'
  });
};
