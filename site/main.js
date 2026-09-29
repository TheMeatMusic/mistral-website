/* Mistral Électrique · three behaviours, no dependencies.
   1. Logo intro: the mark's three bands open onto the hero photo (~1.5 s).
      Once per browser session, skipped under reduced motion, cut short by any click or key.
   2. Phone menu: full-screen sheet below 900 px.
   3. Sticky bar: hidden going down, back on scroll-up once the original nav has left the screen. */
(function () {
  'use strict';
  var fold = document.querySelector('.fold');
  var nav = fold.querySelector('.nav');

  /* ---------- 1. logo intro ---------- */
  var intro = document.getElementById('intro');
  var runs = [];
  function endIntro() {
    runs.forEach(function (r) { r.cancel(); });
    runs = [];
    intro.hidden = true;
  }
  function playIntro() {
    var photo = document.getElementById('introPhoto');
    var mark = document.getElementById('introMark');
    var ground = intro.querySelector('.intro-ground');
    // the mask is the mark's own geometry, traced from mark-dark.png (viewBox 256 x 240)
    var MASK = 'url("data:image/svg+xml,' + encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 240">' +
      '<polygon points="0,63 185,0 256,0 256,28 70,92 0,92"/>' +
      '<polygon points="0,134 185,70 256,70 256,105 70,169 0,169"/>' +
      '<polygon points="0,205 185,141 256,141 256,175 70,239 0,239"/></svg>') + '")';
    ['webkitMask', 'mask'].forEach(function (k) { photo.style[k] = MASK + ' center / 180px auto no-repeat'; });

    intro.hidden = false;
    var box = intro.getBoundingClientRect();
    var W0 = 180, W1 = Math.max(box.width, box.height) * 16;   // the middle band alone then covers the frame
    var OUT = 'cubic-bezier(.16,1,.3,1)', INOUT = 'cubic-bezier(.76,0,.24,1)';
    function a(el, kf, delay, dur, easing) {
      if (el) runs.push(el.animate(kf, { delay: delay, duration: dur, easing: easing || OUT, fill: 'both' }));
    }
    [].forEach.call(mark.querySelectorAll('polygon'), function (p, i) {
      a(p, [{ opacity: 0, transform: 'translateX(-28px)' }, { opacity: 1, transform: 'none' }], i * 90, 370);
    });
    a(photo, [{ opacity: 0 }, { opacity: 1 }], 550, 300, 'linear');
    a(photo, [{ webkitMaskSize: W0 + 'px auto', maskSize: W0 + 'px auto' },
              { webkitMaskSize: W1 + 'px auto', maskSize: W1 + 'px auto' }], 850, 700, INOUT);
    a(mark, [{ transform: 'translate(-50%,-50%) scale(1)', opacity: 1 },
             { transform: 'translate(-50%,-50%) scale(' + (W1 / W0) + ')', opacity: 0 }], 850, 700, INOUT);
    a(ground, [{ opacity: 1 }, { opacity: 0 }], 1150, 400, 'linear');
    [fold.querySelector('.lift'), fold.querySelector('.ticks')].forEach(function (el, i) {
      a(el, [{ opacity: 0, transform: 'translateY(32px)' }, { opacity: 1, transform: 'none' }], 1000 + i * 90, 520);
    });
    a(nav, [{ opacity: 0, transform: 'translateY(-16px)' }, { opacity: 1, transform: 'none' }], 1080, 460);
    Promise.all(runs.map(function (r) { return r.finished; })).then(endIntro, function () {});
    fold.addEventListener('pointerdown', endIntro, { once: true });
    document.addEventListener('keydown', endIntro, { once: true });
  }
  var calm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var seen = false;
  try { seen = !!sessionStorage.getItem('mistral-intro'); sessionStorage.setItem('mistral-intro', '1'); } catch (e) {}
  if (!calm && !seen && fold.animate) playIntro();

  /* ---------- 2. phone menu ---------- */
  var sheet = document.getElementById('sheet');
  var openers = [].slice.call(document.querySelectorAll('[data-menu]'));
  var lastOpener = null;
  function setMenu(open, opener) {
    sheet.hidden = !open;
    openers.forEach(function (b) { b.setAttribute('aria-expanded', open ? 'true' : 'false'); });
    document.documentElement.style.overflow = open ? 'hidden' : '';
    if (open) { lastOpener = opener; document.getElementById('close').focus(); }
    else if (lastOpener) lastOpener.focus();
  }
  openers.forEach(function (b) { b.addEventListener('click', function () { setMenu(true, b); }); });
  document.getElementById('close').addEventListener('click', function () { setMenu(false); });
  [].forEach.call(sheet.querySelectorAll('a'), function (l) { l.addEventListener('click', function () { lastOpener = null; setMenu(false); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !sheet.hidden) setMenu(false); });
  addEventListener('resize', function () { if (!sheet.hidden && innerWidth > 900) setMenu(false); });

  /* ---------- 3. sticky bar ---------- */
  var bar = document.getElementById('bar');
  var lastY = scrollY, ticking = false;
  bar.addEventListener('focusin', function () { bar.classList.add('on'); });
  function onScroll() {
    var y = scrollY, past = y > nav.offsetTop + nav.offsetHeight;
    if (!past) bar.classList.remove('on');
    else if (y < lastY - 4) bar.classList.add('on');
    else if (y > lastY + 4 && !bar.contains(document.activeElement)) bar.classList.remove('on');
    lastY = y;
    ticking = false;
  }
  addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
})();
