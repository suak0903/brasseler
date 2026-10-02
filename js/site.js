/* Brasseler Redesign-Entwurf, Seitenlogik (Vega 02.10.2026). Alles elementgeprüft, ein Skript für alle Seiten.
   1 Kopfleiste scrolled · 2 mobiles Menü mit Aufklappern · 3 Reveal · 4 Lightbox · 5 Demo-Leiste (gemerkt je Sitzung)
   6 Hintergrundvideos: erst laden, wenn sichtbar, Poster bleibt bis dahin (Ladeleistung) */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* 1 */
  var nav = document.getElementById('nav');
  if (nav) {
    var setScrolled = function () { nav.classList.toggle('scrolled', window.scrollY > 20); };
    setScrolled(); window.addEventListener('scroll', setScrolled, { passive: true });
  }

  /* 2 */
  var burger = document.getElementById('burger'), mmenu = document.getElementById('mmenu');
  if (burger && mmenu && nav) {
    mmenu.hidden = true; mmenu.setAttribute('inert', '');
    // Kein overflow-Lock auf body (Design-Kit): der Hintergrund darf weiterscrollen, das Panel hält sich per overscroll-behavior
    var oeffnen = function () { mmenu.hidden = false; void mmenu.offsetWidth; mmenu.classList.add('open'); mmenu.removeAttribute('inert'); nav.classList.add('menu-open'); burger.setAttribute('aria-expanded', 'true'); };
    var schliessen = function () { mmenu.classList.remove('open'); mmenu.setAttribute('inert', ''); nav.classList.remove('menu-open'); burger.setAttribute('aria-expanded', 'false'); window.setTimeout(function () { if (!mmenu.classList.contains('open')) mmenu.hidden = true; }, 420); };
    burger.addEventListener('click', function () { mmenu.classList.contains('open') ? schliessen() : oeffnen(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && mmenu.classList.contains('open')) schliessen(); });
    document.addEventListener('click', function (e) { if (mmenu.classList.contains('open') && !e.target.closest('#mmenu') && !e.target.closest('#burger')) schliessen(); });
    mmenu.addEventListener('click', function (e) {
      var plus = e.target.closest('.nav__plus');
      if (plus) { var li = plus.closest('.nav__li--sub'); var auf = li.classList.toggle('auf'); plus.setAttribute('aria-expanded', auf ? 'true' : 'false'); return; }
      if (e.target.closest('a')) schliessen();
    });
    var sx = 0, sy = 0;
    mmenu.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
    mmenu.addEventListener('touchend', function (e) { var dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy; if (dx > 55 && Math.abs(dx) > Math.abs(dy)) schliessen(); }, { passive: true });
    window.addEventListener('resize', function () { if (window.innerWidth >= 1024 && mmenu.classList.contains('open')) schliessen(); });
  }

  /* 3 Reveal; Kacheln und Karten innerhalb eines Rasters gestaffelt (Divi-Muster des Bestands: Sektionen gleiten ein) */
  var rvs = document.querySelectorAll('.rv');
  Array.prototype.forEach.call(document.querySelectorAll('.teaser, .karten2, .zahlen, .news, .sm__raster'), function (r) {
    Array.prototype.forEach.call(r.children, function (k, i) { if (k.classList.contains('rv')) k.style.transitionDelay = Math.min(i * 90, 540) + 'ms'; });
  });
  if (rvs.length) {
    if (!('IntersectionObserver' in window) || reduce) { Array.prototype.forEach.call(rvs, function (el) { el.classList.add('in'); }); }
    else {
      var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { rootMargin: '0px 0px -6% 0px', threshold: 0.05 });
      Array.prototype.forEach.call(rvs, function (el) { io.observe(el); });
    }
  }
  /* 3a News blättern: zwölf je Klick */
  var mehr = document.getElementById('newsMehr');
  if (mehr) mehr.addEventListener('click', function () {
    var rest = document.querySelectorAll('.news__i.weiter'); for (var i = 0; i < rest.length && i < 12; i++) { rest[i].classList.remove('weiter'); rest[i].classList.add('in'); }
    if (document.querySelectorAll('.news__i.weiter').length === 0) mehr.parentNode.removeChild(mehr);
  });
  /* 3b Zahlen zählen hoch, wie die Divi-Zähler des Bestands; nur Ziffern, Tausenderpunkt bleibt */
  var zahlen = document.querySelectorAll('.zahlen__z');
  if (zahlen.length && !reduce && 'IntersectionObserver' in window) {
    var zio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return; zio.unobserve(e.target);
        var el = e.target, text = el.textContent.trim(), ziel = parseInt(text.replace(/\D/g, ''), 10);
        if (!ziel) return;
        var start = null, dauer = 1400, fmt = function (n) { var s = String(n); return text.indexOf('.') > -1 ? s.replace(/\B(?=(\d{3})+(?!\d))/g, '.') : s; };
        var tick = function (ts) { if (!start) start = ts; var p = Math.min(1, (ts - start) / dauer); p = 1 - Math.pow(1 - p, 3); el.textContent = fmt(Math.round(ziel * p)); if (p < 1) window.requestAnimationFrame(tick); else el.textContent = text; };
        window.requestAnimationFrame(tick);
      });
    }, { threshold: 0.4 });
    Array.prototype.forEach.call(zahlen, function (z) { zio.observe(z); });
  }

  /* 4 */
  var lb = document.getElementById('lb');
  var knoepfe = Array.prototype.slice.call(document.querySelectorAll('[data-lb]'));
  if (lb && knoepfe.length) {
    var lbImg = lb.querySelector('img'), lbCount = lb.querySelector('.lb__count'), index = 0;
    var zeigen = function (i) { index = (i + knoepfe.length) % knoepfe.length; var q = knoepfe[index].querySelector('img'); lbImg.src = knoepfe[index].dataset.full || q.currentSrc || q.src; lbImg.alt = q.alt || ''; if (lbCount) lbCount.textContent = knoepfe.length > 1 ? (index + 1) + ' / ' + knoepfe.length : ''; };
    var auf = function (i) { zeigen(i); lb.hidden = false; document.body.style.overflow = 'hidden'; lb.querySelector('.lb__close').focus(); };
    var zu = function () { lb.hidden = true; document.body.style.overflow = ''; };
    knoepfe.forEach(function (b, i) { b.addEventListener('click', function () { auf(i); }); });
    if (knoepfe.length < 2) { lb.querySelector('.lb__prev').hidden = true; lb.querySelector('.lb__next').hidden = true; }
    lb.querySelector('.lb__close').addEventListener('click', zu);
    lb.querySelector('.lb__prev').addEventListener('click', function () { zeigen(index - 1); });
    lb.querySelector('.lb__next').addEventListener('click', function () { zeigen(index + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) zu(); });
    document.addEventListener('keydown', function (e) { if (lb.hidden) return; if (e.key === 'Escape') zu(); if (e.key === 'ArrowLeft') zeigen(index - 1); if (e.key === 'ArrowRight') zeigen(index + 1); });
    var lx = 0;
    lb.addEventListener('touchstart', function (e) { lx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (e) { var d = e.changedTouches[0].clientX - lx; if (Math.abs(d) > 50) zeigen(index + (d < 0 ? 1 : -1)); }, { passive: true });
  }

  /* 5 */
  // Die Leiste kommt bei jedem Laden wieder (Suat 02.10.2026), kein Merken in der Sitzung
  var demobar = document.getElementById('demobar'), demoClose = document.getElementById('demoClose');
  if (demobar) window.setTimeout(function () { demobar.classList.add('da'); }, 60);  // fadet langsam ein (CSS-Übergang mit Verzögerung)
  if (demoClose) demoClose.addEventListener('click', function () { demobar.classList.add('hide'); document.body.classList.add('demobar-zu'); });

  /* 6 */
  var videos = document.querySelectorAll('video[data-src-mp4]');
  var starten = function (v) {
    if (v.dataset.geladen) return; v.dataset.geladen = '1';
    var kann = !!v.dataset.srcWebm && v.canPlayType('video/webm; codecs="vp9"');  // WebM nur, wenn der Generator sie angeboten hat
    var s = document.createElement('source'); s.src = kann ? v.dataset.srcWebm : v.dataset.srcMp4; s.type = kann ? 'video/webm' : 'video/mp4'; v.appendChild(s);
    if (!kann) { var s2 = document.createElement('source'); s2.src = v.dataset.srcMp4; s2.type = 'video/mp4'; v.appendChild(s2); }
    v.load(); var p = v.play(); if (p && p.catch) p.catch(function () { /* Autoplay verweigert, Poster bleibt */ });
    v.addEventListener('playing', function () { v.classList.add('an'); }, { once: true });
  };
  // Erst nach dem Laden der Seite und einer kurzen Pause: load() des Hero-Videos lag sonst im selben Task wie der Skriptstart
  // und machte daraus 500 bis 750 ms Blockierzeit (Lighthouse live 02.10.2026). Das Poster steht so lange.
  var videosAn = function () {
    if ('IntersectionObserver' in window) {
      var vio = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { starten(e.target); vio.unobserve(e.target); } }); }, { rootMargin: '200px 0px' });
      Array.prototype.forEach.call(videos, function (v) { vio.observe(v); });
    } else { Array.prototype.forEach.call(videos, starten); }
  };
  // Start direkt nach dem Laden, auch auf dem Handy (Suat 02.10.2026: „das Video sollte schon direkt anfangen“). Der Start
  // kostet Stil- und Layoutarbeit (Faber F5), das nehmen wir für den sofortigen Start in Kauf; die Messung sagt es dazu.
  if (videos.length && !reduce) {
    if (document.readyState === 'complete') videosAn(); else window.addEventListener('load', videosAn, { once: true });
  }
})();
