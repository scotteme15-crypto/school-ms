/* Bariso School Management System — client UI kit (icons, utils, toasts, modals, popovers).
   Ported from the original design. Presentation and interaction only: no authoritative business rules. */
/* ------------------------------ ICONS ---------------------------------- */
const ICON = {
  dash:'<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
  users:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  user:'<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  cap:'<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c0 1 2.7 3 6 3s6-2 6-3v-5"/>',
  school:'<path d="M4 21V9l8-5 8 5v12"/><path d="M9 21v-6h6v6"/>',
  book:'<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/>',
  clip:'<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
  check:'<path d="m5 13 4 4L19 7"/>',
  checkc:'<circle cx="12" cy="12" r="9"/><path d="m8.5 12.5 2.5 2.5 4.5-5"/>',
  cal:'<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  file:'<path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7Z"/><path d="M14 2v5h5"/>',
  chart:'<path d="M3 3v18h18"/><rect x="7" y="11" width="3" height="7"/><rect x="12.5" y="7" width="3" height="11"/><rect x="18" y="13" width="3" height="5"/>',
  mega:'<path d="M3 11v2a1 1 0 0 0 1 1h3l6 4V6L7 10H4a1 1 0 0 0-1 1Z"/><path d="M17 9a4 4 0 0 1 0 6"/>',
  gear:'<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.2a1.6 1.6 0 0 0-2.7-1.1l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H3a2 2 0 1 1 0-4h.2a1.6 1.6 0 0 0 1.1-2.7l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 2.7-1.1V3a2 2 0 1 1 4 0v.2a1.6 1.6 0 0 0 2.7 1.1l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0 1.1 2.7H21a2 2 0 1 1 0 4h-.2a1.6 1.6 0 0 0-1.4 1.2Z"/>',
  scroll:'<path d="M5 4h11a2 2 0 0 1 2 2v12a2 2 0 0 0 2 2H8a2 2 0 0 1-2-2V6"/><path d="M6 4a2 2 0 0 0-2 2v2h4"/><path d="M10 9h5M10 13h5"/>',
  bell:'<path d="M18 8a6 6 0 1 0-12 0c0 7-3 8-3 8h18s-3-1-3-8"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
  search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  edit:'<path d="M11 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-5"/><path d="M18.4 2.6a2 2 0 0 1 2.8 2.8L12 14.6l-4 1 1-4Z"/>',
  trash:'<path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/>',
  eye:'<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
  down:'<path d="M12 3v13"/><path d="m7 12 5 5 5-5"/><path d="M4 21h16"/>',
  up:'<path d="M12 21V8"/><path d="m7 12 5-5 5 5"/><path d="M4 3h16"/>',
  print:'<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M6 15h12v6H6z"/>',
  x:'<path d="M18 6 6 18M6 6l12 12"/>',
  right:'<path d="m9 6 6 6-6 6"/>',
  downc:'<path d="m6 9 6 6 6-6"/>',
  sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon:'<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/>',
  out:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
  warn:'<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
  upload:'<path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M4 21h16"/>',
  filter:'<path d="M3 4h18l-7 8v7l-4 2v-9Z"/>',
  mail:'<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 6 10-6"/>',
  phone:'<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"/>',
  pin:'<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
  award:'<circle cx="12" cy="9" r="6"/><path d="m8.2 14-1.4 7L12 18.5 17.2 21l-1.4-7"/>',
  trend:'<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
  act:'<path d="M3 12h4l3 8 4-16 3 8h4"/>',
  grid:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  pencil:'<path d="M18.4 2.6a2 2 0 0 1 2.8 2.8L8 18.6l-4.5 1.4L5 15.5Z"/>',
  lock:'<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  refresh:'<path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/>',
  menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
  flag:'<path d="M5 21V4h14l-3 4 3 4H5"/>',
  db:'<ellipse cx="12" cy="5.5" rx="8" ry="3"/><path d="M4 5.5v13c0 1.7 3.6 3 8 3s8-1.3 8-3v-13"/><path d="M20 12c0 1.7-3.6 3-8 3s-8-1.3-8-3"/>'
};
const ic = (name, size = 17, cls = '') =>
  `<svg class="ic ${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[name] || ''}</svg>`;

