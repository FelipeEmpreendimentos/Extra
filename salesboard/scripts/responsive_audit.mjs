import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const base = process.env.AUDIT_BASE_URL || 'http://127.0.0.1:4173/salesboard';
const outDir = path.resolve('salesboard/audit-artifacts');
fs.mkdirSync(outDir, { recursive: true });

const viewports = [
  [320,568],[360,800],[375,812],[390,844],[412,915],[430,932],
  [768,1024],[820,1180],[1024,768],[1280,720],[1366,768],[1440,900],
  [1536,864],[1920,1080],[2560,1440]
].map(([width,height]) => ({ width, height, name: `${width}x${height}` }));

const screenshotSizes = new Set(['320x568','390x844','768x1024','1366x768','1920x1080','2560x1440']);
const report = { generatedAt: new Date().toISOString(), base, summary: {}, results: [] };

function addIssue(bucket, severity, code, detail) {
  bucket.issues.push({ severity, code, detail });
}

async function inspectLayout(page, bucket, label) {
  const metrics = await page.evaluate(() => {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const root = document.documentElement;
    const body = document.body;
    const visible = (el) => {
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity || 1) > 0 && r.width > 0 && r.height > 0;
    };
    const hasScrollParent = (el) => {
      let p = el.parentElement;
      while (p && p !== body) {
        const s = getComputedStyle(p);
        if (/(auto|scroll|hidden|clip)/.test(s.overflowX)) return true;
        p = p.parentElement;
      }
      return false;
    };
    const offenders = [];
    for (const el of document.querySelectorAll('body *')) {
      if (!visible(el)) continue;
      const r = el.getBoundingClientRect();
      if ((r.left < -2 || r.right > vw + 2) && !hasScrollParent(el)) {
        offenders.push({
          tag: el.tagName.toLowerCase(), id: el.id || '', cls: String(el.className || '').slice(0,120),
          left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width)
        });
        if (offenders.length >= 20) break;
      }
    }
    const tinyTargets = [];
    for (const el of document.querySelectorAll('button,a[href],input,select')) {
      if (!visible(el)) continue;
      const r = el.getBoundingClientRect();
      if ((r.width < 32 || r.height < 32) && !el.closest('.table-wrap')) {
        tinyTargets.push({ tag: el.tagName.toLowerCase(), id: el.id || '', text: (el.textContent || '').trim().slice(0,60), width: Math.round(r.width), height: Math.round(r.height) });
        if (tinyTargets.length >= 20) break;
      }
    }
    return {
      viewport: { width: vw, height: vh },
      scrollWidth: Math.max(root.scrollWidth, body?.scrollWidth || 0),
      scrollHeight: Math.max(root.scrollHeight, body?.scrollHeight || 0),
      offenders,
      tinyTargets,
      activeModal: [...document.querySelectorAll('.modal:not([hidden]),.sb-delete-overlay')].map((m) => {
        const card = m.querySelector('.modal-card,.sb-delete-dialog') || m;
        const r = card.getBoundingClientRect();
        return { top: Math.round(r.top), bottom: Math.round(r.bottom), left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width), height: Math.round(r.height), overflowY: getComputedStyle(card).overflowY };
      })
    };
  });
  bucket.measurements.push({ label, ...metrics });
  if (metrics.scrollWidth > metrics.viewport.width + 2) addIssue(bucket, 'critical', 'horizontal-page-overflow', `${label}: documento ${metrics.scrollWidth}px > viewport ${metrics.viewport.width}px`);
  if (metrics.offenders.length) addIssue(bucket, 'high', 'element-overflow', `${label}: ${JSON.stringify(metrics.offenders.slice(0,8))}`);
  if (metrics.tinyTargets.length) addIssue(bucket, 'low', 'small-interactive-targets', `${label}: ${metrics.tinyTargets.length} alvo(s) abaixo de 32px; amostra ${JSON.stringify(metrics.tinyTargets.slice(0,5))}`);
  for (const modal of metrics.activeModal) {
    if (modal.left < -2 || modal.right > metrics.viewport.width + 2) addIssue(bucket, 'critical', 'modal-horizontal-overflow', `${label}: ${JSON.stringify(modal)}`);
    if (modal.top < -2 || modal.bottom > metrics.viewport.height + 2) {
      if (!/(auto|scroll)/.test(modal.overflowY)) addIssue(bucket, 'high', 'modal-vertical-clipping', `${label}: ${JSON.stringify(modal)}`);
    }
  }
}

