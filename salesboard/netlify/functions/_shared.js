'use strict';

const { createClient } = require('@supabase/supabase-js');

function json(statusCode, payload, extraHeaders = {}) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      ...extraHeaders
    },
    body: JSON.stringify(payload)
  };
}

function requireEnv(names) {
  const missing = names.filter((name) => !process.env[name]);
  if (missing.length) {
    const error = new Error(`Configuração ausente: ${missing.join(', ')}`);
    error.code = 'CONFIG_MISSING';
    error.missing = missing;
    throw error;
  }
}

function getAdminClient() {
  requireEnv(['SUPABASE_URL', 'SUPABASE_SECRET_KEY']);
  return createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SECRET_KEY, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
      detectSessionInUrl: false
    }
  });
}

function bearerToken(event) {
  const header = event.headers?.authorization || event.headers?.Authorization || '';
  const match = /^Bearer\s+(.+)$/i.exec(header);
  return match?.[1] || null;
}

async function verifyUser(event) {
  const token = bearerToken(event);
  if (!token) {
    const error = new Error('Sessão não encontrada.');
    error.code = 'UNAUTHORIZED';
    throw error;
  }

  const admin = getAdminClient();
  const { data, error } = await admin.auth.getUser(token);
  if (error || !data?.user) {
    const authError = new Error('Sessão inválida ou expirada.');
    authError.code = 'UNAUTHORIZED';
    throw authError;
  }

  return { user: data.user, token, admin };
}

function requestOrigin(event) {
  const configured = process.env.URL;
  if (configured) return configured.replace(/\/$/, '');

  const origin = event.headers?.origin;
  if (origin) return origin.replace(/\/$/, '');

  const host = event.headers?.['x-forwarded-host'] || event.headers?.host;
  const proto = event.headers?.['x-forwarded-proto'] || 'https';
  return host ? `${proto}://${host}` : 'http://localhost:8888';
}

function safeError(error) {
  if (error?.code === 'UNAUTHORIZED') return json(401, { error: error.message });
  if (error?.code === 'CONFIG_MISSING') return json(503, { error: 'Ambiente de produção ainda não configurado.', missing: error.missing });
  console.error(error);
  return json(500, { error: 'Não foi possível concluir a solicitação.' });
}

module.exports = {
  json,
  requireEnv,
  getAdminClient,
  verifyUser,
  requestOrigin,
  safeError
};
