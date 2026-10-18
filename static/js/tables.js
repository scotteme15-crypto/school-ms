/* Bariso School Management System — client-side table search, sort and paging. */
/* ------------------------------ TABLE ----------------------------------- */
function makeTable(host, cfg) {
  const st = { q: '', sort: cfg.defaultSort || null, dir: cfg.defaultDir || 1, page: 1, size: cfg.pageSize || 10, filters: {} };
  (cfg.filters || []).forEach(f => st.filters[f.key] = f.value || '');
  function data() {
    let rows = cfg.rows.slice();
    const q = st.q.trim().toLowerCase();
    if (q && cfg.searchKeys) rows = rows.filter(r => cfg.searchKeys.some(k => String(typeof k === 'function' ? k(r) : r[k] ?? '').toLowerCase().includes(q)));
    (cfg.filters || []).forEach(f => {
      const v = st.filters[f.key];
      if (v !== '' && v != null) rows = rows.filter(r => f.test ? f.test(r, v) : String(r[f.key]) === String(v));
    });
    if (st.sort) {
      const col = cfg.columns.find(c => c.key === st.sort);
      if (col) rows = sortBy(rows, r => col.value ? col.value(r) : r[col.key], st.dir);
    }
    return rows;
  }
  function draw() {
    const rows = data();
    const pages = Math.max(1, Math.ceil(rows.length / st.size));
    st.page = clamp(st.page, 1, pages);
    const slice = rows.slice((st.page - 1) * st.size, st.page * st.size);
    const tools = `<div class="toolbar no-print">
      ${cfg.search === false ? '' : `<div class="search-inp"><span class="ic">${ic('search', 15)}</span><input type="search" value="${esc(st.q)}" placeholder="${esc(cfg.searchPlaceholder || 'Search')}" aria-label="Search this table" data-t="q"></div>`}
      ${(cfg.filters || []).map(f => `<select data-t="f" data-k="${f.key}" aria-label="${esc(f.label)}" style="width:auto;min-width:130px">
          <option value="">${esc(f.label)}</option>
          ${f.options.map(o => `<option value="${esc(o.value)}" ${String(st.filters[f.key]) === String(o.value) ? 'selected' : ''}>${esc(o.label)}</option>`).join('')}
        </select>`).join('')}
      ${cfg.toolbarRight || ''}
      ${cfg.exportName ? `<button class="btn sm" data-t="csv" style="margin-left:auto">${ic('down', 14)} Export CSV</button>` : ''}
    </div>`;
    const head = `<tr>${cfg.columns.map(c => `<th class="${c.cls || ''} ${c.sort === false ? '' : 'sortable'} ${st.sort === c.key ? 'act' : ''}" ${c.sort === false ? '' : `data-t="s" data-k="${c.key}" tabindex="0" role="button" aria-label="Sort by ${esc(c.label)}"`}>${esc(c.label)}${c.sort === false ? '' : `<span class="ar">${st.sort === c.key ? (st.dir > 0 ? '↑' : '↓') : '↕'}</span>`}</th>`).join('')}</tr>`;
    const body = slice.length ? slice.map((r, i) => `<tr data-id="${esc(r.id)}" ${cfg.rowClick ? 'style="cursor:pointer"' : ''}>${cfg.columns.map(c => `<td class="${c.cls || ''}">${c.render ? c.render(r, i) : esc(r[c.key] ?? '—')}</td>`).join('')}</tr>`).join('') : '';
    host.innerHTML = `${tools}
      ${slice.length ? `<div class="tablewrap"><table class="dt"><thead>${head}</thead><tbody>${body}</tbody></table></div>` : emptyState(cfg.empty || { title: 'Nothing to show', body: 'No records match the current search or filters.' })}
      ${rows.length > st.size ? `<div class="pager no-print">
        <span class="info">Showing ${(st.page - 1) * st.size + 1}–${Math.min(rows.length, st.page * st.size)} of ${rows.length}</span>
        <span class="pages">
          <button class="pgbtn" data-t="p" data-v="${st.page - 1}" ${st.page === 1 ? 'disabled' : ''} aria-label="Previous page">‹</button>
          ${pageList(st.page, pages).map(n => n === '…' ? `<span style="padding:0 4px;color:var(--tx-3)">…</span>` : `<button class="pgbtn" data-t="p" data-v="${n}" ${n === st.page ? 'aria-current="page"' : ''}>${n}</button>`).join('')}
          <button class="pgbtn" data-t="p" data-v="${st.page + 1}" ${st.page === pages ? 'disabled' : ''} aria-label="Next page">›</button>
        </span></div>` : `<div class="pager no-print"><span class="info">${rows.length} record${rows.length === 1 ? '' : 's'}</span></div>`}`;
    bind(rows);
  }
  function bind(rows) {
    const qi = host.querySelector('[data-t=q]');
    if (qi) {
      qi.oninput = debounce(e => { st.q = e.target.value; st.page = 1; draw(); const n = host.querySelector('[data-t=q]'); if (n) { n.focus(); n.setSelectionRange(n.value.length, n.value.length); } }, 180);
    }
    host.querySelectorAll('[data-t=f]').forEach(s => s.onchange = e => { st.filters[e.target.dataset.k] = e.target.value; st.page = 1; draw(); });
    host.querySelectorAll('[data-t=s]').forEach(t => {
      const go = () => { const k = t.dataset.k; if (st.sort === k) st.dir *= -1; else { st.sort = k; st.dir = 1; } draw(); };
      t.onclick = go; t.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } };
    });
    host.querySelectorAll('[data-t=p]').forEach(b => b.onclick = () => { st.page = +b.dataset.v; draw(); host.scrollIntoView({ block: 'nearest' }); });
    const cs = host.querySelector('[data-t=csv]');
    if (cs) cs.onclick = () => {
      const cols = cfg.columns.filter(c => !c.noExport);
      downloadCSV(cfg.exportName + '.csv', [cols.map(c => c.label), ...rows.map(r => cols.map(c => c.csv ? c.csv(r) : String(r[c.key] ?? '')))]);
      toast('success', 'Export ready', `${rows.length} rows written to ${cfg.exportName}.csv`);
    };
    if (cfg.rowClick) host.querySelectorAll('tbody tr').forEach(tr => tr.onclick = e => {
      if (e.target.closest('button,a,select,input')) return;
      cfg.rowClick(cfg.rows.find(r => String(r.id) === tr.dataset.id));
    });
    cfg.onDraw && cfg.onDraw(host);
  }
  draw();
  return { refresh(rows) { if (rows) cfg.rows = rows; draw(); }, state: st };
}
function pageList(p, n) {
  if (n <= 7) return Array.from({ length: n }, (_, i) => i + 1);
  const out = [1];
  if (p > 3) out.push('…');
  for (let i = Math.max(2, p - 1); i <= Math.min(n - 1, p + 1); i++) out.push(i);
  if (p < n - 2) out.push('…');
  out.push(n);
  return out;
}
function emptyState(e) {
  return `<div class="empty"><div class="ring">${ic(e.icon || 'db', 24)}</div><h3>${esc(e.title)}</h3><p>${esc(e.body)}</p>${e.action || ''}</div>`;
}
function loadingBlock(rows = 5) {
  return `<div class="panel-body">${Array.from({ length: rows }, (_, i) => `<div class="skel" style="width:${90 - i * 9}%;margin-bottom:12px"></div>`).join('')}</div>`;
}
function statusBadge(s) {
  const map = { approved: ['ok', 'Approved'], pending: ['warn', 'Pending'], rejected: ['bad', 'Rejected'], returned: ['info', 'Returned'], draft: ['', 'Draft'] };
  const [c, l] = map[s] || ['', s];
  return `<span class="badge ${c}"><span class="d"></span>${l}</span>`;
}
function personBadge(st) {
  const map = { Active: 'ok', Inactive: '', Graduated: 'info', Suspended: 'bad', 'On leave': 'warn' };
  return `<span class="badge ${map[st] || ''}">${esc(st)}</span>`;
}
function avatarFor(name, cls = '') { return `<span class="avatar ${cls}" aria-hidden="true">${esc(initials(name))}</span>`; }
