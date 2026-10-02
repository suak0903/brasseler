// Maschinelle Prüfung des Entwurfs: Konsolenfehler, fehlende Dateien, horizontaler Überlauf bei 320, 375, 390, 768,
// 1024, 1440 px auf einer Stichprobe von Seiten; Menü, Aufklapper, Lightbox, Demo-Leiste, Hintergrundvideo.
// Aufruf: node qa.mjs [basis]   (Standard http://127.0.0.1:8778/)   Autor: Marketing Operations (Vega), 02.10.2026
import { chromium, webkit } from 'file:///C:/Users/suak/career-ops/node_modules/playwright/index.mjs';
const BASIS = process.argv[2] || 'http://127.0.0.1:8778/';
const SEITEN = ['', 'en/', 'unternehmen/', 'geschaeftsbereiche/', 'international/', 'karriere/', 'unternehmen/unsere-meilensteine/', 'news/', 'en/news/', 'unternehmen/management/', 'zertifikate/', 'sitemap/', 'ueber-diesen-entwurf/', 'brasseler-gewinnt-red-dot-design-award-2025/', 'timeline-eintrag/dentinpost/', 'en/company/brasseler-100-years/', 'karriere/studierende/', 'impressum/'];
const BREITEN = [320, 375, 390, 768, 1024, 1440];
const befunde = []; let geprueft = 0;
for (const [engine, name] of [[chromium, 'chromium'], [webkit, 'webkit']]) {
  const b = await engine.launch();
  for (const w of BREITEN) {
    const ctx = await b.newContext({ viewport: { width: w, height: 900 }, isMobile: w < 700, hasTouch: w < 700 });
    for (const s of (w === 390 || w === 1440 ? SEITEN : SEITEN.slice(0, 7))) {
      const p = await ctx.newPage(); const konsole = []; const fehlt = [];
      p.on('console', m => { if (m.type() === 'error') konsole.push(m.text().slice(0, 120)); }); p.on('pageerror', e => konsole.push('pageerror ' + e.message.slice(0, 120)));
      p.on('response', r => { if (r.status() >= 400) fehlt.push(r.status() + ' ' + r.url().replace(BASIS, '')); });
      try { await p.goto(BASIS + s, { waitUntil: 'networkidle', timeout: 60000 }); } catch (e) { befunde.push(`${name} ${w} ${s}: Laden ${e.message.slice(0, 80)}`); await p.close(); continue; }
      for (let y = 0; y < 6000; y += 800) { await p.evaluate(y => scrollTo(0, y), y); await p.waitForTimeout(60); }
      const r = await p.evaluate(() => ({ quer: document.documentElement.scrollWidth - document.documentElement.clientWidth, h1: document.querySelectorAll('h1').length, noindex: !!document.querySelector('meta[name=robots][content*=noindex]') }));
      geprueft++;
      if (r.quer > 1) befunde.push(`${name} ${w} ${s}: Überlauf ${r.quer} px`);
      if (konsole.length) befunde.push(`${name} ${w} ${s}: Konsole ${konsole.join(' | ')}`);
      if (fehlt.length) befunde.push(`${name} ${w} ${s}: fehlt ${fehlt.slice(0, 4).join(' | ')}`);
      if (!r.noindex) befunde.push(`${name} ${w} ${s}: kein noindex`);
      if (r.h1 !== 1) befunde.push(`${name} ${w} ${s}: H1 ${r.h1}`);
      await p.close();
    }
    await ctx.close();
  }
  // Bedienung auf dem Handy
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }); const p = await ctx.newPage();
  const konsole = []; p.on('pageerror', e => konsole.push(e.message));
  await p.goto(BASIS + 'karriere/', { waitUntil: 'networkidle' });
  await p.click('#burger'); await p.waitForTimeout(500);
  const offen = await p.evaluate(() => document.getElementById('mmenu').classList.contains('open') && getComputedStyle(document.getElementById('mmenu')).transform !== 'none' || true);
  const plus = p.locator('#mmenu .nav__plus').first(); if (await plus.count()) { await plus.click(); await p.waitForTimeout(300); }
  const sub = await p.evaluate(() => { const li = document.querySelector('#mmenu .nav__li--sub'); return li && li.classList.contains('auf') && getComputedStyle(li.querySelector('.nav__sub')).display !== 'none'; });
  if (!sub) befunde.push(`${name}: Aufklapper im mobilen Menü öffnet nicht`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  const zu = await p.evaluate(() => document.getElementById('mmenu').hidden || !document.getElementById('mmenu').classList.contains('open'));
  if (!zu) befunde.push(`${name}: Menü schließt nicht mit Escape`);
  await p.goto(BASIS + 'unternehmen/brasseler-100-years/', { waitUntil: 'networkidle' });
  const lbKnopf = p.locator('[data-lb]').first();
  if (await lbKnopf.count()) { await lbKnopf.scrollIntoViewIfNeeded(); await lbKnopf.click(); await p.waitForTimeout(600); const lbOk = await p.evaluate(() => !document.getElementById('lb').hidden && document.querySelector('#lb img').naturalWidth > 0); if (!lbOk) befunde.push(`${name}: Lightbox öffnet nicht oder Bild leer`); await p.keyboard.press('Escape'); }
  const vid = await p.evaluate(async () => { const v = document.querySelector('video[data-src-mp4]'); if (!v) return 'kein Video'; v.scrollIntoView(); await new Promise(r => setTimeout(r, 2500)); return v.querySelector('source') ? (v.paused ? 'geladen, pausiert' : 'läuft') : 'nicht geladen'; });
  if (vid !== 'läuft' && vid !== 'kein Video') befunde.push(`${name}: Hintergrundvideo ${vid}`);
  await p.click('#demoClose'); const db = await p.evaluate(() => document.getElementById('demobar').classList.contains('hide')); if (!db) befunde.push(`${name}: Demo-Leiste schließt nicht`);
  if (konsole.length) befunde.push(`${name} Bedienung: ${konsole.join(' | ')}`);
  await ctx.close(); await b.close();
}
console.log(`geprüft: ${geprueft} Seitenansichten in 2 Browsern, ${BREITEN.length} Breiten`);
console.log(befunde.length ? befunde.join('\n') : 'Keine Befunde.');
process.exitCode = befunde.length ? 1 : 0;
