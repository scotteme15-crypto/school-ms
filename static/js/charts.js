/* Bariso School Management System — inline SVG chart helpers. */
/* ------------------------------ CHARTS ---------------------------------- */
const PALETTE = ['var(--brand)', 'var(--brass)', 'var(--info)', 'var(--ok)', 'var(--bad)', 'var(--warn)', '#7C6BB5', '#4FA9A2'];
function barChart(data, opt = {}) {
  const W = 640, H = opt.height || 220, pl = 38, pb = 28, pt = 12, pr = 8;
  const max = opt.max || Math.max(1, ...data.map(d => d.value)) * 1.12;
  const iw = W - pl - pr, ih = H - pt - pb;
  const bw = iw / data.length;
  const ticks = 4;
  let g = '';
  for (let i = 0; i <= ticks; i++) {
    const y = pt + ih - (ih * i / ticks);
    g += `<line class="gl" x1="${pl}" x2="${W - pr}" y1="${y}" y2="${y}"/><text x="${pl - 7}" y="${y + 4}" text-anchor="end">${Math.round(max * i / ticks)}</text>`;
  }
  const bars = data.map((d, i) => {
    const h = Math.max(2, ih * (d.value / max));
    const x = pl + i * bw + bw * .22, y = pt + ih - h, w = bw * .56;
    return `<g><rect class="bar" x="${x}" y="${y}" width="${w}" height="${h}" rx="4" fill="${d.color || opt.color || 'var(--brand)'}"><title>${esc(d.label)}: ${d.value}${opt.unit || ''}</title></rect>
      ${opt.values !== false ? `<text x="${x + w / 2}" y="${y - 5}" text-anchor="middle" style="font-weight:600;fill:var(--tx-2)">${d.value}${opt.unit || ''}</text>` : ''}
      <text x="${pl + i * bw + bw / 2}" y="${H - 9}" text-anchor="middle">${esc(d.label)}</text></g>`;
  }).join('');
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opt.aria || 'Bar chart')}">${g}<line class="axis" x1="${pl}" x2="${W - pr}" y1="${pt + ih}" y2="${pt + ih}"/>${bars}</svg>`;
}
function stackedBar(groups, series, opt = {}) {
  const W = 640, H = opt.height || 230, pl = 38, pb = 28, pt = 12, pr = 8;
  const totals = groups.map(g => sum(series.map(s => g.values[s.key] || 0)));
  const max = Math.max(1, ...totals) * 1.1;
  const iw = W - pl - pr, ih = H - pt - pb, bw = iw / groups.length;
  let g = '';
  for (let i = 0; i <= 4; i++) { const y = pt + ih - ih * i / 4; g += `<line class="gl" x1="${pl}" x2="${W - pr}" y1="${y}" y2="${y}"/><text x="${pl - 7}" y="${y + 4}" text-anchor="end">${Math.round(max * i / 4)}</text>`; }
  const bars = groups.map((grp, i) => {
    let acc = 0;
    const segs = series.map(s => {
      const v = grp.values[s.key] || 0, h = ih * (v / max), y = pt + ih - h - acc;
      acc += h;
      return v ? `<rect class="bar" x="${pl + i * bw + bw * .24}" y="${y}" width="${bw * .52}" height="${h}" fill="${s.color}" rx="2"><title>${esc(grp.label)} · ${esc(s.label)}: ${v}</title></rect>` : '';
    }).join('');
    return segs + `<text x="${pl + i * bw + bw / 2}" y="${H - 9}" text-anchor="middle">${esc(grp.label)}</text>`;
  }).join('');
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opt.aria || 'Stacked bar chart')}">${g}<line class="axis" x1="${pl}" x2="${W - pr}" y1="${pt + ih}" y2="${pt + ih}"/>${bars}</svg>`;
}
function lineChart(points, opt = {}) {
  const W = 640, H = opt.height || 210, pl = 38, pb = 26, pt = 14, pr = 10;
  const max = opt.max || Math.max(1, ...points.map(p => p.value)) * 1.08;
  const min = opt.min != null ? opt.min : 0;
  const iw = W - pl - pr, ih = H - pt - pb;
  const X = i => pl + (points.length === 1 ? iw / 2 : iw * i / (points.length - 1));
  const Y = v => pt + ih - ih * ((v - min) / (max - min));
  let g = '';
  for (let i = 0; i <= 4; i++) { const y = pt + ih - ih * i / 4; g += `<line class="gl" x1="${pl}" x2="${W - pr}" y1="${y}" y2="${y}"/><text x="${pl - 7}" y="${y + 4}" text-anchor="end">${Math.round(min + (max - min) * i / 4)}</text>`; }
  const d = points.map((p, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)},${Y(p.value).toFixed(1)}`).join(' ');
  const area = d + ` L${X(points.length - 1)},${pt + ih} L${X(0)},${pt + ih} Z`;
  const dots = points.map((p, i) => `<circle cx="${X(i)}" cy="${Y(p.value)}" r="3.2" fill="var(--card)" stroke="${opt.color || 'var(--brand)'}" stroke-width="2"><title>${esc(p.label)}: ${p.value}${opt.unit || ''}</title></circle>`).join('');
  const labs = points.map((p, i) => (points.length > 9 && i % 2) ? '' : `<text x="${X(i)}" y="${H - 8}" text-anchor="middle">${esc(p.label)}</text>`).join('');
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opt.aria || 'Line chart')}">${g}
    <path d="${area}" fill="${opt.color || 'var(--brand)'}" opacity=".10"/>
    <path d="${d}" fill="none" stroke="${opt.color || 'var(--brand)'}" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>${dots}${labs}</svg>`;
}
function donut(segs, opt = {}) {
  const S = 180, cx = S / 2, cy = S / 2, r = 66, sw = 22;
  const total = sum(segs.map(s => s.value)) || 1;
  let a = -Math.PI / 2, paths = '';
  segs.forEach(s => {
    const ang = (s.value / total) * Math.PI * 2;
    if (s.value <= 0) return;
    const b = a + ang;
    const large = ang > Math.PI ? 1 : 0;
    const x1 = cx + r * Math.cos(a), y1 = cy + r * Math.sin(a), x2 = cx + r * Math.cos(b), y2 = cy + r * Math.sin(b);
    paths += ang >= Math.PI * 2 - 0.001
      ? `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${s.color}" stroke-width="${sw}"><title>${esc(s.label)}: ${s.value}</title></circle>`
      : `<path d="M${x1} ${y1} A${r} ${r} 0 ${large} 1 ${x2} ${y2}" fill="none" stroke="${s.color}" stroke-width="${sw}" stroke-linecap="butt"><title>${esc(s.label)}: ${s.value}</title></path>`;
    a = b;
  });
  return `<svg class="chart" viewBox="0 0 ${S} ${S}" style="max-width:190px;margin:0 auto" role="img" aria-label="${esc(opt.aria || 'Distribution')}">
    <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="var(--line-2)" stroke-width="${sw}"/>${paths}
    <text class="donut-mid" x="${cx}" y="${cy + 2}" text-anchor="middle"><tspan style="font-family:var(--serif);font-size:26px;fill:var(--tx)">${esc(opt.center || total)}</tspan></text>
    <text x="${cx}" y="${cy + 21}" text-anchor="middle">${esc(opt.sub || '')}</text></svg>`;
}
function legend(items) { return `<div class="legend">${items.map(i => `<span><i style="background:${i.color}"></i>${esc(i.label)}${i.value != null ? ` · ${i.value}` : ''}</span>`).join('')}</div>`; }
function hbars(rows, opt = {}) {
  const max = opt.max || Math.max(1, ...rows.map(r => r.value));
  return rows.map(r => `<div class="bar-row"><span class="lab" title="${esc(r.label)}">${esc(r.label)}</span>
    <span class="track"><span class="fill" style="width:${clamp(r.value / max * 100, 0, 100)}%;background:${r.color || 'var(--brand)'}"></span></span>
    <span class="val">${r.display != null ? esc(r.display) : r.value}${opt.unit || ''}</span></div>`).join('');
}
