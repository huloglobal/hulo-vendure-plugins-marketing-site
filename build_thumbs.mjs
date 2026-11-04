// Gallery thumbnails for the WordPress plugin pages: each screenshot PNG is
// written as WebP at a few widths, so a thumbnail never downloads the full
// 1280 px PNG (that stays the lightbox image). Called by build_wordpress.py
// with a JSON job list on stdin:
//
//   [{"src": "/abs/screenshot-1.png", "out": "/abs/dir/screenshot-1-{w}.webp", "widths": [480, 800, 1280]}]
//
// Resolves sharp from the main site's node_modules, as build_css.mjs does
// with Tailwind. Prints {"ok": n} on success; exits non-zero on failure, and
// the builder then falls back to the full-size PNG.
import { createRequire } from 'node:module';
import { join } from 'node:path';

const SITE = process.env.HULO_SITE_DIR || '/root/huloglobal-site';
const require = createRequire(join(SITE, 'package.json'));
const sharp = require('sharp');

let raw = '';
for await (const chunk of process.stdin) raw += chunk;
const jobs = JSON.parse(raw || '[]');
const QUALITY = Number(process.env.HULO_THUMB_QUALITY || 82);

let ok = 0;
for (const job of jobs) {
  const image = sharp(job.src);
  for (const w of job.widths) {
    await image.clone().resize({ width: w, withoutEnlargement: true })
      .webp({ quality: QUALITY, effort: 5 }).toFile(job.out.replace('{w}', String(w)));
    ok++;
  }
}
console.log(JSON.stringify({ ok }));