/* ------------------------------ UTILS ---------------------------------- */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const uid = p => p + '_' + Math.random().toString(36).slice(2, 9);
const clamp = (n, a, b) => Math.max(a, Math.min(b, n));
const sum = a => a.reduce((x, y) => x + y, 0);
const avg = a => a.length ? sum(a) / a.length : 0;
const r1 = n => Math.round(n * 10) / 10;
const uniq = a => Array.from(new Set(a));
const sortBy = (a, f, dir = 1) => a.slice().sort((x, y) => {
  const p = f(x), q = f(y);
  if (typeof p === 'number' && typeof q === 'number') return (p - q) * dir;
  return String(p).localeCompare(String(q), undefined, { numeric: true }) * dir;
});
const ordinal = n => { const s = ['th', 'st', 'nd', 'rd'], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); };
const initials = n => String(n).trim().split(/\s+/).slice(0, 2).map(w => w[0]).join('').toUpperCase();
const pad = n => String(n).padStart(2, '0');
const iso = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
function fmtDate(s) { if (!s) return '—'; const d = new Date(s); if (isNaN(d)) return '—'; return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`; }
function fmtDateTime(s) { const d = new Date(s); if (isNaN(d)) return '—'; return `${fmtDate(s)}, ${pad(d.getHours())}:${pad(d.getMinutes())}`; }
function timeAgo(s) {
  const d = (Date.now() - new Date(s)) / 1000;
  if (d < 60) return 'just now';
  if (d < 3600) return Math.floor(d / 60) + 'm ago';
  if (d < 86400) return Math.floor(d / 3600) + 'h ago';
  if (d < 604800) return Math.floor(d / 86400) + 'd ago';
  return fmtDate(s);
}
function debounce(fn, ms = 220) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function on(sel, ev, fn, root = document) { root.addEventListener(ev, e => { const t = e.target.closest(sel); if (t && root.contains(t)) fn(e, t); }); }
function downloadCSV(filename, rows) {
  const body = rows.map(r => r.map(c => {
    const v = c == null ? '' : String(c);
    return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }).join(',')).join('\r\n');
  const blob = new Blob(['\uFEFF' + body], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = filename;
  document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 400);
}

/* --------------------------- STORAGE LAYER ------------------------------ */

/* ------------------------------ TOASTS ---------------------------------- */
function toast(kind, title, msg, ms = 4200) {
  const host = $('#toasts');
  const el = document.createElement('div');
  el.className = 'toast ' + kind;
  const icons = { success: 'checkc', error: 'warn', warning: 'warn', info: 'info' };
  el.innerHTML = `<span class="tic">${ic(icons[kind] || 'info', 18)}</span>
    <div style="min-width:0"><b>${esc(title)}</b>${msg ? `<p>${esc(msg)}</p>` : ''}</div>
    <button class="rowbtn" aria-label="Dismiss" style="margin-left:auto">${ic('x', 15)}</button>`;
  const kill = () => { el.classList.add('out'); setTimeout(() => el.remove(), 200); };
  el.querySelector('button').onclick = kill;
  host.appendChild(el);
  setTimeout(kill, ms);
}

/* ------------------------------ MODALS ---------------------------------- */
let modalStack = [];
function openModal({ title, subtitle, body, footer, size = '', onMount, onClose }) {
  const scrim = document.createElement('div');
  scrim.className = 'scrim';
  scrim.innerHTML = `<div class="modal ${size}" role="dialog" aria-modal="true" aria-label="${esc(title)}">
      <div class="modal-head">
        <div style="min-width:0"><h2>${esc(title)}</h2>${subtitle ? `<p>${esc(subtitle)}</p>` : ''}</div>
        <button class="rowbtn x" aria-label="Close">${ic('x', 18)}</button>
      </div>
      <div class="modal-body">${body}</div>
      ${footer ? `<div class="modal-foot">${footer}</div>` : ''}
    </div>`;
  const prev = document.activeElement;
  const close = () => {
    scrim.remove(); modalStack = modalStack.filter(m => m !== close);
    if (!modalStack.length) document.body.style.overflow = '';
    if (prev && prev.focus) prev.focus();
    onClose && onClose();
  };
  scrim.querySelector('.x').onclick = close;
  scrim.addEventListener('mousedown', e => { if (e.target === scrim) close(); });
  document.body.style.overflow = 'hidden';
  $('#layers').appendChild(scrim);
  modalStack.push(close);
  const first = scrim.querySelector('input,select,textarea,button.primary');
  if (first) setTimeout(() => first.focus(), 40);
  onMount && onMount(scrim.querySelector('.modal'), close);
  return close;
}
function confirmDialog({ title, body, confirm = 'Confirm', danger = false, requireText = null }) {
  return new Promise(res => {
    let settled = false;
    const finish = v => { if (settled) return; settled = true; res(v); };
    const close = openModal({
      title, size: 'narrow',
      body: `<p style="margin:0;color:var(--tx-2);font-size:14.5px">${body}</p>
        ${requireText ? `<div class="field" style="margin-top:14px"><label for="cdReason">${esc(requireText)}</label><textarea id="cdReason" rows="3" placeholder="Explain what needs to change."></textarea><span class="fielderr" id="cdErr" hidden>A reason is required.</span></div>` : ''}`,
      footer: `<button class="btn" data-x="no">Cancel</button><button class="btn ${danger ? 'danger' : 'primary'}" data-x="yes">${esc(confirm)}</button>`,
      onMount(m) {
        m.querySelector('[data-x=no]').onclick = () => { finish(false); close(); };
        m.querySelector('[data-x=yes]').onclick = () => {
          if (requireText) {
            const v = m.querySelector('#cdReason').value.trim();
            if (v.length < 5) { m.querySelector('#cdErr').hidden = false; m.querySelector('#cdReason').classList.add('err'); return; }
            finish(v); close(); return;
          }
          finish(true); close();
        };
      },
      onClose: () => finish(false)
    });
  });
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && modalStack.length) { modalStack[modalStack.length - 1](); }
});


/* ------------------------------ POPOVER --------------------------------- */
let popEl = null;
function closePop() { if (popEl) { popEl.remove(); popEl = null; } }
function openPop(anchor, html, opts = {}) {
  closePop();
  const p = document.createElement('div');
  p.className = 'pop'; p.innerHTML = html;
  $('#layers').appendChild(p);
  const r = anchor.getBoundingClientRect();
  const w = p.offsetWidth, h = p.offsetHeight;
  let left = opts.align === 'left' ? r.left : r.right - w;
  left = clamp(left, 10, window.innerWidth - w - 10);
  let top = opts.up ? r.top - h - 8 : r.bottom + 8;
  if (top + h > window.innerHeight - 10) top = Math.max(10, r.top - h - 8);
  p.style.left = left + 'px'; p.style.top = top + 'px'; p.style.position = 'fixed';
  popEl = p;
  setTimeout(() => document.addEventListener('mousedown', function h2(e) {
    if (popEl && !popEl.contains(e.target) && !anchor.contains(e.target)) { closePop(); document.removeEventListener('mousedown', h2); }
  }), 0);
  return p;
}
window.addEventListener('resize', closePop);



/* ==========================================================================
   APPLICATION WIRING
   The pages are rendered server-side by Django. Everything below is purely
   presentational: theme, navigation, notifications, the command palette,
   client-side table search/sort and chart painting. No business rules and no
   authoritative data live here — every mutation is a normal Django form POST.
   ========================================================================== */

const THEME_KEY = 'bariso.theme';
const csrfToken = () => ($('meta[name="csrf-token"]') || {}).content || '';

/* --------------------------------- theme -------------------------------- */
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  try { localStorage.setItem(THEME_KEY, t); } catch (e) {}
  const btn = $('#themeBtn');
  if (btn) btn.innerHTML = ic(t === 'dark' ? 'sun' : 'moon', 17);
}
function initTheme() {
  let t = 'light';
  try { t = localStorage.getItem(THEME_KEY) || 'light'; } catch (e) {}
  applyTheme(t);
  const btn = $('#themeBtn');
  if (btn) btn.onclick = () => {
    const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    applyTheme(next);
  };
}

/* ------------------------------- sidebar -------------------------------- */
function initSidebar() {
  const body = document.body;
  const open = $('#openNav'), close = $('#closeNav');
  if (open) open.innerHTML = ic('menu', 18);
  if (close) { close.innerHTML = ic('x', 18); close.style.display = 'grid'; }

  const show = () => {
    body.classList.add('nav-open');
    if (!$('.nav-scrim')) {
      const s = document.createElement('div');
      s.className = 'nav-scrim';
      s.onclick = hide;
      body.appendChild(s);
    }
  };
  const hide = () => { body.classList.remove('nav-open'); $$('.nav-scrim').forEach(x => x.remove()); };
  if (open) open.onclick = show;
  if (close) close.onclick = hide;
  $$('.nav a').forEach(a => addEventListener('click', hide));
  window.addEventListener('resize', () => { if (window.innerWidth > 900) hide(); });
}

/* ----------------------------- notifications ---------------------------- */
function readJSON(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  try { return JSON.parse(el.textContent); } catch (e) { return null; }
}
function initBell() {
  const btn = $('#bellBtn');
  if (!btn) return;
  btn.innerHTML = ic('bell', 17);
  const items = readJSON('notifData') || [];
  const unread = readJSON('notifUnread') || 0;
  if (unread > 0) {
    const dot = document.createElement('span');
    dot.className = 'dot';
    btn.appendChild(dot);
  }
  btn.onclick = () => {
    const kindIcon = { result: 'clip', warning: 'warn', announcement: 'mega', exam: 'scroll', system: 'info' };
    const body = items.length ? items.map(n => `
      <a class="pop-item" href="${n.url || '#'}">
        <span class="dotic">${ic(kindIcon[n.kind] || 'info', 15)}</span>
        <span style="min-width:0"><b style="font-size:13.5px">${esc(n.title)}</b>
        <span style="display:block;color:var(--tx-3);font-size:12.5px">${esc(n.body || '')}</span></span>
        ${n.read ? '' : '<span class="badge" style="margin-left:auto">New</span>'}
      </a>`).join('') : `<div class="pop-item" style="color:var(--tx-3)">You have no notifications yet.</div>`;
    openPop(btn, `
      <div class="pop-head">${ic('bell', 15)} Notifications
        <a href="${(readJSON('notifUrl') || '#')}" style="margin-left:auto;font-size:12.5px;font-weight:600">View all</a>
      </div>
      <div style="max-height:340px;overflow:auto">${body}</div>`, { up: false });
  };
}

/* ------------------------------ profile menu ---------------------------- */
function initProfileMenu() {
  const btn = $('#whoBtn');
  if (!btn) return;
  btn.onclick = () => {
    const menu = $('#profileMenuData');
    openPop(btn, menu ? menu.innerHTML : '', { up: true });
  };
}

/* -------------------------------- charts -------------------------------- */
function initCharts() {
  $$('[data-chart]').forEach(host => {
    let data;
    try { data = JSON.parse(host.getAttribute('data-chart')); } catch (e) { return; }
    const type = host.getAttribute('data-chart-type') || 'bar';
    const opt = { height: +(host.getAttribute('data-chart-height') || 220), unit: host.getAttribute('data-chart-unit') || '' };
    if (type === 'bar') host.innerHTML = barChart(data, opt);
    else if (type === 'line') host.innerHTML = lineChart(data, opt);
    else if (type === 'donut') host.innerHTML = donut(data, opt);
    else if (type === 'hbars') host.innerHTML = hbars(data, opt);
    else if (type === 'stacked') {
      const series = JSON.parse(host.getAttribute('data-chart-series') || '[]');
      host.innerHTML = stackedBar(data, series, opt);
    }
  });
}

/* ------------------------- server-rendered tables ----------------------- */
function initServerTables() {
  $$('[data-server-table]').forEach(wrap => {
    const table = wrap.querySelector('table');
    if (!table) return;
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    const searchInput = wrap.querySelector('[data-table-search]');
    const rows = Array.from(tbody.querySelectorAll('tr')).filter(r => !r.hasAttribute('data-empty'));
    const emptyRow = tbody.querySelector('[data-empty]');
    const pageSize = +(wrap.getAttribute('data-page-size') || 0);

    function filter() {
      const q = (searchInput ? searchInput.value : '').trim().toLowerCase();
      let shown = 0;
      rows.forEach(r => {
        const match = !q || r.textContent.toLowerCase().includes(q);
        r.hidden = !match;
        if (match) shown++;
      });
      if (emptyRow) emptyRow.hidden = shown !== 0;
      const counter = wrap.querySelector('[data-table-count]');
      if (counter) counter.textContent = shown;
      if (pageSize) paginate(shown);
    }

    let page = 1;
    function paginate(shown) {
      const visible = rows.filter(r => !r.hidden);
      const pages = Math.max(1, Math.ceil(visible.length / pageSize));
      page = Math.min(page, pages);
      visible.forEach((r, i) => { r.hidden = !(i >= (page - 1) * pageSize && i < page * pageSize); });
      const host = wrap.querySelector('[data-table-pager]');
      if (host) {
        host.innerHTML = `<span>Page ${page} of ${pages}</span>
          <span class="pages">
            <button class="btn sm" data-pg="prev" ${page === 1 ? 'disabled' : ''}>Prev</button>
            <button class="btn sm" data-pg="next" ${page === pages ? 'disabled' : ''}>Next</button>
          </span>`;
        host.querySelectorAll('[data-pg]').forEach(b => b.onclick = () => {
          page += b.getAttribute('data-pg') === 'next' ? 1 : -1;
          paginate();
        });
      }
    }

    if (searchInput) searchInput.oninput = debounce(filter, 120);

    table.querySelectorAll('th[data-sort]').forEach(th => {
      th.style.cursor = 'pointer';
      th.onclick = () => {
        const key = th.getAttribute('data-sort');
        const dir = th.getAttribute('data-dir') === 'asc' ? -1 : 1;
        table.querySelectorAll('th[data-sort]').forEach(x => x.removeAttribute('data-dir'));
        th.setAttribute('data-dir', dir === 1 ? 'asc' : 'desc');
        const val = r => {
          const cell = r.querySelector(`[data-cell="${key}"]`);
          const raw = cell ? (cell.getAttribute('data-value') || cell.textContent) : r.textContent;
          const num = parseFloat(String(raw).replace(/[^0-9.\-]/g, ''));
          return isNaN(num) ? String(raw).toLowerCase() : num;
        };
        rows.sort((a, b) => (val(a) > val(b) ? 1 : val(a) < val(b) ? -1 : 0) * dir);
        rows.forEach(r => tbody.appendChild(r));
        page = 1;
        filter();
      };
    });

    filter();
  });
}

/* --------------------------- command palette ---------------------------- */
function initSearch() {
  const btn = $('#searchBtn');
  if (!btn) return;
  const open = () => {
    const layer = document.createElement('div');
    layer.className = 'cmd';
    layer.innerHTML = `
      <div style="width:100%;max-width:620px;background:var(--card);border-radius:var(--r-lg);box-shadow:var(--shadow-lg);overflow:hidden">
        <div class="cmd-in">${ic('search', 18)}
          <input id="cmdQ" type="search" placeholder="Search students, teachers, classes…" autocomplete="off"
                 style="border:0;background:none;outline:none;flex:1;font-size:15px">
          <kbd style="border:1px solid var(--line);border-radius:5px;padding:1px 6px;font-size:11px">Esc</kbd>
        </div>
        <div id="cmdOut" style="max-height:52vh;overflow:auto;padding:8px">
          <p style="color:var(--tx-3);font-size:13px;padding:10px 12px;margin:0">Start typing to search your records.</p>
        </div>
      </div>`;
    $('#layers').appendChild(layer);
    const close = () => { layer.remove(); document.removeEventListener('keydown', onKey); };
    const onKey = e => { if (e.key === 'Escape') close(); };
    document.addEventListener('keydown', onKey);
    layer.addEventListener('mousedown', e => { if (e.target === layer) close(); });
    const q = $('#cmdQ');
    q.focus();
    q.oninput = debounce(async () => {
      const term = q.value.trim();
      const out = $('#cmdOut');
      if (term.length < 2) { out.innerHTML = `<p style="color:var(--tx-3);font-size:13px;padding:10px 12px;margin:0">Type at least two characters.</p>`; return; }
      out.innerHTML = loadingBlock(3);
      try {
        const res = await fetch(`/search/?q=${encodeURIComponent(term)}`, { headers: { 'X-Requested-With': 'fetch' } });
        const data = await res.json();
        out.innerHTML = data.results.length ? data.results.map(r => `
          <a class="cmd-row" href="${r.url}">${ic(r.icon || 'search', 17)}
            <span style="min-width:0"><b style="font-size:13.8px">${esc(r.label)}</b>
            <span style="display:block;color:var(--tx-3);font-size:12.5px">${esc(r.sub || '')}</span></span>
            <span class="badge" style="margin-left:auto">${esc(r.kind)}</span>
          </a>`).join('') : `<p style="color:var(--tx-3);font-size:13px;padding:10px 12px;margin:0">No matches found.</p>`;
      } catch (e) {
        out.innerHTML = `<p style="color:var(--bad);font-size:13px;padding:10px 12px;margin:0">Search is unavailable right now.</p>`;
      }
    }, 180);
  };
  btn.onclick = open;
  document.addEventListener('keydown', e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); open(); }
  });
}

/* ------------------------------ flash messages -------------------------- */
function initMessages() {
  const items = readJSON('djangoMessages');
  if (!items) return;
  const map = { success: 'success', error: 'error', warning: 'warning', info: 'info', debug: 'info' };
  items.forEach(m => toast(map[m.level] || 'info', m.text, '', 5200));
}

/* --------------------------------- print -------------------------------- */
function initPrint() {
  $$('[data-print]').forEach(btn => {
    btn.onclick = () => {
      document.body.classList.add('print-report');
      window.print();
      setTimeout(() => document.body.classList.remove('print-report'), 400);
    };
  });
}

/* ------------------------------- boot ----------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSidebar();
  initBell();
  initProfileMenu();
  initCharts();
  initServerTables();
  initSearch();
  initMessages();
  initPrint();
});
