// Tests Brief generation + Interview multi-step flow + Show Details expand.
const { chromium } = require('playwright');
const BASE = 'https://pih-hack-test.onrender.com';

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  page.on('response', async (r) => {
    if (r.url().includes('/api/') && /brief|generate/i.test(r.url())) {
      let b = ''; try { b = (await r.text()).slice(0, 200).replace(/\s+/g, ' '); } catch {}
      console.log(`  BRIEF RESP ${r.status()} ${r.request().method()} ${r.url()} :: ${b}`);
    }
  });

  for (let i = 0; i < 6; i++) {
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (await page.getByRole('button', { name: 'Home', exact: true }).isVisible().catch(() => false)) break;
    await page.waitForTimeout(2000);
  }

  // ===== BRIEF GENERATION =====
  console.log('--- Brief generation ---');
  await page.getByRole('button', { name: 'Library', exact: true }).click();
  await page.waitForTimeout(1500);

  // Show Details expand on first project
  const showDetails = page.getByRole('button', { name: /Show Details/i }).first();
  if (await showDetails.count()) {
    await showDetails.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'playwright/pih-library-details.png', fullPage: true });
    console.log('  Show Details: expanded OK');
  }

  const briefBtn = page.getByRole('button', { name: /Brief/i }).first();
  await briefBtn.click();
  console.log('  Brief button clicked, waiting for generation...');
  let briefText = '';
  for (let i = 0; i < 25; i++) {
    await page.waitForTimeout(3000);
    const body = await page.evaluate(() => document.body.innerText.replace(/\s+/g, ' ').trim());
    // brief likely opens a modal / new view with lots of text
    if (body.length > 1500 || /executive summary|sales brief|generated|key outcomes|value proposition/i.test(body)) { briefText = body; break; }
    briefText = body;
  }
  await page.screenshot({ path: 'playwright/pih-brief-result.png', fullPage: true });
  console.log('  Brief body (600 chars):', briefText.slice(0, 600));

  // ===== INTERVIEW FLOW =====
  console.log('\n--- Interview flow ---');
  await page.getByRole('button', { name: 'Interview', exact: true }).click();
  await page.waitForTimeout(1500);

  const steps = [];
  for (let step = 0; step < 4; step++) {
    const q = await page.evaluate(() => {
      const h = document.querySelector('h2,h3');
      return h ? h.innerText.trim() : '(no question heading)';
    });
    const inp = page.locator('input,textarea').first();
    const hasInput = await inp.count();
    if (hasInput) await inp.fill(`Automated answer for step ${step + 1}`);
    steps.push(`Q${step + 1}: "${q}" (input:${hasInput ? 'yes' : 'no'})`);
    const next = page.getByRole('button', { name: /Next/i }).first();
    if (await next.count() && await next.isEnabled().catch(() => false)) {
      await next.click();
      await page.waitForTimeout(1000);
    } else break;
  }
  await page.screenshot({ path: 'playwright/pih-interview-flow.png', fullPage: true });
  console.log('  Interview steps:\n   ' + steps.join('\n   '));

  await context.close();
  await browser.close();
})().catch((e) => { console.error('FATAL:', e); process.exit(1); });