async function waitForApp(page) {
  await page.goto(`${base}/app/?demo=1`, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForSelector('#app-shell:not([hidden])', { timeout: 30000 });
  await page.waitForTimeout(350);
}

async function clickView(page, view) {
  const candidates = page.locator(`[data-view="${view}"]`);
  const count = await candidates.count();
  for (let i = 0; i < count; i++) {
    if (await candidates.nth(i).isVisible()) {
      await candidates.nth(i).click();
      await page.waitForTimeout(180);
      return true;
    }
  }
  return false;
}

async function auditViewport(browser, vp) {
  const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1 });
  const page = await context.newPage();
  const bucket = { viewport: vp.name, issues: [], measurements: [], consoleErrors: [], pageErrors: [], failedRequests: [] };
  page.on('console', (msg) => { if (msg.type() === 'error') bucket.consoleErrors.push(msg.text()); });
  page.on('pageerror', (err) => bucket.pageErrors.push(String(err.message || err)));
  page.on('requestfailed', (req) => bucket.failedRequests.push({ url: req.url(), error: req.failure()?.errorText || 'failed' }));

  try {
    await page.goto(`${base}/`, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(250);
    await inspectLayout(page, bucket, 'landing');
    if (screenshotSizes.has(vp.name)) await page.screenshot({ path: path.join(outDir, `landing-${vp.name}.png`), fullPage: true });

    await waitForApp(page);
    await inspectLayout(page, bucket, 'dashboard');
    if (screenshotSizes.has(vp.name)) await page.screenshot({ path: path.join(outDir, `dashboard-${vp.name}.png`), fullPage: true });

    const views = ['transactions','accounts','budgets','goals','reports','billing','settings'];
    for (const view of views) {
      const clicked = await clickView(page, view);
      if (!clicked) {
        addIssue(bucket, 'medium', 'view-not-reachable', view);
        continue;
      }
      await inspectLayout(page, bucket, `view:${view}`);
      if (screenshotSizes.has(vp.name) && ['transactions','reports','billing'].includes(view)) {
        await page.screenshot({ path: path.join(outDir, `${view}-${vp.name}.png`), fullPage: true });
      }
    }

    await clickView(page, 'transactions');
    const addTx = page.locator('[data-open-transaction]').filter({ visible: true }).first();
    if (await addTx.count()) {
      await addTx.click(); await page.waitForTimeout(120);
      await inspectLayout(page, bucket, 'modal:transaction');
      await page.locator('#transaction-modal [data-close-modal]').first().click();
    } else addIssue(bucket, 'medium', 'transaction-modal-unreachable', 'botão não encontrado');

    await clickView(page, 'accounts');
    const addAccount = page.locator('#add-account');
    if (await addAccount.isVisible().catch(() => false)) {
      await addAccount.click(); await page.waitForTimeout(120);
      await inspectLayout(page, bucket, 'modal:account');
      await page.locator('#entity-modal [data-close-modal]').first().click();
    }

    await clickView(page, 'budgets');
    const addCategory = page.locator('#add-category');
    if (await addCategory.isVisible().catch(() => false)) {
      await addCategory.click(); await page.waitForTimeout(120);
      await inspectLayout(page, bucket, 'modal:category');
      await page.locator('#entity-modal [data-close-modal]').first().click();
    }

    if (bucket.pageErrors.length) addIssue(bucket, 'critical', 'page-errors', bucket.pageErrors.join(' | '));
    const relevantConsole = bucket.consoleErrors.filter((x) => !/favicon|Failed to load resource/i.test(x));
    if (relevantConsole.length) addIssue(bucket, 'high', 'console-errors', relevantConsole.slice(0,8).join(' | '));
    const relevantFailed = bucket.failedRequests.filter((x) => !/fonts\.gstatic|fonts\.googleapis/i.test(x.url));
    if (relevantFailed.length) addIssue(bucket, 'medium', 'failed-requests', JSON.stringify(relevantFailed.slice(0,8)));
  } catch (error) {
    addIssue(bucket, 'critical', 'audit-exception', String(error?.stack || error));
  } finally {
    await context.close();
  }
  return bucket;
}

const browser = await chromium.launch({ headless: true });
for (const vp of viewports) report.results.push(await auditViewport(browser, vp));
await browser.close();

const counts = { critical: 0, high: 0, medium: 0, low: 0 };
for (const r of report.results) for (const issue of r.issues) counts[issue.severity]++;
report.summary = counts;
fs.writeFileSync(path.join(outDir, 'responsive-audit.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report.summary));
for (const r of report.results) {
  if (!r.issues.length) console.log(`PASS ${r.viewport}`);
  else {
    console.log(`ISSUES ${r.viewport}`);
    for (const issue of r.issues) console.log(`  [${issue.severity}] ${issue.code}: ${issue.detail}`);
  }
}
if (counts.critical || counts.high) process.exitCode = 1;
