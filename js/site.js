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
    var oeffnen = function () { mmenu.hidden = false; void mmenu.offsetWidth; mmenu.classList.add('open'); mmenu.removeAttribute('inert'); nav.classList.add('menu-open'); burger.setAttribute('aria-expanded', 'true'); document.body.style.overflow = 'hidden'; };
    var schliessen = function () { mmenu.classList.remove('open'); mmenu.setAttribute('inert', ''); nav.classList.remove('menu-open'); burger.setAttribute('aria-expanded', 'false'); document.body.style.overflow = ''; window.setTimeout(function () { if (!mmenu.classList.contains('open')) mmenu.hidden = true; }, 380); };
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

  /* 3 */
  var rvs = document.querySelectorAll('.rv');
  if (rvs.length) {
    if (!('IntersectionObserver' in window) || reduce) { Array.prototype.forEach.call(rvs, function (el) { el.classList.add('in'); }); }
    else {
      var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { rootMargin: '0px 0px -6% 0px', threshold: 0.05 });
      Array.prototype.forEach.call(rvs, function (el) { io.observe(el); });
    }
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
  var demobar = document.getElementById('demobar'), demoClose = document.getElementById('demoClose');
  var zuMerken = false; try { zuMerken = window.sessionStorage.getItem('brasseler-demo-zu') === '1'; } catch (e) { zuMerken = false; }
  if (demobar && zuMerken) { demobar.classList.add('hide'); document.body.classList.add('demobar-zu'); }
  if (demoClose) demoClose.addEventListener('click', function () { demobar.classList.add('hide'); document.body.classList.add('demobar-zu'); try { window.sessionStorage.setItem('brasseler-demo-zu', '1'); } catch (e) { /* Privatmodus */ } });

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
  // und machte daraus 500 bis 750 ms Blockierzeit (Lighthouse live 03.10.2026). Das Poster steht so lange.
  var videosAn = function () {
    if ('IntersectionObserver' in window) {
      var vio = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { starten(e.target); vio.unobserve(e.target); } }); }, { rootMargin: '200px 0px' });
      Array.prototype.forEach.call(videos, function (v) { vio.observe(v); });
    } else { Array.prototype.forEach.call(videos, starten); }
  };
  // Auf Touch-Geräten erst bei der ersten Berührung oder dem ersten Scrollen: das Einfügen der Quellen löst Stil- und
  // Layoutarbeit von mehreren hundert Millisekunden aus (Faber F5, styleLayout 1,3 s), die sonst in die Ladezeit fällt.
  if (videos.length && !reduce) {
    var gestartet = false;
    var los = function () { if (gestartet) return; gestartet = true; videosAn(); };
    var touch = window.matchMedia('(pointer: coarse)').matches;
    var spaeter = function () {
      if (!touch) { window.setTimeout(los, 400); return; }
      ['touchstart', 'scroll', 'pointerdown', 'keydown'].forEach(function (ev) { window.addEventListener(ev, los, { once: true, passive: true }); });
    };
    if (document.readyState === 'complete') spaeter(); else window.addEventListener('load', spaeter, { once: true });
  }
})();
