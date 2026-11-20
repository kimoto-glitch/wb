/* 웨이보 셀러 소식 — 보고서 인터랙션
   검색 · 셀러 필터 · 사진 라이트박스 · 날짜 이동 */

(function () {
  'use strict';

  var sections = Array.prototype.slice.call(document.querySelectorAll('.seller-section'));
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
  var input = document.getElementById('search');
  var clearBtn = document.getElementById('search-clear');
  var countLine = document.getElementById('count-line');
  var empty = document.getElementById('empty');
  var dateSelect = document.getElementById('datepick');

  var state = { seller: 'all', q: '' };

  var totalPosts = document.querySelectorAll('.post').length;

  /* ── 정규화: 대소문자·공백 무시 ── */
  function norm(s) {
    return (s || '').toLowerCase().replace(/\s+/g, ' ').trim();
  }

  function apply() {
    var q = norm(state.q);
    var shown = 0;

    sections.forEach(function (sec) {
      var seller = sec.getAttribute('data-seller');
      var sellerOn = state.seller === 'all' || state.seller === seller;
      var visibleInSection = 0;

      Array.prototype.forEach.call(sec.querySelectorAll('.post'), function (post) {
        var hay = post.getAttribute('data-search') || norm(post.textContent);
        var match = !q || hay.indexOf(q) !== -1;
        var show = sellerOn && match;
        post.hidden = !show;
        if (show) { visibleInSection++; shown++; }
      });

      sec.hidden = visibleInSection === 0;
      var badge = sec.querySelector('.seller-count');
      if (badge) badge.textContent = visibleInSection + '건';
    });

    empty.style.display = shown === 0 ? 'block' : 'none';

    if (countLine) {
      var parts = [];
      parts.push(shown === totalPosts ? '전체 ' + totalPosts + '건' : shown + ' / ' + totalPosts + '건 표시');
      if (q) parts.push('검색 “' + state.q.trim() + '”');
      var tabLabel = document.querySelector('.tab[aria-pressed="true"]');
      if (tabLabel && state.seller !== 'all') parts.push('필터 ' + tabLabel.getAttribute('data-label'));
      countLine.textContent = parts.join('  ·  ');
    }

    if (clearBtn) clearBtn.hidden = state.q.length === 0;
  }

  /* ── 필터 탭 ── */
  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      state.seller = tab.getAttribute('data-seller');
      tabs.forEach(function (t) { t.setAttribute('aria-pressed', String(t === tab)); });
      apply();
    });
  });

  /* ── 검색 ── */
  if (input) {
    input.addEventListener('input', function () {
      state.q = input.value;
      apply();
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { input.value = ''; state.q = ''; apply(); }
    });
  }
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      if (input) { input.value = ''; input.focus(); }
      state.q = '';
      apply();
    });
  }

  /* ── 날짜 이동 ── */
  if (dateSelect) {
    dateSelect.addEventListener('change', function () {
      var v = dateSelect.value;
      if (v && v !== dateSelect.getAttribute('data-current')) {
        window.location.href = '../' + v + '/';
      }
    });
  }

  /* ── 라이트박스 ── */
  var lb = document.getElementById('lightbox');
  var lbImg = document.getElementById('lb-img');
  var lbCount = document.getElementById('lb-count');
  var lbTitle = document.getElementById('lb-title');
  var lbPrev = document.getElementById('lb-prev');
  var lbNext = document.getElementById('lb-next');
  var lbClose = document.getElementById('lb-close');
  var group = [];
  var idx = 0;
  var lastFocus = null;

  function render() {
    var it = group[idx];
    if (!it) return;
    lbImg.src = it.full;
    lbImg.alt = it.alt || '';
    lbCount.textContent = (idx + 1) + ' / ' + group.length;
    lbTitle.textContent = it.post || '';
    lbPrev.hidden = group.length < 2;
    lbNext.hidden = group.length < 2;
  }

  function open(postEl, startIndex) {
    var data = postEl.getAttribute('data-photos');
    var title = postEl.getAttribute('data-post-title') || '';
    group = [];
    try {
      group = (JSON.parse(data || '[]') || []).map(function (p) {
        return { full: p.f, alt: p.a || '', post: title };
      });
    } catch (err) {
      group = [];
    }
    if (!group.length) return;
    idx = startIndex || 0;
    lastFocus = document.activeElement;
    lb.setAttribute('data-open', 'true');
    document.body.style.overflow = 'hidden';
    render();
    lbClose.focus();
  }

  function close() {
    lb.setAttribute('data-open', 'false');
    lbImg.src = '';
    document.body.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function step(d) {
    if (group.length < 2) return;
    idx = (idx + d + group.length) % group.length;
    render();
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.thumb') : null;
    if (!btn) return;
    var postEl = btn.closest('.post');
    if (!postEl) return;
    open(postEl, parseInt(btn.getAttribute('data-idx') || '0', 10));
  });

  if (lb) {
    lbClose.addEventListener('click', close);
    lbPrev.addEventListener('click', function (e) { e.stopPropagation(); step(-1); });
    lbNext.addEventListener('click', function (e) { e.stopPropagation(); step(1); });
    lb.addEventListener('click', function (e) {
      if (e.target === lb || e.target.classList.contains('lb-stage')) close();
    });
    document.addEventListener('keydown', function (e) {
      if (lb.getAttribute('data-open') !== 'true') return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft') step(-1);
      else if (e.key === 'ArrowRight') step(1);
    });
  }

  apply();
})();
