import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const dir = process.argv[2];
const b = await chromium.launch({ args: ['--allow-file-access-from-files'] });
const p = await b.newPage({ viewport: { width: 1080, height: 3300 }, deviceScaleFactor: 1 });
await p.goto('file://' + dir + '/thumb.html'); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
for (const id of ['t916', 't45']) await (await p.$('#' + id)).screenshot({ path: `${dir}/thumb_${id}.png` });
await b.close(); console.log('ok');
