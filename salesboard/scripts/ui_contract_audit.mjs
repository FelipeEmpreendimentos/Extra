import { chromium } from 'playwright';

const base = process.env.AUDIT_BASE_URL || 'http://127.0.0.1:4173/salesboard';
const viewports = [{ width: 1366, height: 768 }, { width: 390, height: 844 }];
const failures = [];

function fail(viewport, message) { failures.push(`${viewport.width}x${viewport.height}: ${message}`); }

const browser = await chromium.launch({ headless: true });
for (const viewport of viewports) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const nativeDialogs = [];
  page.on('dialog', async (dialog) => { nativeDialogs.push(dialog.message()); await dialog.dismiss(); });

  try {
    await page.goto(`${base}/app/?demo=1`, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForSelector('#app-shell:not([hidden])', { timeout: 30000 });

    await page.locator('#quick-add').click();
    await page.locator('input[name="transaction_type"][value="income"]').check();
    await page.locator('#tx-goal').selectOption('g1');
    await page.waitForTimeout(100);

    const alignment = await page.evaluate(() => {
      const rect = (selector) => {
        const r = document.querySelector(selector)?.getBoundingClientRect();
        return r ? { top: r.top, left: r.left, width: r.width, height: r.height, bottom: r.bottom } : null;
      };
      return {
        goalLabel: rect('#tx-goal-wrap'),
        statusLabel: rect('#tx-status')?.top,
        goalControl: rect('#tx-goal'),
        statusControl: rect('#tx-status'),
        accountControl: rect('#tx-account'),
        categoryControl: rect('#tx-category')
      };
    });

    if (!alignment.goalControl || !alignment.statusControl) fail(viewport, 'campos Meta/Status não foram encontrados');
    else {
      if (Math.abs(alignment.goalControl.top - alignment.statusControl.top) > 2) fail(viewport, `Meta e Status desalinhados em ${Math.abs(alignment.goalControl.top - alignment.statusControl.top).toFixed(1)}px`);
      if (Math.abs(alignment.goalControl.height - alignment.statusControl.height) > 2) fail(viewport, 'Meta e Status com alturas diferentes');
    }
    if (alignment.accountControl && alignment.categoryControl && Math.abs(alignment.accountControl.top - alignment.categoryControl.top) > 2) fail(viewport, 'Categoria e Conta desalinhadas');

    await page.locator('#transaction-modal [data-close-modal]').first().click();

    // Lançamento: deve abrir modal do SalesBoard, nunca confirm() do navegador.
    await page.locator('[data-view="transactions"]').first().click();
    await page.locator('[data-delete-transaction]').first().click();
    await page.waitForSelector('#confirm-modal:not([hidden])');
    if (!(await page.locator('#confirm-title').textContent()).includes('Excluir lançamento')) fail(viewport, 'confirmação de lançamento não usa o modal padrão');
    await page.locator('#confirm-cancel').click();

    // Conta: mesmo contrato visual.
    await page.locator('[data-view="accounts"]').first().click();
    await page.locator('[data-delete-account-row]').first().click();
    await page.waitForSelector('#confirm-modal:not([hidden])');
    const accountTitle = await page.locator('#confirm-title').textContent();
    if (!/Excluir conta|Arquivar conta/.test(accountTitle || '')) fail(viewport, 'confirmação de conta não usa o modal padrão');
    await page.locator('#confirm-cancel').click();

    // Categoria: mesmo contrato visual.
    await page.locator('[data-view="categories"]').first().click();
    await page.locator('[data-delete-category-row]').first().click();
    await page.waitForSelector('#confirm-modal:not([hidden])');
    const categoryTitle = await page.locator('#confirm-title').textContent();
    if (!/Excluir categoria|Arquivar categoria/.test(categoryTitle || '')) fail(viewport, 'confirmação de categoria não usa o modal padrão');
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
