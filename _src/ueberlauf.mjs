// Welche Elemente ragen bei schmaler Breite über den rechten Rand? Aufruf: node ueberlauf.mjs [pfad] [breite]
import { chromium } from 'file:///C:/Users/suak/career-ops/node_modules/playwright/index.mjs';
const pfad = process.argv[2] || '', w = +(process.argv[3] || 320);
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: w, height: 800 }, isMobile: true });
await p.goto('http://127.0.0.1:8778/' + pfad, { waitUntil: 'networkidle' });
for (let y = 0; y < 8000; y += 600) { await p.evaluate(y => scrollTo(0, y), y); await p.waitForTimeout(50); }
console.log(await p.evaluate(() => { const cw = document.documentElement.clientWidth; const out = []; for (const el of document.querySelectorAll('body *')) { const r = el.getBoundingClientRect(); if (r.right > cw + 1 && r.width > 0 && getComputedStyle(el).position !== 'fixed') out.push(`${el.tagName.toLowerCase()}.${(el.className && el.className.baseVal === undefined ? el.className : '').toString().split(' ')[0]} right=${Math.round(r.right)} w=${Math.round(r.width)}`); } return `clientWidth ${cw}, scrollWidth ${document.documentElement.scrollWidth}\n` + out.slice(0, 12).join('\n'); }));
await b.close();
