// Focused test of the Discover natural-language search.
const { chromium } = require('playwright');
const BASE = 'https://pih-hack-test.onrender.com';

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const apiCalls = [];
  page.on('request', (r) => { if (r.url().includes('/api/')) apiCalls.push(`${r.method()} ${r.url()}`); });
  page.on('response', async (r) => {
    if (r.url().includes('/api/') && !r.url().match(/projects$|health$/)) {
      let body = '';
      try { body = (await r.text()).slice(0, 300).replace(/\s+/g, ' '); } catch {}
      console.log(`  RESP ${r.status()} ${r.request().method()} ${r.url()} :: ${body}`);
    }
  });

  // load home (retry cold start)
  for (let i = 0; i < 6; i++) {
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (await page.getByRole('button', { name: 'Home', exact: true }).isVisible().catch(() => false)) break;
    await page.waitForTimeout(2000);
  }

  await page.getByRole('button', { name: 'Discover', exact: true }).click();
  await page.waitForTimeout(1500);

  const input = page.locator('input').first();
  await input.fill('database migration to the cloud');
  await page.getByRole('button', { name: /search/i }).first().click();

  console.log('Search submitted, waiting for results...');
  // Wait up to 90s for either results or an error to appear (results = body changes away from suggestions)
  const started = Date.now();
  let resolvedText = '';
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(3000);
    const body = await page.evaluate(() => document.body.innerText.replace(/\s+/g, ' ').trim());
    const stillLoading = await page.getByRole('button', { name: /search/i }).first().evaluate((b) => b.disabled || /\.\.\.|loading/i.test(b.innerText)).catch(() => false);
    if (!stillLoading && !body.includes('Try searching for')) { resolvedText = body; break; }
    if (body.match(/error|failed|no results|no projects/i)) { resolvedText = body; break; }
    resolvedText = body;
  }
  const elapsed = ((Date.now() - started) / 1000).toFixed(1);
  await page.screenshot({ path: 'playwright/pih-discover-result.png', fullPage: true });

  console.log(`\nElapsed: ${elapsed}s`);
  console.log('API calls seen:', apiCalls.length ? apiCalls.join(' | ') : '(none)');
  console.log('Final body (700 chars):', resolvedText.slice(0, 700));

  await context.close();
  await browser.close();
})().catch((e) => { console.error('FATAL:', e); process.exit(1); });
