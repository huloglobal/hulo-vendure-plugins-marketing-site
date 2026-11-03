// Compile the stylesheet for the generated pages (/vendure-plugins,
// /wordpress-plugins, /legal) from the main site's own Tailwind theme.
//
// The pages used to link the Astro site's frozen index CSS, which only held
// the utilities the Astro pages happened to use — so classes such as md:flex,
// pt-12 or mx-auto silently did nothing here. This scans the generated HTML
// for every class it uses and compiles exactly those, with the same @theme,
// base layer and components (container-page, btn, platform badges…) as
// huloglobal.com, from /root/huloglobal-site/src/styles/global.css.
//
// Usage: node build_css.mjs   (after the python builders have written dist/)
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SITE = process.env.HULO_SITE_DIR || '/root/huloglobal-site';
const require = createRequire(join(SITE, 'package.json'));
const { compile } = await import(require.resolve('@tailwindcss/node'));
const { Scanner } = require('@tailwindcss/oxide');

const stylesDir = join(SITE, 'src', 'styles');
// Theme + components from the main site, nothing else.
const input = readFileSync(join(stylesDir, 'global.css'), 'utf8');

const compiler = await compile(input, { base: stylesDir, onDependency: () => {} });
const scanner = new Scanner({
  sources: ['vendure-plugins', 'wordpress-plugins', 'legal'].map(d => ({
    base: join(HERE, 'dist', d), pattern: '**/*.html', negated: false,
  })),
});
const candidates = scanner.scan();
const css = compiler.build(candidates);

const out = join(HERE, 'dist', 'vendure-plugins', 'assets', 'pages.css');
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, css);
console.log(`pages.css: ${candidates.length} candidates, ${(css.length / 1024).toFixed(1)} KiB -> ${out}`);
