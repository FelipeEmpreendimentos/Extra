import { createClient } from 'npm:@supabase/supabase-js@2.111.0'

const PROD_ORIGIN = 'https://felipeempreendimentos.github.io'
const TEST_CATALOG = {
  essentialProduct: 'prod_V3mP62OMS5pAmt',
  proProduct: 'prod_V3mPwwBjaVkm8E',
  essentialPrices: ['price_1U3eqnRlODNbnkUiLRDXlIZm', 'price_1U3erCRlODNbnkUiYSxDq1e6'],
  proPrices: ['price_1U3eqyRlODNbnkUirbXIqvR8', 'price_1U3erNRlODNbnkUiCYny1NeZ']
}

function allowedOrigin(req: Request) {
  const origin = req.headers.get('origin') || ''
  if (origin === PROD_ORIGIN || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)) return origin
  return PROD_ORIGIN
}
function cors(req: Request) { return { 'Access-Control-Allow-Origin': allowedOrigin(req), 'Access-Control-Allow-Headers': 'authorization, apikey, content-type', 'Access-Control-Allow-Methods': 'POST, OPTIONS', 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'Vary': 'Origin' } }
function adminClient() { const url=Deno.env.get('SUPABASE_URL')!; const legacy=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'); const modern=Deno.env.get('SUPABASE_SECRET_KEYS'); const key=legacy||(modern?JSON.parse(modern).default:''); if(!url||!key) throw new Error('SUPABASE_NOT_CONFIGURED'); return createClient(url,key,{auth:{persistSession:false,autoRefreshToken:false}}) }
function stripeSecret(){const secret=Deno.env.get('STRIPE_SECRET_KEY')||'';if(!secret)throw new Error('STRIPE_NOT_CONFIGURED');return secret}
function catalog(){
  const secret=stripeSecret()
  const configured={
    essentialProduct:Deno.env.get('STRIPE_PRODUCT_ESSENTIAL')||'',
    proProduct:Deno.env.get('STRIPE_PRODUCT_PRO')||'',
    essentialPrices:[Deno.env.get('STRIPE_PRICE_ESSENTIAL_MONTHLY')||'',Deno.env.get('STRIPE_PRICE_ESSENTIAL_ANNUAL')||''],
    proPrices:[Deno.env.get('STRIPE_PRICE_PRO_MONTHLY')||'',Deno.env.get('STRIPE_PRICE_PRO_ANNUAL')||'']
  }
  if(configured.essentialProduct&&configured.proProduct&&configured.essentialPrices.every(Boolean)&&configured.proPrices.every(Boolean)) return configured
  if(secret.startsWith('sk_test_')) return TEST_CATALOG
  throw new Error('STRIPE_CATALOG_NOT_CONFIGURED')
}
async function stripeRequest(path:string,init:RequestInit={}){const secret=stripeSecret();const response=await fetch(`https://api.stripe.com/v1${path}`,{...init,headers:{Authorization:`Bearer ${secret}`,'Content-Type':'application/x-www-form-urlencoded',...(init.headers||{})}});const data=await response.json();if(!response.ok)throw new Error(data?.error?.message||'Stripe request failed');return data}
async function ensurePortalConfiguration(returnUrl:string){const cat=catalog();const existing=await stripeRequest('/billing_portal/configurations?active=true&limit=10',{method:'GET'});const salesboardConfig=(existing.data||[]).find((item:any)=>item.metadata?.salesboard==='true');if(salesboardConfig)return salesboardConfig.id;const body=new URLSearchParams();body.set('default_return_url',returnUrl);body.set('business_profile[headline]','Gerencie sua assinatura do SalesBoard Finance');body.set('business_profile[privacy_policy_url]',`${PROD_ORIGIN}/Extra/salesboard/legal/privacidade.html`);body.set('business_profile[terms_of_service_url]',`${PROD_ORIGIN}/Extra/salesboard/legal/termos.html`);body.set('features[payment_method_update][enabled]','true');body.set('features[invoice_history][enabled]','true');body.set('features[subscription_cancel][enabled]','true');body.set('features[subscription_cancel][mode]','at_period_end');body.set('features[subscription_update][enabled]','true');body.set('features[subscription_update][default_allowed_updates][0]','price');body.set('features[subscription_update][proration_behavior]','create_prorations');body.set('features[subscription_update][products][0][product]',cat.essentialProduct);cat.essentialPrices.forEach((price,index)=>body.set(`features[subscription_update][products][0][prices][${index}]`,price));body.set('features[subscription_update][products][1][product]',cat.proProduct);cat.proPrices.forEach((price,index)=>body.set(`features[subscription_update][products][1][prices][${index}]`,price));body.set('metadata[salesboard]','true');const config=await stripeRequest('/billing_portal/configurations',{method:'POST',body});return config.id}
Deno.serve(async(req)=>{const headers=cors(req);if(req.method==='OPTIONS')return new Response(null,{status:204,headers});if(req.method!=='POST')return new Response(JSON.stringify({error:'Método não permitido.'}),{status:405,headers});try{const token=(req.headers.get('authorization')||'').replace(/^Bearer\s+/i,'');if(!token)return new Response(JSON.stringify({error:'Sessão necessária.'}),{status:401,headers});const admin=adminClient();const {data,error}=await admin.auth.getUser(token);if(error||!data?.user)return new Response(JSON.stringify({error:'Sessão inválida.'}),{status:401,headers});const {data:profile,error:profileError}=await admin.from('profiles').select('stripe_customer_id').eq('id',data.user.id).single();if(profileError)throw profileError;if(!profile.stripe_customer_id)return new Response(JSON.stringify({error:'Nenhuma cobrança encontrada para esta conta.'}),{status:404,headers});const origin=allowedOrigin(req);const returnUrl=origin.includes('github.io')?`${PROD_ORIGIN}/Extra/salesboard/app/?view=billing`:`${origin.replace(/\/$/,'')}/app/?view=billing`;const configuration=await ensurePortalConfiguration(returnUrl);const params=new URLSearchParams({customer:profile.stripe_customer_id,return_url:returnUrl,configuration});const portal=await stripeRequest('/billing_portal/sessions',{method:'POST',body:params});return new Response(JSON.stringify({url:portal.url}),{status:200,headers})}catch(error){console.error(error);const raw=String(error instanceof Error?error.message:error);const message=raw==='STRIPE_NOT_CONFIGURED'?'Cobrança ainda não configurada no servidor.':raw==='STRIPE_CATALOG_NOT_CONFIGURED'?'Catálogo de cobrança de produção ainda não configurado.':`Não foi possível abrir o portal de cobrança. ${raw.includes('configuration')?'A configuração do portal precisa ser revisada no Stripe.':''}`.trim();return new Response(JSON.stringify({error:message}),{status:500,headers})}})
