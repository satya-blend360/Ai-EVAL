// Recon pass for https://pih-hack-test.onrender.com/
// Captures: title, console errors, failed network requests, page structure
// (headings, links, buttons, inputs, forms), full-page screenshot.
const { chromium } = require('playwright');

const URL = process.argv[2] || 'https://pih-hack-test.onrender.com/';

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const consoleMsgs = [];
  const pageErrors = [];
  const failedRequests = [];
  const responses = [];

  page.on('console', (m) => consoleMsgs.push(`[${m.type()}] ${m.text()}`));
  page.on('pageerror', (e) => pageErrors.push(e.message));
  page.on('requestfailed', (r) => failedRequests.push(`${r.method()} ${r.url()} -> ${r.failure()?.errorText}`));
  page.on('response', (r) => { if (r.status() >= 400) responses.push(`${r.status()} ${r.url()}`); });

  const started = Date.now();
  let status = 'n/a';
  try {
    const resp = await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
    status = resp ? resp.status() : 'no-response';
  } catch (e) {
    console.log('NAVIGATION ERROR:', e.message);
  }
  const loadMs = Date.now() - started;

  await page.waitForTimeout(2500); // allow any client-side rendering

  const title = await page.title();
  const url = page.url();

  const structure = await page.evaluate(() => {
    const text = (el) => (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120);
    const grab = (sel) => Array.from(document.querySelectorAll(sel));
    return {
      headings: grab('h1,h2,h3,h4').map((h) => `${h.tagName}: ${text(h)}`).filter((x) => x.length > 5).slice(0, 40),
      links: grab('a').map((a) => ({ t: text(a), href: a.getAttribute('href') })).filter((l) => l.t || l.href).slice(0, 60),
      buttons: grab('button, input[type=submit], [role=button]').map((b) => text(b) || b.getAttribute('aria-label') || '(unlabeled)').slice(0, 40),
      inputs: grab('input, textarea, select').map((i) => `${i.tagName.toLowerCase()}[type=${i.getAttribute('type') || 'n/a'}] name=${i.getAttribute('name') || ''} placeholder="${i.getAttribute('placeholder') || ''}"`).slice(0, 40),
      forms: grab('form').map((f) => `action=${f.getAttribute('action') || ''} method=${f.getAttribute('method') || 'get'}`),
      bodyTextSample: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 800),
    };
  });

  await page.screenshot({ path: 'playwright/pih-recon-home.png', fullPage: true });

  console.log('===== RECON REPORT =====');
  console.log('URL (final):', url);
  console.log('HTTP status:', status, '| load(networkidle) ms:', loadMs);
  console.log('Title:', JSON.stringify(title));
  console.log('\n-- Headings --');           console.log(structure.headings.join('\n') || '(none)');
  console.log('\n-- Buttons --');            console.log(structure.buttons.join('\n') || '(none)');
  console.log('\n-- Inputs --');             console.log(structure.inputs.join('\n') || '(none)');
  console.log('\n-- Forms --');              console.log(structure.forms.join('\n') || '(none)');
  console.log('\n-- Links --');              console.log(structure.links.map((l) => `${l.t} -> ${l.href}`).join('\n') || '(none)');
  console.log('\n-- Body text sample --');   console.log(structure.bodyTextSample);
  console.log('\n-- Console messages --');   console.log(consoleMsgs.join('\n') || '(none)');
  console.log('\n-- Page errors --');        console.log(pageErrors.join('\n') || '(none)');
  console.log('\n-- Failed requests --');    console.log(failedRequests.join('\n') || '(none)');
  console.log('\n-- HTTP >=400 responses --'); console.log(responses.join('\n') || '(none)');
  console.log('========================');

  await context.close();
  await browser.close();
})().catch((e) => { console.error('FATAL:', e); process.exit(1); });
