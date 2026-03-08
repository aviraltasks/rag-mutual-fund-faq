(function () {
  // On Vercel, API is under /api; when run by Phase 05 server locally, same-origin /chat and /last-updated
  const API_BASE = (typeof window !== 'undefined' && window.API_BASE) || '';
  const CHAT_URL = API_BASE + '/chat';
  const LAST_UPDATED_URL = API_BASE + '/last-updated';

  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const messagesEl = document.getElementById('chat-messages');
  const sendBtn = form.querySelector('.chat-send');

  // Load date/time into footer on page load so it appears without waiting for a chat response
  (function loadLastUpdated() {
    const footerEl = document.getElementById('last-updated-footer');
    if (!footerEl) return;
    fetch(LAST_UPDATED_URL).then(function (r) { return r.json(); }).then(function (data) {
      if (data && data.last_updated_note) footerEl.textContent = data.last_updated_note;
    }).catch(function () {});
  })();

  function addMessage(role, content, options = {}) {
    var isRefusal = options.refusal || (content && (content.toLowerCase().indexOf("don't have that information") !== -1 || content.toLowerCase().indexOf("no matching data") !== -1));
    const div = document.createElement('div');
    div.className = 'msg ' + role + (isRefusal ? ' refusal' : '');
    const textEl = document.createElement('div');
    textEl.className = 'msg-text';
    textEl.textContent = content;
    div.appendChild(textEl);
    if (options.citationUrl) {
      const links = document.createElement('div');
      links.className = 'msg-links';
      const a = document.createElement('a');
      a.href = options.citationUrl;
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = options.citationLabel || 'Source';
      links.appendChild(a);
      div.appendChild(links);
    }
    if (options.lastUpdatedNote) {
      const note = document.createElement('div');
      note.className = 'msg-note';
      note.textContent = options.lastUpdatedNote;
      div.appendChild(note);
      var footerEl = document.getElementById('last-updated-footer');
      if (footerEl) footerEl.textContent = options.lastUpdatedNote;
    }
    if (options.educationalLink) {
      const links = document.createElement('div');
      links.className = 'msg-links';
      const a = document.createElement('a');
      a.href = options.educationalLink;
      a.target = '_blank';
      a.rel = 'noopener';
      a.textContent = 'Learn more (investor education)';
      links.appendChild(a);
      div.appendChild(links);
    }
    if (options.suggestedQuery) {
      const tryDiv = document.createElement('div');
      tryDiv.className = 'msg-try-typing';
      tryDiv.appendChild(document.createTextNode('Try typing: '));
      const span = document.createElement('button');
      span.type = 'button';
      span.className = 'try-typing-btn';
      span.textContent = '"' + options.suggestedQuery + '"';
      span.addEventListener('click', function () {
        input.value = options.suggestedQuery;
        input.focus();
      });
      tryDiv.appendChild(span);
      div.appendChild(tryDiv);
    }
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function setLoading(loading) {
    if (!sendBtn) return;
    sendBtn.disabled = loading;
    if (loading) {
      sendBtn.setAttribute('aria-busy', 'true');
      sendBtn.classList.add('loading');
      sendBtn.innerHTML = '<span class="send-spinner" aria-hidden="true"></span> Searching…';
    } else {
      sendBtn.removeAttribute('aria-busy');
      sendBtn.classList.remove('loading');
      sendBtn.textContent = 'Send';
    }
  }

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const query = (input.value || '').trim();
    if (!query) return;
    input.value = '';
    addMessage('user', query);
    setLoading(true);
    try {
      const res = await fetch(CHAT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        addMessage('assistant', data.detail || 'Something went wrong. Please try again.', { refusal: true });
        return;
      }
      if (data.refusal) {
        addMessage('assistant', data.message, { refusal: true, educationalLink: data.educational_link || null });
        return;
      }
      var citationLabel = (data.citation_url && data.citation_url.indexOf('sbimf') !== -1) ? 'Download statements / factsheets' : 'Source';
      addMessage('assistant', data.answer, {
        citationUrl: data.citation_url || null,
        citationLabel: citationLabel,
        lastUpdatedNote: data.last_updated_note || null,
        suggestedQuery: data.suggested_query || null,
      });
      if (data.scheme_used) {
        var hintEl = document.getElementById('scheme-hint');
        var hintNameEl = document.getElementById('scheme-hint-name');
        if (hintNameEl) hintNameEl.textContent = data.scheme_used;
        if (hintEl) hintEl.style.display = 'block';
      }
    } catch (err) {
      addMessage('assistant', 'Unable to reach the server. Please try again.', { refusal: true });
    } finally {
      setLoading(false);
    }
  });

  document.querySelectorAll('.chip').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const q = this.getAttribute('data-query');
      if (q) {
        input.value = q;
        input.focus();
      }
    });
  });

  var schemeHintEl = document.getElementById('scheme-hint');
  var schemeHintNameEl = document.getElementById('scheme-hint-name');
  var FUNDS = [
    'SBI US Specific Equity Active FoF Fund',
    'SBI Nifty Index Fund',
    'SBI Flexicap Fund',
    'SBI ELSS Tax Saver Fund',
    'SBI Large Cap Fund'
  ];
  var roundRobinIndex = 0;
  document.querySelectorAll('.ask-about-link').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var q = this.getAttribute('data-query');
      var scheme = this.getAttribute('data-scheme');
      if (!q) return;
      var chosenFund = FUNDS[roundRobinIndex % FUNDS.length];
      roundRobinIndex += 1;
      var newQuery = scheme ? q.replace(new RegExp(scheme.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), chosenFund) : q;
      input.value = newQuery;
      form.requestSubmit();
    });
  });
})();
