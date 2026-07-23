// Records a video walkthrough of the PIH AI Evaluation Dashboard.
// Run with: node playwright/record-dashboard.js
const { chromium } = require('playwright');
const { convertFile } = require('./webm-to-mp4');

const URL = 'http://localhost:8501/';

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: 'playwright/videos', size: { width: 1440, height: 900 } },
  });
  const page = await context.newPage();

  const pause = (ms) => page.waitForTimeout(ms);

  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForSelector('text=Project Intelligence Hub', { timeout: 30000 });
  await pause(2500);

  // Main tab: Overview & Trends (already selected) -> linger on charts
  await pause(2500);

  // Main tab: Deep-Dive Metrics, then walk each sub-tab
  await page.getByRole('tab', { name: 'Deep-Dive Metrics' }).click();
  await pause(1500);

  const subTabs = [
    'Information Extraction',
    'Semantic Search / Retrieval',
    'RAG & Faithfulness',
    'Hallucination Details',
    'Sales Brief Grader',
    'LLM-as-a-Judge',
  ];
  for (const name of subTabs) {
    try {
      await page.getByRole('tab', { name }).click();
      await pause(1800);
    } catch (e) {
      console.log('skip sub-tab', name, e.message);
    }
  }

  // Main tab: Real-Time Testbench
  await page.getByRole('tab', { name: 'Real-Time Testbench' }).click();
  await pause(2500);

  await context.close(); // finalizes the video file
  await browser.close();

  const video = await page.video();
  const webmPath = video ? await video.path() : null;
  if (webmPath) {
    const mp4Path = await convertFile(webmPath); // converts to mp4 and deletes the .webm
    console.log('VIDEO SAVED:', mp4Path);
  } else {
    console.log('(no video produced)');
  }
})().catch((e) => {
  console.error('FAILED:', e);
  process.exit(1);
});
