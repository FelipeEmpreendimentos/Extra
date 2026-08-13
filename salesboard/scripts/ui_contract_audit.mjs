import { chromium } from 'playwright';
import fs from 'node:fs';

const base = process.env.AUDIT_BASE_URL || 'http://127.0.0.1:4173/salesboard';
const viewports = [{ width: 1366, height: 768 }, { width: 390, height: 844 }];
const failures = [];

function fail(viewport, message) { failures.push(`${viewport.width}x${viewport.height}: ${message}`); }

async function openView(page, view) {
  const candidates = [`.mobile-nav [data-view="${view}"]`, `#main-nav [data-view="${view}"]`, `[data-view="${view}"]`];
  for (const selector of candidates) {
    const item = page.locator(selector).first();
    if (!(await item.count())) continue;
    try {
      await item.evaluate((element) => element.click());
      await page.waitForTimeout(120);
      return true;
    } catch {}
  }
  return false;
}

// Static contract: browser-native dialogs are forbidden in the product UI.
for (const file of ['salesboard/app/app.js', 'salesboard/app/runtime-bridge.js']) {
  const source = fs.readFileSync(file, 'utf8');
  if (/\b(?:confirm|prompt|alert)\s*\(/.test(source)) failures.push(`static: diálogo nativo encontrado em ${file}`);
}

const browser = await chromium.launch({ headless: true });
for (const viewport of viewports) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const nativeDialogs = [];
  page.on('dialog', async (dialog) => { nativeDialogs.push(dialog.message()); await dialog.dismiss(); });

  try {
    await page.goto(`${base}/app/?demo=1`, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForSelector('#app-shell:not([hidden])', { timeout: 30000 });

    await page.locator('#quick-add').evaluate((element) => element.click());
    await page.locator('input[name="transaction_type"][value="income"]').check();
    await page.locator('#tx-goal').selectOption('g1');
    await page.waitForTimeout(100);

    const alignment = await page.evaluate(() => {
      const rect = (selector) => {
        const r = document.querySelector(selector)?.getBoundingClientRect();
        return r ? { top: r.top, left: r.left, right: r.right, width: r.width, height: r.height, bottom: r.bottom } : null;
      };
      return {
        goalControl: rect('#tx-goal'),
        statusControl: rect('#tx-status'),
        accountControl: rect('#tx-account'),
        categoryControl: rect('#tx-category'),
        modal: rect('#transaction-modal .modal-card')
      };
    });

    if (!alignment.goalControl || !alignment.statusControl) fail(viewport, 'campos Meta/Status não foram encontrados');
    else if (viewport.width > 680) {
      if (Math.abs(alignment.goalControl.top - alignment.statusControl.top) > 2) fail(viewport, `Meta e Status desalinhados em ${Math.abs(alignment.goalControl.top - alignment.statusControl.top).toFixed(1)}px`);
      if (Math.abs(alignment.goalControl.height - alignment.statusControl.height) > 2) fail(viewport, 'Meta e Status com alturas diferentes');
      if (alignment.accountControl && alignment.categoryControl && Math.abs(alignment.accountControl.top - alignment.categoryControl.top) > 2) fail(viewport, 'Categoria e Conta desalinhadas');
    } else {
      if (alignment.goalControl.width < viewport.width * 0.7 || alignment.statusControl.width < viewport.width * 0.7) fail(viewport, 'campos do lançamento estreitos demais no celular');
      if (alignment.modal && (alignment.modal.left < -1 || alignment.modal.right > viewport.width + 1)) fail(viewport, 'modal de lançamento ultrapassa a largura do celular');
    }

    await page.locator('#transaction-modal [data-close-modal]').first().evaluate((element) => element.click());

    // Lançamento: deve abrir modal do SalesBoard, nunca confirm() do navegador.
    if (!(await openView(page, 'transactions'))) throw new Error('view transactions não encontrada');
    await page.locator('[data-delete-transaction]').first().evaluate((element) => element.click());
    await page.waitForSelector('#confirm-modal:not([hidden])');
    if (!(await page.locator('#confirm-title').textContent()).includes('Excluir lançamento')) fail(viewport, 'confirmação de lançamento não usa o modal padrão');
    await page.locator('#confirm-cancel').click();

    // Conta: mesmo contrato visual. Conta com histórico deve ser arquivada.
    if (!(await openView(page, 'accounts'))) throw new Error('view accounts não encontrada');
    await page.locator('[data-delete-account-row]').first().evaluate((element) => element.click());
    await page.waitForSelector('#confirm-modal:not([hidden])');
    const accountTitle = await page.locator('#confirm-title').textContent();
    if (!/Excluir conta|Arquivar conta/.test(accountTitle || '')) fail(viewport, 'confirmação de conta não usa o modal padrão');
    await page.locator('#confirm-cancel').click();

    // Categoria: mesmo contrato visual. Categoria com histórico deve ser arquivada.
    if (!(await openView(page, 'categories'))) throw new Error('view categories não encontrada');
    await page.locator('[data-delete-category-row]').first().evaluate((element) => element.click());
    await page.waitForSelector('#confirm-modal:not([hidden])');
    const categoryTitle = await page.locator('#confirm-title').textContent();
    if (!/Excluir categoria|Arquivar categoria/.test(categoryTitle || '')) fail(viewport, 'confirmação de categoria não usa o modal padrão');
    await page.locator('#confirm-cancel').click();

    // Meta usa o mesmo componente de confirmação.
    if (!(await openView(page, 'goals'))) throw new Error('view goals não encontrada');
    await page.locator('[data-delete-goal-row]').first().evaluate((element) => element.click());
    await page.waitForSelector('#confirm-modal:not([hidden])');
    if (!(await page.locator('#confirm-title').textContent()).includes('Excluir meta')) fail(viewport, 'confirmação de meta não usa o modal padrão');
    await page.locator('#confirm-cancel').click();

    if (nativeDialogs.length) fail(viewport, `diálogo nativo detectado: ${nativeDialogs.join(' | ')}`);
  } catch (error) {
    fail(viewport, String(error?.stack || error));
  } finally {
    await context.close();
  }
}
await browser.close();

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}
console.log('PASS UI contract: alignment + custom confirmations on desktop and mobile');
