import { createClient } from '@supabase/supabase-js';

export const config = {
  schedule: '0 8 * * *'
};

function parseDate(value) {
  const [year, month, day] = String(value).split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function daysInMonth(year, monthIndex) {
  return new Date(Date.UTC(year, monthIndex + 1, 0)).getUTCDate();
}

function addInterval(date, interval) {
  const source = new Date(date.getTime());
  if (interval === 'weekly') {
    source.setUTCDate(source.getUTCDate() + 7);
    return source;
  }

  if (interval === 'yearly') {
    const targetYear = source.getUTCFullYear() + 1;
    const month = source.getUTCMonth();
    const day = Math.min(source.getUTCDate(), daysInMonth(targetYear, month));
    return new Date(Date.UTC(targetYear, month, day));
  }

  const targetMonthAbsolute = source.getUTCFullYear() * 12 + source.getUTCMonth() + 1;
  const targetYear = Math.floor(targetMonthAbsolute / 12);
  const targetMonth = targetMonthAbsolute % 12;
  const day = Math.min(source.getUTCDate(), daysInMonth(targetYear, targetMonth));
  return new Date(Date.UTC(targetYear, targetMonth, day));
}

function hasProAccess(profile, now) {
  if (!profile) return false;
  if (profile.subscription_status === 'active' && profile.plan === 'pro') return true;
  return profile.subscription_status === 'trialing' && profile.trial_ends_at && new Date(profile.trial_ends_at) > now;
}

export default async () => {
  const required = ['SUPABASE_URL', 'SUPABASE_SECRET_KEY'];
  const missing = required.filter((name) => !process.env[name]);
  if (missing.length) {
    console.error('Recurring processor configuration missing:', missing.join(', '));
    return new Response(null, { status: 503 });
  }

  const admin = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SECRET_KEY, {
    auth: { autoRefreshToken: false, persistSession: false }
  });

  const { data: sources, error: sourceError } = await admin
    .from('transactions')
    .select('id,user_id,account_id,category_id,type,description,amount,transaction_date,status,recurrence_interval,notes')
    .eq('recurring', true)
    .is('recurrence_source_id', null)
    .not('recurrence_interval', 'is', null)
    .limit(1000);

  if (sourceError) {
    console.error('Recurring source query failed:', sourceError);
    return new Response(null, { status: 500 });
  }

  if (!sources?.length) return new Response(null, { status: 204 });

  const userIds = [...new Set(sources.map((source) => source.user_id))];
  const sourceIds = sources.map((source) => source.id);

  const [{ data: profiles, error: profileError }, { data: generated, error: generatedError }] = await Promise.all([
    admin.from('profiles').select('id,plan,subscription_status,trial_ends_at').in('id', userIds),
    admin.from('transactions').select('recurrence_source_id,transaction_date').in('recurrence_source_id', sourceIds)
  ]);

  if (profileError || generatedError) {
    console.error('Recurring lookup failed:', profileError || generatedError);
    return new Response(null, { status: 500 });
  }

  const profileMap = new Map((profiles || []).map((profile) => [profile.id, profile]));
  const existing = new Set((generated || []).map((row) => `${row.recurrence_source_id}|${row.transaction_date}`));
  const now = new Date();
  const today = parseDate(formatDate(now));
  const inserts = [];

  for (const source of sources) {
    if (!hasProAccess(profileMap.get(source.user_id), now)) continue;
    if (!['weekly', 'monthly', 'yearly'].includes(source.recurrence_interval)) continue;

    let occurrence = addInterval(parseDate(source.transaction_date), source.recurrence_interval);
    let guard = 0;

    while (occurrence <= today && guard < 520) {
      const occurrenceDate = formatDate(occurrence);
      const uniqueKey = `${source.id}|${occurrenceDate}`;

      if (!existing.has(uniqueKey)) {
        inserts.push({
          user_id: source.user_id,
          account_id: source.account_id,
          category_id: source.category_id,
          type: source.type,
          description: source.description,
          amount: source.amount,
          transaction_date: occurrenceDate,
          status: 'pending',
          recurring: false,
          recurrence_interval: null,
          recurrence_source_id: source.id,
          notes: source.notes ? `${source.notes}\nGerado automaticamente a partir de uma recorrência.` : 'Gerado automaticamente a partir de uma recorrência.'
        });
        existing.add(uniqueKey);
      }

      occurrence = addInterval(occurrence, source.recurrence_interval);
      guard += 1;
    }
  }

  if (!inserts.length) return new Response(null, { status: 204 });

  const { error: insertError } = await admin.from('transactions').insert(inserts);
  if (insertError && insertError.code !== '23505') {
    console.error('Recurring insert failed:', insertError);
    return new Response(null, { status: 500 });
  }

  console.log(`Recurring processor generated ${inserts.length} pending occurrence(s).`);
  return new Response(null, { status: 204 });
};
