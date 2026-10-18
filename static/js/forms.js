/* ==========================================================================
   FORM BEHAVIOUR
   Small conveniences for the Django-rendered forms: password visibility,
   confirmation dialogs for destructive POSTs, auto-submitting filters and a
   live (display-only) total for marks entry. Validation itself is done on the
   server by Django forms.
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

  /* --------------------------- show / hide password --------------------- */
  $$('[data-pw-toggle]').forEach(btn => {
    btn.innerHTML = ic('eye', 16);
    btn.onclick = () => {
      const input = document.querySelector(btn.getAttribute('data-pw-toggle'));
      if (!input) return;
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.innerHTML = ic(show ? 'lock' : 'eye', 16);
      btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    };
  });

  /* ------------------------------ confirm dialogs ----------------------- */
  $$('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
      if (form.dataset.confirmed === '1') return;
      e.preventDefault();
      confirmDialog({
        title: form.getAttribute('data-confirm-title') || 'Please confirm',
        body: form.getAttribute('data-confirm'),
        confirm: form.getAttribute('data-confirm-action') || 'Confirm',
        danger: form.getAttribute('data-confirm-danger') !== 'false',
      }).then(ok => {
        if (ok) { form.dataset.confirmed = '1'; form.submit(); }
      });
    });
  });

  /* --------------------------- auto-submitting filters ------------------ */
  $$('[data-autosubmit]').forEach(el => {
    el.addEventListener('change', () => el.form && el.form.submit());
  });

  /* ------------------------- marks entry live totals -------------------- */
  const sheet = $('[data-marks-sheet]');
  if (sheet) {
    const components = JSON.parse(sheet.getAttribute('data-components') || '[]');
    const maxTotal = components.reduce((sum, c) => sum + Number(c.max), 0) || 100;
    const bands = JSON.parse(sheet.getAttribute('data-bands') || '[]');
    const letterFor = pct => {
      for (const b of bands) { if (pct >= Number(b.min)) return b.letter; }
      return bands.length ? bands[bands.length - 1].letter : '—';
    };
    const recompute = () => {
      sheet.querySelectorAll('[data-mark-row]').forEach(row => {
        let total = 0;
        row.querySelectorAll('[data-score]').forEach(inp => {
          const max = Number(inp.getAttribute('data-max') || 0);
          let v = parseFloat(inp.value);
          if (isNaN(v)) v = 0;
          if (v < 0) { v = 0; inp.value = 0; }
          if (v > max) { v = max; inp.value = max; }
          total += v;
        });
        const pct = total / maxTotal * 100;
        const cell = row.querySelector('[data-row-total]');
        if (cell) cell.textContent = `${total} (${pct.toFixed(1)}%)`;
        const gradeCell = row.querySelector('[data-row-grade]');
        if (gradeCell) gradeCell.textContent = letterFor(pct);
      });
    };
    sheet.addEventListener('input', e => { if (e.target.matches('[data-score]')) recompute(); });
    recompute();
  }

  /* ------------------------- attendance bulk marking ------------------- */
  const att = $('[data-attendance-form]');
  if (att) {
    att.querySelectorAll('[data-set-all]').forEach(btn => {
      btn.onclick = () => {
        const status = btn.getAttribute('data-set-all');
        att.querySelectorAll('select[data-attendance-status]').forEach(sel => { sel.value = status; });
      };
    });
  }

  /* ------------------------------- tabs --------------------------------- */
  $$('[data-tabs]').forEach(group => {
    const buttons = group.querySelectorAll('[data-tab]');
    buttons.forEach(btn => {
      btn.onclick = () => {
        const target = btn.getAttribute('data-tab');
        buttons.forEach(b => b.classList.toggle('on', b === btn));
        group.querySelectorAll('[data-tab-panel]').forEach(p => {
          p.hidden = p.getAttribute('data-tab-panel') !== target;
        });
      };
    });
  });
});
