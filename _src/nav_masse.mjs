// Breiten der Kopfleisten-Elemente bei 320 px, um den Überlauf zu finden
import { chromium } from 'file:///C:/Users/suak/career-ops/node_modules/playwright/index.mjs';
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 320, height: 800 }, isMobile: true });
await p.goto('http://127.0.0.1:8778/', { waitUntil: 'networkidle' });
console.log(await p.evaluate(() => {
  const m = s => { const el = document.querySelector(s); if (!el) return s + ': fehlt'; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return `${s}: left=${Math.round(r.left)} w=${Math.round(r.width)} right=${Math.round(r.right)} display=${cs.display} pos=${cs.position} transform=${cs.transform}`; };
  return ['html', 'body', '.nav', '.nav__in', '.nav__logo', '.logo', '.nav__claim', '.nav__menu', '.nav__r', '.nav__lang', '.burger', '.mmenu', 'main', '.hero', '.demobar', '.fuss', '.fuss__kurve', '.skip'].map(m).join('\n') + `\nscrollWidth html ${document.documentElement.scrollWidth} body ${document.body.scrollWidth} | css geladen: ${[...document.styleSheets].map(s => s.href && s.href.split('/').pop()).join(',')}`;
}));
await b.close();
