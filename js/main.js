/* ==========================================================================
   Палки и Балки — логика лендинга.
   Один файл на обе страницы: каждый блок включается, только если на
   странице есть его разметка.
   ========================================================================== */
(function () {
  'use strict';

  var doc = document;
  var body = doc.body;
  var $ = function (sel, root) { return (root || doc).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); };

  /* Контакты берутся из data-атрибутов <body> — менять там. */
  var TG = body.dataset.tg || '';
  var WA = body.dataset.wa || '';

  /* ---------- Текущий год в подвале ---------- */
  var year = $('#year');
  if (year) year.textContent = String(new Date().getFullYear());

  /* ---------- Меню ---------- */
  (function menu() {
    var menuEl = $('#menu');
    var openBtn = $('[data-menu-open]');
    if (!menuEl || !openBtn) return;

    var lastFocus = null;

    function open() {
      lastFocus = doc.activeElement;
      menuEl.hidden = false;
      requestAnimationFrame(function () {
        menuEl.dataset.open = 'true';
        body.classList.add('is-locked');
        openBtn.setAttribute('aria-expanded', 'true');
        var first = $('[data-menu-close]', menuEl);
        if (first) first.focus();
      });
    }

    function close() {
      if (menuEl.dataset.open !== 'true') return;
      menuEl.dataset.open = 'false';
      body.classList.remove('is-locked');
      openBtn.setAttribute('aria-expanded', 'false');
      window.setTimeout(function () {
        if (menuEl.dataset.open === 'false') menuEl.hidden = true;
      }, 350);
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    openBtn.addEventListener('click', open);
    $$('[data-menu-close]').forEach(function (el) { el.addEventListener('click', close); });
    $$('[data-menu-link]', menuEl).forEach(function (el) { el.addEventListener('click', close); });
    doc.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });
  }());

  /* ---------- Аккордеон направлений ---------- */
  var accordion = (function () {
    var wrap = $('[data-acc]');
    if (!wrap) return { open: function () {} };

    var items = $$('.acc__item', wrap);

    function setOpen(item, state) {
      var btn = $('.acc__head', item);
      item.classList.toggle('is-open', state);
      if (btn) btn.setAttribute('aria-expanded', state ? 'true' : 'false');
    }

    items.forEach(function (item) {
      var btn = $('.acc__head', item);
      if (!btn) return;
      btn.addEventListener('click', function () {
        setOpen(item, !item.classList.contains('is-open'));
        syncToggleAll();
      });
    });

    var toggleAll = $('[data-acc-all]');
    function syncToggleAll() {
      if (!toggleAll) return;
      var allOpen = items.every(function (i) { return i.classList.contains('is-open'); });
      toggleAll.setAttribute('aria-expanded', allOpen ? 'true' : 'false');
      var label = $('span', toggleAll);
      if (label) label.textContent = allOpen ? 'Свернуть все' : 'Раскрыть все';
    }
    if (toggleAll) {
      toggleAll.addEventListener('click', function () {
        var allOpen = items.every(function (i) { return i.classList.contains('is-open'); });
        items.forEach(function (i) { setOpen(i, !allOpen); });
        syncToggleAll();
      });
    }

    function openById(id) {
      var item = doc.getElementById(id);
      if (!item || !item.classList.contains('acc__item')) return false;
      setOpen(item, true);
      syncToggleAll();
      item.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'start' });
      var btn = $('.acc__head', item);
      if (btn) window.setTimeout(function () { btn.focus({ preventScroll: true }); }, 450);
      return true;
    }

    /* Карточки-плитки направлений */
    $$('[data-goto]').forEach(function (card) {
      card.addEventListener('click', function () { openById(card.dataset.goto); });
    });

    /* Прямая ссылка вида index.html#dir-kitchen */
    if (window.location.hash) {
      var id = window.location.hash.slice(1);
      window.setTimeout(function () { openById(id); }, 120);
    }

    return { open: openById };
  }());

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /* ---------- Появление блоков при скролле ---------- */
  (function reveal() {
    var items = $$('.reveal');
    if (!items.length) return;
    if (!('IntersectionObserver' in window) || prefersReducedMotion()) {
      items.forEach(function (el) { el.classList.add('is-in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  }());

  /* ---------- Квиз ---------- */
  (function quiz() {
    var form = $('#quiz');
    if (!form) return;

    var preview = $('#quiz-preview');
    var status = $('#quiz-status');

    function selectedDirs() {
      return $$('input[name="dir"]:checked', form).map(function (i) { return i.value; });
    }
    function selectedBudget() {
      var b = $('input[name="budget"]:checked', form);
      return b ? b.value : '';
    }
    function name() {
      var n = $('#q-name', form);
      return n ? n.value.trim() : '';
    }

    function buildMessage() {
      var dirs = selectedDirs();
      var lines = ['Здравствуйте! Заявка с сайта «Палки и Балки».'];
      lines.push('Направление: ' + (dirs.length ? dirs.join(', ') : '—'));
      lines.push('Бюджет: ' + (selectedBudget() || '—'));
      if (name()) lines.push('Имя: ' + name());
      lines.push('Прошу рассчитать стоимость и записать на замер.');
      return lines.join('\n');
    }

    function renderPreview() {
      if (!preview) return;
      var dirs = selectedDirs();
      preview.innerHTML = 'Текст заявки:\n' +
        'Направление: <b>' + escapeHtml(dirs.length ? dirs.join(', ') : 'не выбрано') + '</b>\n' +
        'Бюджет: <b>' + escapeHtml(selectedBudget() || 'не выбран') + '</b>' +
        (name() ? '\nИмя: <b>' + escapeHtml(name()) + '</b>' : '');
    }

    function escapeHtml(str) {
      return String(str).replace(/[&<>"']/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
      });
    }

    function validate() {
      if (!selectedDirs().length) {
        say('Отметьте хотя бы одно направление — так мы сразу поймём задачу.');
        var first = $('input[name="dir"]', form);
        if (first) first.focus();
        return false;
      }
      if (!selectedBudget()) {
        say('Выберите ориентир по бюджету — можно приблизительно.');
        var b = $('input[name="budget"]', form);
        if (b) b.focus();
        return false;
      }
      say('');
      return true;
    }

    function say(text) {
      if (status) status.textContent = text;
    }

    function openMessenger(url) {
      var win = window.open(url, '_blank', 'noopener');
      if (!win) window.location.href = url;
    }

    form.addEventListener('change', renderPreview);
    form.addEventListener('input', renderPreview);
    renderPreview();

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!validate()) return;
      if (!TG) { say('Не указан Telegram-аккаунт: задайте data-tg у <body>.'); return; }
      openMessenger('https://t.me/' + TG + '?text=' + encodeURIComponent(buildMessage()));
      say('Открываем Telegram — текст заявки уже подставлен, остаётся отправить.');
    });

    var waBtn = $('[data-quiz-wa]');
    if (waBtn) {
      waBtn.addEventListener('click', function () {
        if (!validate()) return;
        if (!WA) { say('Не указан номер WhatsApp: задайте data-wa у <body>.'); return; }
        openMessenger('https://wa.me/' + WA + '?text=' + encodeURIComponent(buildMessage()));
        say('Открываем WhatsApp — текст заявки уже подставлен.');
      });
    }

    var copyBtn = $('[data-quiz-copy]');
    if (copyBtn) {
      copyBtn.addEventListener('click', function () {
        var text = buildMessage();
        var done = function () { say('Текст заявки скопирован — можно вставить в любой мессенджер.'); };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(done, fallback);
        } else {
          fallback();
        }
        function fallback() {
          var ta = doc.createElement('textarea');
          ta.value = text;
          ta.setAttribute('readonly', '');
          ta.style.position = 'fixed';
          ta.style.opacity = '0';
          body.appendChild(ta);
          ta.select();
          try { doc.execCommand('copy'); done(); } catch (err) { say('Скопировать не удалось — выделите текст вручную.'); }
          body.removeChild(ta);
        }
      });
    }

    /* Кнопки «Рассчитать …» внутри блоков направлений подставляют направление */
    $$('[data-prefill]').forEach(function (link) {
      link.addEventListener('click', function () {
        var value = link.dataset.prefill;
        var input = $$('input[name="dir"]', form).filter(function (i) { return i.value === value; })[0];
        if (input && !input.checked) {
          input.checked = true;
          renderPreview();
        }
      });
    });
  }());

  /* ---------- Портфолио: фильтры ---------- */
  (function portfolioFilters() {
    var filters = $$('.pf-filter');
    var items = $$('.pf-item');
    var empty = $('.pf-empty');
    if (!filters.length || !items.length) return;

    function apply(value) {
      var shown = 0;
      items.forEach(function (item) {
        var match = value === 'all' || item.dataset.dir === value;
        item.hidden = !match;
        if (match) shown++;
      });
      filters.forEach(function (f) {
        f.setAttribute('aria-pressed', f.dataset.filter === value ? 'true' : 'false');
      });
      if (empty) empty.hidden = shown > 0;
      try {
        var url = new URL(window.location.href);
        url.hash = value === 'all' ? '' : value;
        window.history.replaceState(null, '', url.toString());
      } catch (err) { /* не критично */ }
    }

    filters.forEach(function (f) {
      f.addEventListener('click', function () { apply(f.dataset.filter); });
    });

    var hash = window.location.hash.slice(1);
    var known = filters.some(function (f) { return f.dataset.filter === hash; });
    apply(known ? hash : 'all');
  }());

  /* ---------- Портфолио: просмотр фото ---------- */
  (function lightbox() {
    var box = $('#lightbox');
    if (!box) return;
    var img = $('img', box);
    var cap = $('.lightbox__cap', box);
    var lastFocus = null;

    function open(src, title, meta) {
      lastFocus = doc.activeElement;
      img.src = src;
      img.alt = title;
      cap.innerHTML = '';
      cap.appendChild(doc.createTextNode(title));
      if (meta) {
        var small = doc.createElement('small');
        small.textContent = meta;
        cap.appendChild(small);
      }
      box.dataset.open = 'true';
      body.classList.add('is-locked');
      var close = $('.lightbox__close', box);
      if (close) close.focus();
    }

    function close() {
      box.dataset.open = 'false';
      body.classList.remove('is-locked');
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    $$('.pf-item').forEach(function (item) {
      item.addEventListener('click', function () {
        var picture = $('img', item);
        open(picture ? picture.src : '', item.dataset.title || '', item.dataset.meta || '');
      });
    });

    box.addEventListener('click', function (e) {
      if (e.target === box || e.target.closest('.lightbox__close')) close();
    });
    doc.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && box.dataset.open === 'true') close();
    });
  }());

}());
