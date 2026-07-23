// Full functional test of https://pih-hack-test.onrender.com/
// Walks every nav section, exercises Interview / Library / Discover,
// probes the API, captures per-section screenshots, records video.
const { chromium, request } = require('playwright');
const { convertFile } = require('./webm-to-mp4');

const BASE = process.argv[2] || 'https://pih-hack-test.onrender.com';

const results = [];
function log(section, ok, detail) {
  results.push({ section, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'} | ${section} | ${detail}`);
}

async function dump(page) {
  return page.evaluate(() => {
    const t = (el) => (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 100);
    const q = (s) => Array.from(document.querySelectorAll(s));
    return {
      h: q('h1,h2,h3,h4').map(t).filter((x) => x.length > 3).slice(0, 25),
      btns: q('button,[role=button]').map((b) => t(b) || b.getAttribute('aria-label') || '?').slice(0, 30),
      inputs: q('input,textarea,select').map((i) => `${i.tagName.toLowerCase()}[${i.type || ''}] ph="${i.placeholder || ''}"`).slice(0, 30),
      body: (document.body.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
    };
  });
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: 'playwright/videos', size: { width: 1440, height: 900 } },
  });
  const page = await context.newPage();

  const consoleErrors = [];
  const httpErrors = [];
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('response', (r) => { if (r.status() >= 400) httpErrors.push(`${r.status()} ${r.request().method()} ${r.url()}`); });

  // ---- Quantify root-route flakiness via direct probes ----
  {
    const probe = await request.newContext();
    let ok = 0, notFound = 0, other = 0;
    const N = 8;
    for (let i = 0; i < N; i++) {
      try {
        const r = await probe.get(BASE + '/', { timeout: 20000 });
        const body = (await r.text()).slice(0, 40);
        if (r.status() === 200 && /<!DOCTYPE|<html/i.test(body)) ok++;
        else if (/Not Found/i.test(body) || r.status() === 404) notFound++;
        else other++;
      } catch { other++; }
    }
    await probe.dispose();
    log('Root "/" stability', notFound === 0, `${N} hits -> ${ok} OK / ${notFound} "Not Found" / ${other} other`);
  }

  // ---- Home (retry through cold-start 404s) ----
  let homeLoaded = false;
  for (let attempt = 1; attempt <= 6 && !homeLoaded; attempt++) {
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    try {
      await page.getByRole('button', { name: 'Home', exact: true }).waitFor({ state: 'visible', timeout: 8000 });
      homeLoaded = true;
    } catch {
      console.log(`  home not rendered (attempt ${attempt}), retrying...`);
      await page.waitForTimeout(2000);
    }
  }
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'playwright/pih-01-home.png', fullPage: true });
  const home = await dump(page);
  log('Home render', homeLoaded && home.h.length > 0, `headings: ${home.h.join(' | ')}`);
  const connected = home.body.includes('Connected');
  log('Home/status badge', connected, connected ? '✅ Connected shown' : 'no Connected badge');

  // ---- Navigate each section by clicking nav buttons ----
  const sections = ['Interview', 'Library', 'Discover'];
  let idx = 1;
  for (const name of sections) {
    idx++;
    try {
      const btn = page.getByRole('button', { name, exact: true }).first();
      await btn.click({ timeout: 8000 });
      await page.waitForTimeout(2500);
      const d = await dump(page);
      await page.screenshot({ path: `playwright/pih-0${idx}-${name.toLowerCase()}.png`, fullPage: true });
      log(name, true, `headings: [${d.h.join(' | ')}] | buttons: [${d.btns.join(', ')}] | inputs: ${d.inputs.length}`);

      // --- Section-specific interactions ---
      if (name === 'Discover') {
        const search = page.locator('input[type=text], input:not([type]), textarea').first();
        if (await search.count()) {
          await search.fill('database migration projects');
          await page.waitForTimeout(300);
          // try a search/submit button or Enter
          const go = page.getByRole('button', { name: /search|discover|go|find/i }).first();
          if (await go.count()) await go.click({ timeout: 5000 }).catch(() => {});
          else await search.press('Enter');
          await page.waitForTimeout(4000);
          await page.screenshot({ path: 'playwright/pih-discover-search.png', fullPage: true });
          const after = await dump(page);
          log('Discover/search', true, `after search body: ${after.body.slice(0, 250)}`);
        } else {
          log('Discover/search', false, 'no search input found');
        }
      }

      if (name === 'Interview') {
        const inputs = page.locator('input[type=text], input:not([type]), textarea');
        const n = await inputs.count();
        if (n > 0) {
          await inputs.first().fill('Test answer from automated Playwright run');
          await page.waitForTimeout(500);
          await page.screenshot({ path: 'playwright/pih-interview-filled.png', fullPage: true });
          log('Interview/input', true, `${n} input field(s); filled first one`);
        } else {
          log('Interview/input', false, 'no input fields found on Interview view');
        }
      }

      if (name === 'Library') {
        const d2 = await dump(page);
        log('Library/content', true, `body: ${d2.body.slice(0, 250)}`);
      }
    } catch (e) {
      log(name, false, `interaction error: ${e.message}`);
    }
  }

  // ---- Direct API probes ----
  const api = await request.newContext();
  for (const ep of ['/api/health', '/api/projects', '/health', '/api', '/api/discover']) {
    try {
      const r = await api.get(BASE + ep, { timeout: 15000 });
      const body = (await r.text()).slice(0, 120).replace(/\s+/g, ' ');
      log(`API ${ep}`, r.ok(), `HTTP ${r.status()} :: ${body}`);
    } catch (e) {
      log(`API ${ep}`, false, e.message);
    }
  }
  await api.dispose();

  // ---- Console / HTTP error summary ----
  log('Console errors', consoleErrors.length === 0, consoleErrors.length ? consoleErrors.join(' || ') : 'none');
  log('HTTP >=400', httpErrors.length === 0, httpErrors.length ? [...new Set(httpErrors)].join(' || ') : 'none');

  // ---- finalize video -> mp4 ----
  const video = page.video();
  await context.close();
  await browser.close();
  if (video) {
    const mp4 = await convertFile(await video.path());
    console.log('VIDEO:', mp4);
  }

  // ---- summary ----
  const pass = results.filter((r) => r.ok).length;
  console.log(`\n===== SUMMARY: ${pass}/${results.length} checks passed =====`);
})().catch((e) => { console.error('FATAL:', e); process.exit(1); });
