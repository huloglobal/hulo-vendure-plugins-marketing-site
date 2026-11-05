/* hulo-ui.js: progressive enhancement for huloglobal.com's generated plugin
   pages. Every page reads completely without it: this file only turns markup
   that is already there into tabs, filters, a lightbox and so on. Vanilla JS,
   no dependencies, loaded with `defer` (minified into dist by build_css.mjs).

   html.hu-js is set in <head> before this file loads, so hulo-ui.css can lay
   the page out the way this script will leave it (no jump when it runs).
   When it has run, html.hu-ui is set; if the file fails to load, the
   <script> tag's onerror (or, failing that, a timer in <head>) removes hu-js
   and the page falls back to its scripts-off layout. A widget that throws
   is marked .hu-failed and shows its plain HTML; the others still work. */
(function () {
  'use strict';

  var doc = document, root = doc.documentElement, body = doc.body;
  var motionQuery = window.matchMedia ? matchMedia('(prefers-reduced-motion: reduce)') : null;
  function reduced() { return !!(motionQuery && motionQuery.matches); }
  function all(sel, ctx) { return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel)); }
  function has(list, word) { return (' ' + (list || '') + ' ').indexOf(' ' + word + ' ') >= 0; }
  function el(tag, cls, text) {
    var n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text) n.textContent = text;
    return n;
  }
  function stored(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (e) { /* private mode: no memory, no problem */ }
    return null;
  }
  function svg(paths) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + paths + '</svg>';
  }
  function keyboardFocus(n) {
    try { return n.matches(':focus-visible'); } catch (e) { return true; }
  }
  function onScroll(fn) {
    var queued = false;
    function run() { queued = false; fn(); }
    function queue() { if (!queued) { queued = true; requestAnimationFrame(run); } }
    addEventListener('scroll', queue, { passive: true });
    addEventListener('resize', queue);
    return queue;
  }
  // A widget that throws shows its plain HTML (hu-failed) instead of a
  // half-built control; the error still reaches the console.
  function failed(n, e) {
    if (n && n.classList) {
      n.classList.add('hu-failed');
      all('.hu-needs-js', n).forEach(function (c) { c.classList.add('hu-failed'); });
    }
    setTimeout(function () { throw e; });
  }
  function each(sel, fn) {
    all(sel).forEach(function (n) { try { fn(n); } catch (e) { failed(n, e); } });
  }
  function safely(fn) { try { fn(); } catch (e) { failed(null, e); } }
  // Things to undo for printing (every tab panel, plan and release prints).
  var printHooks = [];
  // After Back / Forward without the back-forward cache the browser puts
  // back which radio was checked, possibly after this script has run: each
  // widget re-reads its checked radio on pageshow so what is shown matches
  // the highlighted chip or plan.
  var syncs = [];

  // Polite live region for short status messages. While a modal dialog is
  // open everything outside it is inert, so messages go to the dialog's own
  // region ([data-live] inside it) instead.
  var live = el('div', 'sr-only');
  live.setAttribute('role', 'status');
  live.setAttribute('aria-atomic', 'true');
  body.appendChild(live);
  var liveTimer;
  function announce(msg) {
    var dlg = doc.querySelector('dialog[open]');
    var region = (dlg && dlg.querySelector('[data-live]')) || live;
    clearTimeout(liveTimer);
    live.textContent = '';
    region.textContent = '';
    liveTimer = setTimeout(function () { region.textContent = msg; }, 80);
  }

  // ── Sticky offsets ──
  // Which bars stick is decided in CSS (the section bar replaces the header
  // on phones; nothing sticks on very short screens). The script measures
  // their real heights for the offsets; stickyHeight() counts only the bars
  // that are sticky right now.
  var header = doc.querySelector('body > header');
  var secnav = doc.querySelector('.hu-secnav');
  function isSticky(n) { return !!n && getComputedStyle(n).position === 'sticky'; }
  function stickyHeight() { return (isSticky(header) ? header.offsetHeight : 0) + (isSticky(secnav) ? secnav.offsetHeight : 0); }
  function measure() {
    if (header) root.style.setProperty('--hu-header-h', header.offsetHeight + 'px');
    if (secnav) root.style.setProperty('--hu-secnav-h', secnav.offsetHeight + 'px');
  }
  if (secnav) root.classList.add('hu-has-secnav');
  measure();
  if (window.ResizeObserver) {
    var ro = new ResizeObserver(measure);
    if (header) ro.observe(header);
    if (secnav) ro.observe(secnav);
  } else {
    addEventListener('resize', measure);
  }

  // ── Keyboard focus on something taller than the screen ──
  // A tab panel or a scrolling table that takes focus: when it is taller
  // than the room between the sticky bars and the bottom scroll padding,
  // browsers centre it, or line up its bottom edge, so its top (heading,
  // column headers, the top of its focus ring) ends up under the bars or
  // above the screen. Show its top instead (scroll-padding and the element's
  // scroll-margin keep it clear of the bars). Keyboard focus only: a click
  // never moves the page.
  // The lowest a top may sit and still count as shown: above the bottom
  // scroll padding, with room under it for a heading.
  var HEAD_ROOM = 64;
  function padBottom() { return parseFloat(getComputedStyle(root).scrollPaddingBottom) || 0; }
  function lowestTop() { return innerHeight - padBottom() - HEAD_ROOM; }
  function topHidden(n) {
    var t = n.getBoundingClientRect().top;
    return t < stickyHeight() - 1 || t > lowestTop();
  }
  function showTop(n) { if (topHidden(n)) n.scrollIntoView({ block: 'start' }); }
  function showTopOnFocus(n) {
    n.addEventListener('focus', function () {
      if (n.huOwnFocus || !keyboardFocus(n)) return;
      // The focus event comes after the browser's own scroll, or, with smooth
      // scrolling, as it starts: decide from where the element is now.
      var r = n.getBoundingClientRect(), line = stickyHeight();
      var act = r.height > innerHeight - padBottom() - line && (r.top < line - 1 || r.top > lowestTop());
      requestAnimationFrame(function () {
        if (doc.activeElement !== n) return;
        if (act || n.getBoundingClientRect().top < stickyHeight() - 1) n.scrollIntoView({ block: 'start' });
      });
    });
  }
  // Focus n without the browser's scroll, then show its top if need be.
  function focusTop(n) {
    n.huOwnFocus = true;
    n.focus({ preventScroll: true });
    n.huOwnFocus = false;
    showTop(n);
  }

  // ── Horizontal scrollers with edge fades (section bar, category chips,
  // wide tables): .is-overflowing while the content is wider than the box,
  // .is-scrolled once it has moved off its start, .is-end at its end; the
  // CSS fades (or shades) only the edges that hide something. ──
  function fadeScroller(box) {
    function hint() {
      var over = box.scrollWidth > box.clientWidth + 1;
      box.classList.toggle('is-overflowing', over);
      box.classList.toggle('is-scrolled', over && box.scrollLeft > 2);
      box.classList.toggle('is-end', !over || box.scrollLeft + box.clientWidth >= box.scrollWidth - 2);
    }
    box.addEventListener('scroll', hint, { passive: true });
    addEventListener('resize', hint);
    if (window.ResizeObserver) new ResizeObserver(hint).observe(box);
    hint();
    return hint;
  }
  var FADE = 48; // the faded edge (2.5rem) plus a little air
  // Keep an item clear of a fading scroller's edges.
  function keepInView(box, item, instant) {
    if (!box || box.scrollWidth <= box.clientWidth + 1) return;
    var bl = box.getBoundingClientRect().left, ir = item.getBoundingClientRect();
    var l = ir.left - bl + box.scrollLeft, r = l + ir.width, s = box.scrollLeft, w = box.clientWidth, to = null;
    if (l < s + FADE) to = Math.max(0, l - FADE);
    else if (r > s + w - FADE) to = Math.min(box.scrollWidth - w, r - w + FADE);
    if (to !== null && Math.abs(to - s) > 1) box.scrollTo({ left: to, behavior: instant || reduced() ? 'auto' : 'smooth' });
  }
  // Keyboard focus inside a scroller: keep the focused item clear of the
  // fades. Not for a mouse: scrolling the row under a button that is still
  // down would move the target away before the click lands.
  function keepFocusInView(box, itemSel) {
    box.addEventListener('focusin', function (e) {
      var item = e.target.closest && e.target.closest(itemSel);
      if (item && keyboardFocus(e.target)) keepInView(box, item, true);
    });
  }

  // ── Section bar / manual contents: scrollspy. ──
  function initSpy(nav) {
    var items = [];
    all('a[href^="#"]', nav).forEach(function (a) {
      var target = doc.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)));
      if (target) items.push({ a: a, el: target });
    });
    if (!items.length) return;
    var list = nav.querySelector('ul');
    var active = null, pinned = null, pinBase = null, settle = 0;
    function isBeside(it) { return getComputedStyle(it.el).position === 'sticky'; }
    function current() {
      var line = stickyHeight() + 40, cur = items[0];
      items.forEach(function (it) {
        if (!isBeside(it) && it.el.getBoundingClientRect().top <= line) cur = it;
      });
      if (innerHeight + scrollY >= root.scrollHeight - 4) {
        for (var i = items.length - 1; i >= 0; i--) {
          if (!isBeside(items[i]) && items[i].el.getBoundingClientRect().top < innerHeight) { cur = items[i]; break; }
        }
      }
      return cur;
    }
    function mark(it) {
      if (active === it) return;
      if (active) active.a.removeAttribute('aria-current');
      active = it;
      it.a.setAttribute('aria-current', 'true');
      // Not while the keyboard is in the bar: focus decides what is in view.
      var kb = false;
      try { kb = !!list && list.contains(doc.activeElement) && doc.activeElement.matches(':focus-visible'); } catch (e) { kb = false; }
      if (!kb && list) keepInView(list, it.a.parentNode);
    }
    function update() {
      var cur = current();
      if (pinned) {
        if (pinBase === null) {
          clearTimeout(settle);
          settle = setTimeout(function () { pinBase = current(); update(); }, 180);
          return mark(pinned);
        }
        if (cur === pinBase) return mark(pinned);
        pinned = null;
      }
      mark(cur);
    }
    items.forEach(function (it) {
      it.a.addEventListener('click', function () {
        pinned = it; pinBase = null;
        mark(it);
        update();
      });
    });
    var hint = list && list.classList.contains('hu-secnav-list') ? fadeScroller(list) : function () {};
    if (list) keepFocusInView(list, 'li');
    onScroll(function () { update(); hint(); });
    update();
  }

  // ── Tabs (WAI-ARIA tabs pattern, horizontal, automatic activation). ──
  var groups = {}, uid = 0;
  var FOCUSABLE = 'a[href], button, input, select, textarea, [tabindex]';
  // A panel whose first content (a heading, a paragraph, a code sample…) is
  // not focusable is a tab stop itself, as the tabs pattern says: Tab from
  // the selected tab then lands on the top of the panel (its heading), not on
  // a link far down inside it. The heading each panel carries for the
  // scripts-off and print layouts (.hu-tab-h) is not shown here, so it is
  // skipped.
  var CONTENT = 'h1, h2, h3, h4, h5, h6, p, ul, ol, dl, pre, table, figure, blockquote, img, [data-copy], ' + FOCUSABLE;
  function startsFocusable(p) {
    var c = all(CONTENT, p);
    for (var i = 0; i < c.length; i++) {
      var n = c[i];
      if (n.closest('.hu-tab-h, .sr-only')) continue;
      if (n.matches(FOCUSABLE)) return true;
      if (n.tagName === 'IMG' || (n.textContent || '').trim()) return false;
    }
    return false;
  }
  // The label in one inner span (the tab is a flex box: separate text runs
  // would be separate flex items that never wrap together), with a
  // hyphenated word ("add-on") kept on one line: a tab is never narrower
  // than its longest word (hulo-ui.css), so a label wraps between words,
  // never inside one.
  function tabLabel(t, text) {
    var l = el('span', 'hu-tab-l');
    text.split(' ').forEach(function (w, k) {
      if (k) l.appendChild(doc.createTextNode(' '));
      l.appendChild(w.indexOf('-') > 0 ? el('span', 'hu-nobr', w) : doc.createTextNode(w));
    });
    t.appendChild(l);
  }
  function initTabs(box) {
    var panels = all('[data-tab]', box).filter(function (p) { return p.parentNode === box; });
    if (panels.length < 2) return;
    var group = box.getAttribute('data-tabs-group');
    var list = el('div', 'hu-tablist');
    list.setAttribute('role', 'tablist');
    if (box.getAttribute('data-tabs-label')) list.setAttribute('aria-label', box.getAttribute('data-tabs-label'));
    // Arrow keys follow the tablist's orientation: Left / Right here, Up /
    // Down only for a vertical one (data-tabs-orientation="vertical").
    var vertical = box.getAttribute('data-tabs-orientation') === 'vertical';
    if (vertical) list.setAttribute('aria-orientation', 'vertical');
    var current = 0;
    var tabs = panels.map(function (p, i) {
      if (!p.id) p.id = 'hu-panel-' + (++uid);
      var t = el('button', 'hu-tab');
      tabLabel(t, p.getAttribute('data-tab'));
      t.type = 'button';
      t.id = p.id + '-tab';
      t.setAttribute('role', 'tab');
      t.setAttribute('aria-controls', p.id);
      p.setAttribute('role', 'tabpanel');
      p.setAttribute('aria-labelledby', t.id);
      if (!startsFocusable(p)) { p.tabIndex = 0; showTopOnFocus(p); }
      t.addEventListener('click', function () { select(i, true); });
      t.addEventListener('keydown', function (e) {
        if (e.key === 'Tab') {
          // Tab from the selected tab onto its panel (the next tab stop when
          // the panel is focusable itself): move focus without the browser's
          // scroll, which centres a tall panel that starts near the foot of
          // the window, and show the panel's top instead.
          var panel = panels[i];
          if (e.shiftKey || e.altKey || e.ctrlKey || e.metaKey || i !== current || panel.hidden || panel.getAttribute('tabindex') !== '0') return;
          e.preventDefault();
          focusTop(panel);
          return;
        }
        var n = tabs.length, j = -1;
        var next = vertical ? 'ArrowDown' : 'ArrowRight', prev = vertical ? 'ArrowUp' : 'ArrowLeft';
        if (e.key === next) j = (i + 1) % n;
        else if (e.key === prev) j = (i - 1 + n) % n;
        else if (e.key === 'Home') j = 0;
        else if (e.key === 'End') j = n - 1;
        if (j < 0) return;
        e.preventDefault();
        tabs[j].focus();
        select(j, true);
      });
      list.appendChild(t);
      return t;
    });
    panels[0].parentNode.insertBefore(list, panels[0]);
    box.classList.add('hu-tabs-on');
    fadeScroller(list);
    keepFocusInView(list, '.hu-tab');
    function select(i, byUser) {
      current = i;
      tabs.forEach(function (t, j) {
        var on = i === j;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.tabIndex = on ? 0 : -1;
        panels[j].hidden = !on;
      });
      if (byUser && group) {
        var label = tabs[i].textContent;
        if (!panels[i].hasAttribute('data-tab-nopersist')) stored('hulo-tab-' + group, label);
        (groups[group] || []).forEach(function (other) { if (other !== api) other.byLabel(label); });
      }
      checkScrollables(panels[i]);
    }
    var api = {
      byLabel: function (label) { tabs.forEach(function (t, j) { if (t.textContent === label) select(j, false); }); },
      show: function (panel) { var j = panels.indexOf(panel); if (j >= 0) select(j, false); }
    };
    box.huTabs = api;
    var first = 0;
    if (group) {
      (groups[group] = groups[group] || []).push(api);
      var saved = stored('hulo-tab-' + group);
      tabs.forEach(function (t, j) { if (saved && t.textContent === saved) first = j; });
    }
    select(first, false);
    // Print every panel, each under its own heading (.hu-tab-h).
    var hiddenBefore = null;
    printHooks.push({
      before: function () {
        hiddenBefore = panels.map(function (p) { return p.hidden; });
        panels.forEach(function (p) { p.hidden = false; });
        box.classList.add('hu-printing');
      },
      after: function () {
        if (hiddenBefore) panels.forEach(function (p, j) { p.hidden = hiddenBefore[j]; });
        box.classList.remove('hu-printing');
      }
    });
  }

  // ── Scrolling tables and code ──
  // The built HTML makes every scrolling box a tab stop (tabindex="0") so a
  // keyboard can scroll it with scripts off. Here it stays one only while
  // its content actually overflows at the current width (a table that fits
  // is not a stop), and keyboard focus shows its top.
  var scrollables = [];
  function checkOne(n) {
    if (!n.offsetWidth && !n.offsetHeight) return; // hidden (another tab): decide when shown
    var scrolls = n.scrollWidth > n.clientWidth + 1 || n.scrollHeight > n.clientHeight + 1;
    if (scrolls) { if (n.getAttribute('tabindex') !== '0') n.setAttribute('tabindex', '0'); }
    else if (doc.activeElement !== n && n.hasAttribute('tabindex')) n.removeAttribute('tabindex');
  }
  function checkScrollables(ctx) {
    scrollables.forEach(function (n) { if (!ctx || ctx.contains(n)) checkOne(n); });
  }
  function initScrollable(n) {
    scrollables.push(n);
    showTopOnFocus(n);
    // Every scrolling table shades the edge that hides columns (hulo-ui.css).
    if (n.getAttribute('role') === 'region') fadeScroller(n);
    if (n.classList.contains('vp-compare-table')) stickyColumn(n);
    checkOne(n);
  }
  // The comparison table's feature column stays put (position: sticky) while
  // the plugin columns scroll under it. The browser's own focus scroll keeps
  // clear of it (scroll-padding-inline-start, from the column's measured
  // width, --hu-stick-w) but leaves alone a link that is only partly under
  // it; keyboard focus on such a link scrolls the table until it is clear.
  // On the right it also keeps clear of the shade over the hidden columns
  // (about 22px, hulo-ui.css), and a link that ends up within a shade's
  // width of the table's end takes the table all the way there, where the
  // shade goes.
  var EDGE = 8, SHADE = 40;
  function stickyColumn(box) {
    var first = box.querySelector('tr > :first-child');
    if (!first) return;
    function sticky() { return getComputedStyle(first).position === 'sticky'; }
    function measure() { box.style.setProperty('--hu-stick-w', Math.round(sticky() ? first.getBoundingClientRect().width : 0) + 'px'); }
    measure();
    if (window.ResizeObserver) new ResizeObserver(measure).observe(first);
    box.addEventListener('focusin', function (e) {
      var t = e.target, cell = t.closest && t.closest('td, th');
      if (t === box || !cell || cell.cellIndex === 0 || !keyboardFocus(t)) return;
      // After the browser's own scroll (focus scrolls first).
      requestAnimationFrame(function () {
        if (doc.activeElement !== t) return;
        var b = box.getBoundingClientRect(), r = t.getBoundingClientRect();
        var max = box.scrollWidth - box.clientWidth, atEnd = box.scrollLeft >= max - 2;
        var left = (sticky() ? first.getBoundingClientRect().right : b.left + box.clientLeft) + EDGE;
        var right = b.left + box.clientLeft + box.clientWidth - (atEnd ? EDGE : SHADE);
        if (r.left < left) box.scrollLeft -= left - r.left;
        else if (r.right > right) {
          var to = box.scrollLeft + Math.min(r.right - right, r.left - left);
          box.scrollLeft = max - to < SHADE ? max : to;
        }
      });
    });
  }
  var scrollTimer;
  addEventListener('resize', function () { clearTimeout(scrollTimer); scrollTimer = setTimeout(checkScrollables, 150); });
  if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(function () { checkScrollables(); });

  // ── Copy-to-clipboard buttons on code blocks. ──
  // One-line commands: the button sits beside the command. Multi-line code:
  // the button sits in a strip above the first line, so it never takes width
  // from the code.
  var COPY_ICON = svg('<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>');
  var DONE_ICON = svg('<polyline points="20 6 9 17 4 12"/>');
  function copyText(text) {
    function legacy() {
      return new Promise(function (resolve, reject) {
        var ta = el('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none';
        body.appendChild(ta);
        ta.select();
        var ok = false;
        try { ok = doc.execCommand('copy'); } catch (e) { ok = false; }
        body.removeChild(ta);
        if (ok) resolve(); else reject(new Error('copy blocked'));
      });
    }
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text).catch(legacy);
    return legacy();
  }
  function initCopy(code) {
    var wrap = code.parentNode;
    if (!wrap.classList.contains('hu-codewrap')) {
      wrap = el('div', 'hu-codewrap');
      code.parentNode.insertBefore(wrap, code);
      wrap.appendChild(code);
    }
    if (!wrap.classList.contains('hu-codewrap-1') && !wrap.classList.contains('hu-codewrap-n')) {
      wrap.classList.add(code.textContent.replace(/\s+$/, '').indexOf('\n') >= 0 ? 'hu-codewrap-n' : 'hu-codewrap-1');
    }
    var b = el('button', 'hu-copy');
    b.type = 'button';
    b.innerHTML = COPY_ICON + '<span class="hu-copy-t">Copy</span>';
    var what = el('span', 'sr-only', ' ' + (code.getAttribute('data-copy') || 'code'));
    b.appendChild(what);
    var timer;
    b.addEventListener('click', function () {
      var text = code.getAttribute('data-copy-text') || code.textContent.replace(/\s+$/, '');
      copyText(text).then(function () {
        b.classList.add('is-done');
        b.querySelector('svg').outerHTML = DONE_ICON;
        b.querySelector('.hu-copy-t').textContent = 'Copied';
        announce('Copied to the clipboard.');
        clearTimeout(timer);
        timer = setTimeout(function () {
          b.classList.remove('is-done');
          b.querySelector('svg').outerHTML = COPY_ICON;
          b.querySelector('.hu-copy-t').textContent = 'Copy';
        }, 2200);
      }, function () {
        var range = doc.createRange();
        range.selectNodeContents(code);
        var sel = getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        announce('This browser blocked copying. The text is selected: press Control+C or Command+C to copy it.');
      });
    });
    wrap.appendChild(b);
    wrap.classList.add('hu-has-copy');
  }

  // ── Pricing period switch (native radio group). ──
  // The card keeps the height of its tallest plan, so switching never moves
  // what is below it.
  function initPeriod(box) {
    var sw = box.querySelector('[data-period-switch]');
    if (!sw) return;
    var plans = all('[data-plan]', box), radios = all('input[type="radio"]', sw);
    var value = null;
    function show(v, byUser) {
      value = v;
      plans.forEach(function (p) {
        var on = p.getAttribute('data-plan') === v;
        if (on && p.hidden && byUser && !reduced()) {
          p.classList.remove('hu-swap');
          void p.offsetWidth;
          p.classList.add('hu-swap');
        }
        p.hidden = !on;
      });
      if (!byUser) return;
      stored('hulo-period', v);
      var plan = box.querySelector('[data-plan="' + v + '"]');
      var price = plan && plan.querySelector('[data-plan-price]');
      var label = sw.querySelector('input[value="' + v + '"] + span');
      if (price && label) announce(label.textContent + ': ' + price.textContent.trim() + ' ' + (plan.getAttribute('data-plan-unit') || '') + '.');
    }
    var fitWidth = -1;
    function fit() {
      if (box.offsetWidth === fitWidth) return;
      fitWidth = box.offsetWidth;
      box.style.minHeight = '';
      var tallest = 0;
      plans.forEach(function (p) {
        plans.forEach(function (q) { q.hidden = q !== p; });
        tallest = Math.max(tallest, box.offsetHeight);
      });
      plans.forEach(function (p) { p.hidden = p.getAttribute('data-plan') !== value; });
      if (tallest) box.style.minHeight = tallest + 'px';
    }
    var saved = stored('hulo-period'), pick = null;
    radios.forEach(function (r) { if (r.value === saved) pick = r; });
    pick = pick || radios.filter(function (r) { return r.checked; })[0] || radios[0];
    pick.checked = true;
    sw.hidden = false;
    show(pick.value, false);
    box.classList.add('hu-period-on');
    sw.classList.add('hu-ready');
    fit();
    var fitTimer;
    addEventListener('resize', function () { clearTimeout(fitTimer); fitTimer = setTimeout(fit, 150); });
    if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(function () { fitWidth = -1; fit(); });
    sw.addEventListener('change', function (e) { if (e.target.type === 'radio') show(e.target.value, true); });
    syncs.push(function () {
      var c = sw.querySelector('input:checked');
      if (c && c.value !== value) show(c.value, false);
    });
    printHooks.push({
      before: function () { plans.forEach(function (p) { p.hidden = false; }); box.classList.add('hu-printing'); },
      after: function () { show(value, false); box.classList.remove('hu-printing'); }
    });
  }

  // ── The price card beside the features (Vendure pages). ──
  // It sticks under the bars, 16px down (build.py). In a window too short to
  // hold the whole card and its footnote from there, its foot (the buy
  // button, the Terms and Privacy links) would stay below the window while
  // it sticks, so there it scrolls with the page instead (.hu-aside-static).
  function initAside(aside) {
    function fit() {
      aside.classList.remove('hu-aside-static');
      var cs = getComputedStyle(aside);
      if (cs.position !== 'sticky') return;
      if ((parseFloat(cs.top) || 0) + aside.offsetHeight > innerHeight - EDGE) aside.classList.add('hu-aside-static');
    }
    fit();
    var timer;
    // after the period switch has settled the card's height (150ms)
    addEventListener('resize', function () { clearTimeout(timer); timer = setTimeout(fit, 200); });
    if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(function () { setTimeout(fit, 0); });
  }

  // ── Release notes: "Show all N releases", "Show all N changes" on a long
  // open release, and the kind filter. ──
  var KIND_WORDS = { security: ['security change', 'security changes'], fix: ['fix', 'fixes'], feature: ['new feature', 'new features'] };
  function initChangelog(box) {
    var rels = all('[data-rel]', box);
    var more = box.querySelector('[data-cl-more]'), btn = box.querySelector('[data-cl-more-btn]');
    var tools = box.querySelector('[data-cl-tools]');
    var filter = box.querySelector('[data-cl-filter]'), status = box.querySelector('[data-cl-status]');
    var expanded = false, kind = 'all', openBefore = null;
    // A long release open by default shows its first few changes per group
    // (the rest carry .hu-cl-x); its button is a disclosure for the rest.
    var clips = [];
    all('[data-clip]', box).forEach(function (r) {
      var b = r.querySelector('[data-clip-btn]');
      if (!b) return;
      clips.push({ r: r, b: b });
      b.classList.add('hu-ready');
      b.addEventListener('click', function () {
        var open = b.getAttribute('aria-expanded') !== 'true';
        var was = b.getBoundingClientRect().top;
        b.setAttribute('aria-expanded', open ? 'true' : 'false');
        clipSync();
        // The changes it shows are spread through the release above the
        // button (and push it down): focus, and the view, go to the first of
        // them, so reading starts there and focus never stays on a button
        // that has been pushed out of the window.
        var first = open && r.querySelector('.hu-cl-x');
        if (first) {
          first.setAttribute('tabindex', '-1');
          focusTop(first);
        } else if (!open) {
          // Hiding them again pulls the button up by as much: the page
          // scrolls back by the same amount, at once, so the button (with
          // focus or the pointer on it) stays where it was.
          var shift = b.getBoundingClientRect().top - was;
          if (Math.abs(shift) > 1) {
            try { scrollTo({ top: scrollY + shift, behavior: 'instant' }); } catch (e) { scrollTo(0, scrollY + shift); }
          }
        }
      });
    });
    function clipSync() {
      clips.forEach(function (c) {
        c.r.classList.toggle('is-unclipped', kind !== 'all' || c.b.getAttribute('aria-expanded') === 'true');
        c.b.hidden = kind !== 'all';
      });
    }
    // A disclosure: the label stays the same, aria-expanded says whether
    // the older releases are showing.
    function setMore(on) {
      expanded = on;
      if (!more || !btn) return;
      more.hidden = !on && kind === 'all';
      btn.setAttribute('aria-expanded', on ? 'true' : 'false');
      // Once the filter has spoken, keep what it says true.
      if (status && status.textContent && kind === 'all') status.textContent = allSaid();
    }
    // On All: "Showing all N releases." only when they are; while the older
    // ones wait behind "Show all N releases", "the latest 5 of N".
    function allSaid() {
      return (more && !expanded && status.getAttribute('data-folded')) || status.getAttribute('data-all') || '';
    }
    if (more && btn) {
      btn.hidden = false;
      btn.classList.add('hu-ready');
      btn.addEventListener('click', function () { setMore(!expanded); });
      setMore(false);
    }
    function apply(k, say) {
      if (kind === 'all' && k !== 'all') openBefore = rels.map(function (r) { return r.open; });
      kind = k;
      var items = 0, releases = 0;
      rels.forEach(function (r) {
        var any = false;
        all('[data-kind]', r).forEach(function (li) {
          var match = k === 'all' || has(li.getAttribute('data-kind'), k);
          li.hidden = !match;
          if (match) { any = true; items++; }
        });
        all('[data-grp], [data-subgrp]', r).forEach(function (g) { g.hidden = k !== 'all' && !g.querySelector('[data-kind]:not([hidden])'); });
        all('[data-cl-intro]', r).forEach(function (p) { p.hidden = k !== 'all'; });
        r.hidden = k !== 'all' && !any;
        if (k !== 'all' && any) { releases++; if ('open' in r) r.open = true; }
      });
      if (k === 'all' && openBefore) {
        rels.forEach(function (r, i) { if ('open' in r) r.open = openBefore[i]; });
        openBefore = null;
      }
      if (more) more.hidden = k === 'all' ? !expanded : false;
      if (btn) btn.hidden = k !== 'all';
      clipSync();
      if (status && say) {
        var w = KIND_WORDS[k];
        status.textContent = k === 'all' ? allSaid()
          : 'Showing ' + items + ' ' + (items === 1 ? w[0] : w[1]) + ' in ' + releases + (releases === 1 ? ' release.' : ' releases.');
      }
    }
    if (filter) {
      filter.addEventListener('change', function (e) { if (e.target.type === 'radio') apply(e.target.value, true); });
      var picked = filter.querySelector('input:checked');
      if (picked && picked.value !== 'all') apply(picked.value, true);
      syncs.push(function () {
        var c = filter.querySelector('input:checked'), v = c ? c.value : 'all';
        if (v !== kind) apply(v, true);
      });
    }
    clipSync();
    box.classList.add('hu-cl-on');
    if (tools) tools.classList.add('hu-ready');
    box.huReveal = function () { if (kind === 'all') setMore(true); };
    // A link to a release the kind filter hides: back to All.
    box.huShowAll = function () {
      if (kind === 'all') return;
      var a = filter && filter.querySelector('input[value="all"]');
      if (a) a.checked = true;
      apply('all', true);
    };
    // Printing: every release, open, with all of its changes (the filter
    // chips do not print, so a filtered list would silently leave some out);
    // the filter is put back afterwards.
    var printKind = 'all';
    printHooks.push({
      before: function () {
        printKind = kind;
        if (kind !== 'all') apply('all', false);
        if (more) { more.huWas = more.hidden; more.hidden = false; }
        rels.forEach(function (r) { if ('open' in r) { r.huWasOpen = r.open; r.open = true; } });
        clips.forEach(function (c) { c.r.classList.add('is-unclipped'); });
      },
      after: function () {
        if (more) more.hidden = more.huWas;
        rels.forEach(function (r) { if ('open' in r && r.huWasOpen !== undefined) r.open = r.huWasOpen; });
        if (printKind !== 'all') apply(printKind, false);
        clipSync();
      }
    });
  }

  // "New" pills are baked in at build time; drop any whose 30 days have run
  // out since (the page may be older than the release window).
  function expireNew() {
    var d = new Date(), pad = function (n) { return (n < 10 ? '0' : '') + n; };
    var today = d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
    all('.hu-pill-new[data-new-until]').forEach(function (p) {
      if (p.getAttribute('data-new-until') < today) p.parentNode.removeChild(p);
    });
  }

  // ── FAQ: "Expand all" (the open / close motion is CSS). ──
  function initFaq(list) {
    var items = all('details', list);
    if (items.length < 2) return;
    // The bar is in the HTML (laid out from the first paint, hu-needs-js);
    // built here for a list without one.
    var bar = list.previousElementSibling, b = bar && bar.classList.contains('hu-expand-bar') ? bar.querySelector('.hu-expand') : null;
    if (!b) {
      bar = el('div', 'hu-expand-bar');
      b = el('button', 'hu-expand');
      b.type = 'button';
      bar.appendChild(b);
      list.parentNode.insertBefore(bar, list);
    }
    function allOpen() { return items.every(function (d) { return d.open; }); }
    function label() { b.textContent = allOpen() ? 'Collapse all' : 'Expand all'; }
    b.addEventListener('click', function () {
      var open = !allOpen();
      items.forEach(function (d) { d.open = open; });
      label();
      announce(open ? 'All answers expanded.' : 'All answers collapsed.');
    });
    items.forEach(function (d) { d.addEventListener('toggle', label); });
    label();
    bar.classList.add('hu-ready');
    // Printing: every answer.
    printHooks.push({
      before: function () { items.forEach(function (d) { d.huWasOpen = d.open; d.open = true; }); },
      after: function () { items.forEach(function (d) { if (d.huWasOpen !== undefined) d.open = d.huWasOpen; }); }
    });
  }

  // ── Screenshot lightbox (native <dialog>). ──
  // A fixed-size frame: title bar, the image (contained), the caption and
  // Previous / Next, so stepping through never moves the buttons. Full screen
  // on phones; image beside the caption on short landscape screens; "Full
  // size" opens the PNG itself (pinch-zoom on a phone). The dialog is named
  // by its title and described by the caption, read once on opening; the
  // image's own name is the short title, so the caption is not read again
  // as the image. Tab and Shift+Tab wrap inside the dialog.
  function initGallery(gallery) {
    var links = all('a.hu-shot', gallery);
    if (!links.length || typeof HTMLDialogElement !== 'function') return;
    var dlg = el('dialog', 'hu-lightbox'), index = 0, opener = null;
    dlg.setAttribute('aria-labelledby', 'hu-lb-title');
    dlg.setAttribute('aria-describedby', 'hu-lb-cap');
    dlg.innerHTML =
      '<div class="hu-lb-bar"><h2 class="hu-lb-title" id="hu-lb-title"></h2>' +
      '<a class="hu-lb-full" target="_blank" rel="noopener">Full size<span class="sr-only"> image, opens in a new tab</span></a>' +
      '<button type="button" class="hu-lb-close">' + svg('<line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/>') + '<span class="sr-only">Close</span></button></div>' +
      '<div class="hu-lb-body"><div class="hu-lb-stage"><img class="hu-lb-img" alt=""></div>' +
      '<p class="hu-lb-cap" id="hu-lb-cap"></p></div>' +
      '<div class="hu-lb-nav"><button type="button" class="btn btn-secondary hu-lb-prev"><span aria-hidden="true">←</span> Previous</button>' +
      '<button type="button" class="btn btn-secondary hu-lb-next">Next <span aria-hidden="true">→</span></button></div>' +
      '<p class="sr-only" role="status" aria-atomic="true" data-live></p>';
    body.appendChild(dlg);
    var title = dlg.querySelector('.hu-lb-title'), img = dlg.querySelector('.hu-lb-img'), cap = dlg.querySelector('.hu-lb-cap');
    var full = dlg.querySelector('.hu-lb-full');
    // A real link from the start (the first screenshot), not an <a> without
    // an href while the dialog waits closed: show() points it at each image.
    full.href = links[0].getAttribute('href');
    var single = links.length < 2;
    if (single) dlg.querySelector('.hu-lb-nav').hidden = true;
    var firstThumb = links[0].querySelector('img');
    if (firstThumb && firstThumb.getAttribute('width') && firstThumb.getAttribute('height')) {
      dlg.style.setProperty('--hu-lb-ratio', String(+firstThumb.getAttribute('height') / +firstThumb.getAttribute('width')));
    }
    function caption(a) { return a.getAttribute('data-caption') || ''; }
    // A caption taller than its box (short landscape screens with large
    // text) scrolls inside it: a tab stop then, so the keyboard can scroll it.
    function capFit() {
      if (!dlg.open) return;
      if (cap.scrollHeight > cap.clientHeight + 1) cap.setAttribute('tabindex', '0');
      else if (doc.activeElement !== cap) cap.removeAttribute('tabindex');
    }
    addEventListener('resize', capFit);
    function show(i, say) {
      index = (i + links.length) % links.length;
      var a = links[index];
      title.textContent = 'Screenshot ' + (index + 1) + ' of ' + links.length;
      img.src = a.getAttribute('href');
      full.href = a.getAttribute('href');
      img.alt = title.textContent;
      var thumb = a.querySelector('img');
      if (thumb && thumb.getAttribute('width')) { img.width = +thumb.getAttribute('width'); img.height = +thumb.getAttribute('height'); }
      cap.textContent = caption(a);
      cap.scrollTop = 0;
      capFit();
      if (say) announce(title.textContent + '. ' + caption(a));
      var next = new Image();
      next.src = links[(index + 1) % links.length].getAttribute('href');
    }
    links.forEach(function (a, i) {
      a.setAttribute('aria-haspopup', 'dialog');
      a.addEventListener('click', function (e) {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button > 0) return;
        e.preventDefault();
        opener = a;
        show(i, false);
        dlg.showModal();
        capFit();
        dlg.querySelector('.hu-lb-close').focus();
      });
    });
    dlg.querySelector('.hu-lb-close').addEventListener('click', function () { dlg.close(); });
    dlg.querySelector('.hu-lb-prev').addEventListener('click', function () { show(index - 1, true); });
    dlg.querySelector('.hu-lb-next').addEventListener('click', function () { show(index + 1, true); });
    function stops() { return all('a[href], button', dlg).filter(function (n) { return n.offsetWidth || n.offsetHeight; }); }
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'Tab') {
        var f = stops();
        if (!f.length) return;
        var first = f[0], last = f[f.length - 1];
        if (!e.shiftKey && doc.activeElement === last) { e.preventDefault(); first.focus(); }
        else if (e.shiftKey && doc.activeElement === first) { e.preventDefault(); last.focus(); }
        return;
      }
      if (single) return;
      if (e.key === 'ArrowLeft') { e.preventDefault(); show(index - 1, true); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); show(index + 1, true); }
    });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('close', function () { dlg.querySelector('[data-live]').textContent = ''; if (opener) opener.focus(); });
  }

  // ── Plugin catalogue: category chips + live search. ──
  // Search matches what a card says about the plugin (name, tagline, feature
  // list) and its keywords: not button labels, prices or screen-reader text.
  // Hyphens and dashes count as spaces, in the cards and in the query, and a
  // card also matches its hyphenated words written as one ("e-mail" finds
  // "email" and the other way round; "geo-block" finds "Geo Block").
  var DASH = /[\u002d\u2010-\u2015\u2212]+/g;
  function norm(s) { return (s || '').toLowerCase().replace(DASH, ' ').replace(/\s+/g, ' ').trim(); }
  function joined(s) {
    var w = (s || '').toLowerCase().match(/[a-z0-9]+(?:[\u002d\u2010\u2011][a-z0-9]+)+/g);
    return w ? w.map(function (x) { return x.replace(DASH, ''); }).join(' ') : '';
  }
  function visibleText(n) {
    var out = '';
    for (var c = n.firstChild; c; c = c.nextSibling) {
      if (c.nodeType === 3) out += c.nodeValue;
      else if (c.nodeType === 1 && !c.classList.contains('sr-only')) out += ' ' + visibleText(c) + ' ';
    }
    return out;
  }
  function initCatalog(box) {
    var controls = box.querySelector('[data-catalog-controls]'), cards = all('[data-cats]', box);
    var input = box.querySelector('input[type="search"]'), count = box.querySelector('[data-catalog-count]');
    var empty = box.querySelector('[data-catalog-empty]'), timer;
    if (!controls || !cards.length) return;
    cards.forEach(function (c) {
      var parts = all('h3, .vp-card-tagline, ul li', c).map(visibleText);
      var text = parts.join(' ') + ' ' + (c.getAttribute('data-keywords') || '');
      c.huText = norm(text + ' ' + joined(text));
    });
    var picked = controls.querySelector('input[type="radio"]:checked');
    var cat = picked ? picked.value : 'all';
    function chipLabel(value) {
      var span = controls.querySelector('input[value="' + value + '"] + span');
      return span ? span.getAttribute('data-name') : '';
    }
    function run(delaySay) {
      var words = norm(input ? input.value : '').split(' ').filter(Boolean), shown = 0;
      cards.forEach(function (c) {
        var ok = (cat === 'all' || has(c.getAttribute('data-cats'), cat)) &&
          words.every(function (w) { return c.huText.indexOf(w) >= 0; });
        c.hidden = !ok;
        if (ok) shown++;
      });
      if (empty) empty.hidden = shown > 0;
      var msg = shown === cards.length ? 'Showing all ' + shown + ' plugins.'
        : 'Showing ' + shown + ' of ' + cards.length + ' plugins' + (cat !== 'all' ? ' in ' + chipLabel(cat) : '') + (words.length ? ' matching “' + input.value.trim() + '”' : '') + '.';
      clearTimeout(timer);
      if (count.textContent === msg) return;
      if (delaySay) timer = setTimeout(function () { count.textContent = msg; }, 450);
      else count.textContent = msg;
    }
    controls.addEventListener('change', function (e) { if (e.target.type === 'radio') { cat = e.target.value; run(false); } });
    if (input) {
      input.addEventListener('input', function () { run(true); });
      input.addEventListener('keydown', function (e) { if (e.key === 'Escape' && input.value) { input.value = ''; run(false); } });
    }
    var reset = box.querySelector('[data-catalog-reset]');
    if (reset) reset.addEventListener('click', function () {
      if (input) input.value = '';
      var allChip = controls.querySelector('input[value="all"]');
      if (allChip) { allChip.checked = true; cat = 'all'; allChip.focus(); }
      run(false);
    });
    run(false);
    syncs.push(function () {
      var c = controls.querySelector('input[type="radio"]:checked'), v = c ? c.value : 'all';
      if (v !== cat || (input && input.value)) { cat = v; run(false); }
    });
    // On phones the chips are one row that scrolls sideways (hulo-ui.css).
    var chips = controls.querySelector('.hu-chips');
    if (chips) { fadeScroller(chips); keepFocusInView(chips, '.hu-chip'); }
    controls.classList.add('hu-ready');
  }

  // ── Reveal on scroll (never with reduced motion; never above the fold). ──
  // Fails open: nothing is hidden under automation (navigator.webdriver:
  // full-page captures and audits see the whole page; add ?hu-reveal to the
  // URL to test the effect there), on a very tall viewport, and anything
  // still waiting is shown at once if the viewport becomes that tall later.
  var TALL = 1600;
  function initReveal() {
    if (navigator.webdriver && !/[?&]hu-reveal\b/.test(location.search)) return;
    if (reduced() || !('IntersectionObserver' in window) || innerHeight > TALL) return;
    var targets = [];
    all('main .vp-section > .container-page').forEach(function (c) {
      var cards = all('.vp-cards-grid > .vp-card', c);
      if (cards.length) {
        cards.forEach(function (card, i) { card.style.setProperty('--hu-d', (i % 3) * 70 + 'ms'); targets.push(card); });
      } else {
        targets.push(c);
      }
    });
    all('main .hu-shots > li').forEach(function (li, i) { li.style.setProperty('--hu-d', (i % 3) * 70 + 'ms'); targets.push(li); });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var t = en.target;
        io.unobserve(t);
        t.classList.add('hu-in');
        setTimeout(function () { t.classList.remove('hu-reveal', 'hu-in'); t.style.removeProperty('--hu-d'); }, 1000);
      });
    }, { rootMargin: '0px 0px -6% 0px' });
    var fold = innerHeight, waiting = [];
    targets.forEach(function (t) {
      if (t.getBoundingClientRect().top < fold) return;
      t.classList.add('hu-reveal');
      io.observe(t);
      waiting.push(t);
    });
    function showAll() {
      io.disconnect();
      waiting.forEach(function (t) { t.classList.remove('hu-reveal', 'hu-in'); t.style.removeProperty('--hu-d'); });
      removeEventListener('resize', onResize);
      doc.removeEventListener('focusin', onFocus);
    }
    function onResize() { if (innerHeight > TALL || reduced()) showAll(); }
    // Focus moving into something still waiting (or fading in): show it at
    // once, with no fade, so the focused control and its ring are never
    // invisible while the page scrolls to them. A fade already under way is
    // cut short too (taking the classes off alone would let it run on).
    function onFocus(e) {
      waiting.forEach(function (t) {
        if (!t.classList.contains('hu-reveal') || !t.contains(e.target)) return;
        io.unobserve(t);
        t.style.transition = 'none';
        t.classList.remove('hu-reveal', 'hu-in');
        t.style.removeProperty('--hu-d');
        void t.offsetWidth;
        t.style.removeProperty('transition');
      });
    }
    if (waiting.length) {
      doc.addEventListener('focusin', onFocus);
      addEventListener('resize', onResize);
      if (motionQuery && motionQuery.addEventListener) motionQuery.addEventListener('change', onResize);
      printHooks.push({ before: showAll, after: function () {} });
    }
  }

  // ── Back to top. ──
  // From 1024px wide it shows once the page is well scrolled. Narrower, it
  // would float over the content column (FAQ toggles, release chevrons, Copy
  // buttons), so there it shows only at the end of the page, once its spot
  // is over the footer, and stays while the keyboard is in the footer (Tab
  // after the last footer link reaches it) or on the button itself.
  function initTop() {
    if (root.scrollHeight < innerHeight * 2.5) return;
    var b = el('button', 'hu-top');
    b.type = 'button';
    b.innerHTML = svg('<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>') + '<span class="sr-only">Back to top</span>';
    body.appendChild(b);
    var wide = window.matchMedia ? matchMedia('(min-width: 1024px)') : { matches: true };
    var foot = doc.querySelector('body > footer') || doc.querySelector('footer');
    var on = false;
    function set(want) { if (want !== on) { on = want; b.classList.toggle('is-on', on); } }
    function engaged() {
      var hover = false;
      try { hover = b.matches(':hover'); } catch (e) { hover = false; }
      return doc.activeElement === b || hover;
    }
    function inFooter() { var a = doc.activeElement; return !!foot && !!a && foot.contains(a); }
    function overFooter() {
      // the top of the button's spot (it is fixed to the bottom corner)
      var spot = innerHeight - (parseFloat(getComputedStyle(b).bottom) || 16) - b.offsetHeight - 8;
      return foot ? foot.getBoundingClientRect().top <= spot : innerHeight + scrollY >= root.scrollHeight - 4;
    }
    function update() {
      if (scrollY <= Math.max(700, innerHeight * 1.2) && !inFooter()) return set(false);
      set(wide.matches || overFooter() || inFooter() || engaged());
    }
    onScroll(update)();
    if (foot) {
      foot.addEventListener('focusin', update);
      foot.addEventListener('focusout', function () { setTimeout(update, 0); });
    }
    b.addEventListener('blur', function () { setTimeout(update, 0); });
    b.addEventListener('mouseleave', update);
    if (wide.addEventListener) wide.addEventListener('change', update);
    b.addEventListener('click', function () {
      scrollTo({ top: 0, behavior: reduced() ? 'auto' : 'smooth' });
      var main = doc.getElementById('main');
      if (main) { main.setAttribute('tabindex', '-1'); main.focus({ preventScroll: true }); }
    });
  }

  // ── A link to something folded away (#whats-new-v0.2.0, #features-pro). ──
  function revealHash() {
    var id = decodeURIComponent(location.hash.slice(1));
    var target = id && doc.getElementById(id);
    if (!target) return;
    var changed = false;
    for (var n = target; n && n !== body; n = n.parentNode) {
      if (n.hasAttribute('data-rel') && n.hidden) {
        var list = n.closest('[data-changelog]');
        if (list && list.huShowAll) { list.huShowAll(); changed = true; }
      }
      if (n.hasAttribute('data-cl-more') && n.hidden) {
        var box = n.closest('[data-changelog]');
        if (box && box.huReveal) { box.huReveal(); changed = true; }
      }
      if (n.tagName === 'DETAILS' && !n.open) { n.open = true; changed = true; }
      if (n.hasAttribute('data-tab') && n.hidden && n.parentNode.huTabs) { n.parentNode.huTabs.show(n); changed = true; }
    }
    if (changed) target.scrollIntoView();
  }

  each('[data-copy]', initCopy);   // before tabs, so each panel's Copy button is in place
  each('[role="region"][tabindex="0"], pre[tabindex="0"], .vp-code[tabindex="0"], .doc-code[tabindex="0"]', initScrollable);
  each('[data-tabs]', initTabs);
  each('[data-period]', initPeriod);
  each('.vp-pricing-aside', initAside);   // after the period switch has set the card's height
  each('[data-changelog]', initChangelog);
  safely(expireNew);
  each('.vp-faq', initFaq);
  each('[data-gallery]', initGallery);
  each('[data-catalog]', initCatalog);
  each('nav[data-spy]', initSpy);
  safely(initReveal);
  safely(initTop);
  safely(revealHash);
  addEventListener('hashchange', revealHash);
  addEventListener('pageshow', function () { syncs.forEach(function (f) { safely(f); }); });
  // Printing shows what tabs, the period switch and "Show all" fold away.
  addEventListener('beforeprint', function () { printHooks.forEach(function (h) { safely(h.before); }); });
  addEventListener('afterprint', function () { printHooks.forEach(function (h) { safely(h.after); }); });
  root.classList.add('hu-ui');
})();
