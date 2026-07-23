// Converts every .webm in a directory to .mp4 (H.264) and deletes the .webm.
// Usage:
//   const { convertDir, convertFile } = require('./webm-to-mp4');
//   await convertDir('playwright/videos');
// Or standalone:
//   node playwright/webm-to-mp4.js [dir]   (defaults to playwright/videos)
const { execFile } = require('child_process');
const fs = require('fs');
const path = require('path');

const ffmpegPath = require('ffmpeg-static');

function run(args) {
  return new Promise((resolve, reject) => {
    execFile(ffmpegPath, args, (err, stdout, stderr) => {
      if (err) reject(new Error(stderr || err.message));
      else resolve();
    });
  });
}

// Convert a single .webm -> .mp4, then delete the source .webm.
async function convertFile(webmPath) {
  const mp4Path = webmPath.replace(/\.webm$/i, '.mp4');
  await run([
    '-y', '-i', webmPath,
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-movflags', '+faststart', '-an',
    mp4Path,
  ]);
  fs.unlinkSync(webmPath);
  console.log(`converted ${path.basename(webmPath)} -> ${path.basename(mp4Path)} (webm deleted)`);
  return mp4Path;
}

// Convert all .webm files in a directory.
async function convertDir(dir) {
  if (!fs.existsSync(dir)) return [];
  const webms = fs.readdirSync(dir).filter((f) => f.toLowerCase().endsWith('.webm'));
  const out = [];
  for (const f of webms) out.push(await convertFile(path.join(dir, f)));
  return out;
}

module.exports = { convertFile, convertDir };

// Run standalone if invoked directly.
if (require.main === module) {
  const dir = process.argv[2] || 'playwright/videos';
  convertDir(dir)
    .then((files) => console.log(files.length ? `Done: ${files.length} file(s).` : 'No .webm files found.'))
    .catch((e) => { console.error('FAILED:', e.message); process.exit(1); });
}
