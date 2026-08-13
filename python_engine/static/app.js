/* =========================================================
   Jain Panchang – SPA
   Hash-based routing: #home | #calendar | #panchang |
                       #muhurta | #choghadiya | #location | #settings
   ========================================================= */

'use strict';

// ── State ─────────────────────────────────────────────────────
const STORAGE_KEY = 'jain_panchang_v2';

function loadState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  } catch { return {}; }
}

function saveState(patch) {
  const s = { ...loadState(), ...patch };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  return s;
}

function getState() { return loadState(); }

// ── API ───────────────────────────────────────────────────────
async function apiFetch(path, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

function todayStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

function formatDateLabel(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  return dt.toLocaleDateString('en-IN', { weekday: 'short', year: 'numeric', month: 'long', day: 'numeric' });
}

// ── Time formatting ───────────────────────────────────────────
function to24h(timeStr) {
  // "HH:MM" or "HH:MM:SS" already in 24h → return HH:MM
  if (!timeStr) return '—';
  return timeStr.slice(0, 5);
}

function to12h(timeStr) {
  if (!timeStr) return '—';
  const [h, m] = timeStr.split(':').map(Number);
  const suffix = h >= 12 ? 'PM' : 'AM';
  const h12 = h % 12 || 12;
  return `${String(h12).padStart(2,'0')}:${String(m).padStart(2,'0')} ${suffix}`;
}

function formatTime(timeStr, fmt) {
  return fmt === '12h' ? to12h(timeStr) : to24h(timeStr);
}

// ── Moon phase emoji from tithi index (1-30) ─────────────────
function moonEmoji(tithiIndex) {
  const idx = tithiIndex || 1;
  if (idx <= 2)  return '🌑';
  if (idx <= 7)  return '🌒';
  if (idx <= 12) return '🌓';
  if (idx <= 14) return '🌔';
  if (idx === 15) return '🌕';
  if (idx <= 17) return '🌖';
  if (idx <= 22) return '🌗';
  if (idx <= 27) return '🌘';
  return '🌑';
}

function chogQualityLabel(nature) {
  if (nature === 'auspicious') return 'Auspicious';
  if (nature === 'inauspicious') return 'Inauspicious';
  return 'Neutral';
}

// ── Router ────────────────────────────────────────────────────
const pages = {};

function registerPage(id, controller) {
  pages[id] = controller;
}

let _prevHash = null;
let _activeController = null;

function getHashParts() {
  const raw = location.hash.slice(1) || 'home';
  const [page, queryStr] = raw.split('?');
  const params = {};
  if (queryStr) {
    queryStr.split('&').forEach(p => {
      const [k, v] = p.split('=');
      params[decodeURIComponent(k)] = decodeURIComponent(v || '');
    });
  }
  return { page: page || 'home', params };
}

function navigate(page, params = {}) {
  const query = Object.keys(params).length
    ? '?' + Object.entries(params).map(([k,v]) => `${k}=${encodeURIComponent(v)}`).join('&')
    : '';
  const targetHash = page + query;
  if (location.hash === '#' + targetHash) {
    route();
  } else {
    location.hash = targetHash;
  }
}

function route() {
  const { page, params } = getHashParts();

  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

  const el = document.getElementById(`page-${page}`);
  if (el) el.classList.add('active');

  if (_activeController && _activeController.onLeave) _activeController.onLeave();

  const ctrl = pages[page];
  if (ctrl) {
    _activeController = ctrl;
    ctrl.onEnter(params);
  }

  window.scrollTo(0, 0);
}

// ── Theme ─────────────────────────────────────────────────────
const THEME_KEY = 'jain_panchang_theme';

function initTheme() {
  const savedTheme = localStorage.getItem(THEME_KEY) || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);

  const toggleButtons = document.querySelectorAll('#themeToggleHome, #themeToggleDrawer, .theme-toggle-btn');
  toggleButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem(THEME_KEY, next);
    });
  });
}

// ── Drawer ────────────────────────────────────────────────────
function initDrawer() {
  const overlay = document.getElementById('drawerOverlay');
  const drawer  = document.getElementById('drawer');

  function open() {
    if (overlay) {
      overlay.classList.add('open');
      overlay.classList.add('active');
    }
    if (drawer) {
      drawer.classList.add('open');
      drawer.classList.add('active');
    }
  }
  function close() {
    if (overlay) {
      overlay.classList.remove('open');
      overlay.classList.remove('active');
    }
    if (drawer) {
      drawer.classList.remove('open');
      drawer.classList.remove('active');
    }
  }

  if (overlay) overlay.addEventListener('click', close);

  document.querySelectorAll('[id$="MenuBtn"]').forEach(btn => {
    btn.addEventListener('click', open);
  });

  if (drawer) {
    drawer.querySelectorAll('[data-nav]').forEach(btn => {
      btn.addEventListener('click', () => { navigate(btn.dataset.nav); close(); });
    });
  }
}

// ── Shared: data-nav buttons (Event Delegation) ─────────────────
function initNavButtons() {
  document.addEventListener('click', (e) => {
    const navBtn = e.target.closest('[data-nav]');
    if (navBtn) {
      const page = navBtn.dataset.nav;
      if (page) {
        navigate(page);
        const overlay = document.getElementById('drawerOverlay');
        const drawer  = document.getElementById('drawer');
        if (overlay) { overlay.classList.remove('open'); overlay.classList.remove('active'); }
        if (drawer)  { drawer.classList.remove('open');  drawer.classList.remove('active'); }
      }
    }
  });
}

// ── Tithi row helpers ─────────────────────────────────────────
function tithiEndSub(tithi, panchangDate, ft) {
  if (tithi.continues_past_next_sunrise || !tithi.ends) return '';
  const endTime = ft(tithi.ends.time);
  const endDate = tithi.ends.local?.slice(0, 10);
  if (endDate && endDate !== panchangDate) {
    const label = new Date(endDate + 'T12:00:00').toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short',
    });
    return `upto ${endTime}, ${label}`;
  }
  return `upto ${endTime}`;
}

function tithiRows(tithiField, panchangDate, ft) {
  const arr = Array.isArray(tithiField) ? tithiField : (tithiField ? [tithiField] : []);
  return arr.map((t, i) => ({
    label: i === 0 ? 'Tithi' : '',
    value: t.name || '—',
    sub: tithiEndSub(t, panchangDate, ft),
  }));
}

// ── Date Banner render ────────────────────────────────────────
function renderDateBanner(moonEl, gregorianEl, detailsEl, data) {
  const p = data.panchang;
  const tithiArr = Array.isArray(p.tithi) ? p.tithi : (p.tithi ? [p.tithi] : []);
  const tithiIdx = tithiArr[0]?.index || 1;
  moonEl.textContent = moonEmoji(tithiIdx);

  const dt = new Date(data.date + 'T00:00:00');
  gregorianEl.textContent = dt.toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  });

  const samvat   = p.vikram_samvat || '—';
  const month    = p.hindu_month?.name || '—';
  const tithi    = tithiArr.map(t => t.name).join(' / ') || '—';
  const location = data.location || '—';
  detailsEl.textContent = `VS ${samvat} | ${month} | ${tithi} | ${location}`;
}

async function showFestivalDetailById(occurrenceId) {
  const year = parseInt(occurrenceId.split(':').pop().slice(0, 4), 10);
  const state = getState();
  const profile = state.jainProfile || 'shwetambar_murtipujak_tapagachchha';
  let f = festState.festivals.find(x => x.occurrence_id === occurrenceId);
  if (f) {
    openFestivalModal(f);
    return;
  }
  try {
    const data = await apiFetch('/generate-jain-festivals', 'POST', {
      year, lat: state.lat, lon: state.lon, ayanamsa: state.ayanamsa || 'Lahiri', profile
    });
    festState.festivals = data.festivals || [];
    f = festState.festivals.find(x => x.occurrence_id === occurrenceId);
    if (f) openFestivalModal(f);
  } catch (err) {
    alert("Could not load festival details: " + err.message);
  }
}

// ── HOME ──────────────────────────────────────────────────────
registerPage('home', {
  onEnter() {
    const state = getState();
    const moonEl     = document.getElementById('homeBanner').querySelector('.date-banner-moon');
    const gregorian  = document.getElementById('homeGregorianDate');
    const details    = document.getElementById('homeBannerDetails');
    const daily      = document.getElementById('homeDailyContent');

    if (!state.lat || !state.lon) {
      const dt = new Date();
      gregorian.textContent = dt.toLocaleDateString('en-IN', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
      });
      details.innerHTML = '<span data-nav="location" style="cursor:pointer;">📍 Set a location for Panchang data</span>';
      daily.innerHTML = '<div class="home-daily-empty" data-nav="location" style="cursor:pointer;">📍 Set a location to calculate today’s Jain Tithi.</div>';
      return;
    }

    daily.innerHTML = '<div class="loading-spinner">Calculating...</div>';
    apiFetch('/generate-panchang', 'POST', {
      date: todayStr(), lat: state.lat, lon: state.lon, ayanamsa: state.ayanamsa || 'Lahiri'
    }).then(data => {
      renderDateBanner(moonEl, gregorian, details, data);
      const p = data.panchang || {};
      const ev = data.events || {};
      const jain = p.jain_tithi;
      const sunrise = ev.sunrise?.time?.slice(0, 5) || '—';
      daily.innerHTML = `
        <section class="home-daily-panel" data-nav="panchang">
          <div class="home-daily-label">Today’s Jain Tithi</div>
          <div class="home-daily-tithi">${jain?.name || '—'}</div>
          <div class="home-daily-meta">
            <span>Sunrise ${formatTime(sunrise, getState().timeFormat || '12h')}</span>
            <span>${p.vara?.name || ''}</span>
          </div>
        </section>
      `;
      daily.querySelector('[data-nav="panchang"]').addEventListener('click', () => navigate('panchang'));
    }).catch(e => {
      details.textContent = e.message;
      daily.innerHTML = `<div class="home-daily-empty">${e.message}</div>`;
    });
  }
});

// ── CALENDAR ──────────────────────────────────────────────────
const calState = { year: new Date().getFullYear(), month: new Date().getMonth() + 1 };

const MONTH_NAMES = ['January','February','March','April','May','June',
                     'July','August','September','October','November','December'];

registerPage('calendar', {
  onEnter() {
    this._renderNav();
    this._load();
  },

  onLeave() {},

  _renderNav() {
    const label = `${MONTH_NAMES[calState.month - 1]} ${calState.year}`;
    document.getElementById('calMonthTitle').textContent = label;
    document.getElementById('calNavTitle').textContent  = label;
  },

  async _load() {
    const state = getState();
    const grid  = document.getElementById('calGrid');
    grid.innerHTML = '<div class="cal-loading">Calculating...</div>';

    if (!state.lat || !state.lon) {
      grid.innerHTML = '<div class="cal-loading">Set a location to see the calendar.</div>';
      return;
    }

    try {
      const profile = state.jainProfile || 'shwetambar_murtipujak_tapagachchha';
      const data = await apiFetch(
        `/month-overview?year=${calState.year}&month=${calState.month}&lat=${state.lat}&lon=${state.lon}&ayanamsa=${state.ayanamsa || 'Lahiri'}&profile=${profile}`
      );

      document.getElementById('calSamvat').textContent = `Vikram Samvat ${data.vikram_samvat} | ${data.hindu_month}`;

      this._renderGrid(data.days);
    } catch (e) {
      grid.innerHTML = `<div class="cal-loading">${e.message}</div>`;
    }
  },

  _renderGrid(days) {
    const grid  = document.getElementById('calGrid');
    const today = todayStr();
    const fmt   = getState().timeFormat || '12h';

    const firstDate = new Date(days[0].date + 'T00:00:00');
    const startWeekday = firstDate.getDay(); // 0=Sun

    grid.innerHTML = '';

    // Empty cells before first day
    for (let i = 0; i < startWeekday; i++) {
      const empty = document.createElement('div');
      empty.className = 'cal-cell empty';
      grid.appendChild(empty);
    }

    days.forEach(day => {
      const cell = document.createElement('div');
      cell.className = 'cal-cell' + (day.date === today ? ' today' : '');
      
      const isReview = day.jain_festivals && day.jain_festivals.some(f => f.status === 'review_needed');
      if (isReview) cell.className += ' review-needed-cell';

      const dayNum = parseInt(day.date.split('-')[2], 10);
      const tithiText = day.tithi_name || day.tithi_index || '';
      const tithiTime = day.tithi_end_time ? `<span class="cal-endtime">${day.tithi_end_time}</span>` : '';
      const nakName = day.nakshatra_name || '';
      const nakTime = day.nakshatra_end_time ? `<span class="cal-endtime">${day.nakshatra_end_time}</span>` : '';
      const weekdayHindi = new Date(day.date + 'T00:00:00').toLocaleDateString('hi-IN', { weekday: 'long' });
      const srText = day.sunrise_time ? formatTime(day.sunrise_time, fmt) : '';
      const ssText = day.sunset_time  ? formatTime(day.sunset_time,  fmt) : '';

      let markersHTML = '';
      if (day.jain_festivals && day.jain_festivals.length) {
        const mainFests = day.jain_festivals.filter(f => f.category !== 'parva');
        if (mainFests.length) {
          markersHTML = `<div class="fest-markers-container" style="margin-top:4px;">` +
            mainFests.map(f => {
              const catClass = f.status === 'review_needed' ? 'review' : f.category;
              return `<div class="fest-marker fest-marker--${catClass}" data-festid="${f.occurrence_id}" style="font-size:7px; cursor:pointer;">${f.name}</div>`;
            }).join('') + `</div>`;
        }
      }

      const panchakBadge = day.has_panchak
        ? `<div class="cal-panchak-marker" data-panchak-date="${day.date}">पंचक</div>`
        : '';

      cell.innerHTML = `
        <div class="cal-cell-header">
          <span class="cal-date">${dayNum}</span>
        </div>
        <div class="cal-cell-body">
          <span class="cal-cell-label">Tithi</span>
          <span class="cal-value">${tithiText}</span>
          ${tithiTime}
          <span class="cal-nakshatra-row">${nakName}</span>
        </div>
        ${markersHTML}
        ${panchakBadge}
        ${srText || ssText ? `<div class="cal-sun-row"><span data-sr>${srText}</span><span data-ss>${ssText}</span></div>` : ''}
        <div class="cal-cell-footer">${weekdayHindi}</div>
      `;

      cell.addEventListener('click', (e) => {
        const panchakMarker = e.target.closest('[data-panchak-date]');
        if (panchakMarker) {
          e.stopPropagation();
          navigate('panchak', { date: panchakMarker.dataset.panchakDate });
          return;
        }
        const marker = e.target.closest('[data-festid]');
        if (marker) {
          e.stopPropagation();
          showFestivalDetailById(marker.dataset.festid);
        } else {
          navigate('panchang', { date: day.date });
        }
      });
      grid.appendChild(cell);
    });

  }
});

document.getElementById('calPrev').addEventListener('click', () => {
  calState.month--;
  if (calState.month < 1) { calState.month = 12; calState.year--; }
  pages['calendar']._renderNav();
  pages['calendar']._load();
});

document.getElementById('calNext').addEventListener('click', () => {
  calState.month++;
  if (calState.month > 12) { calState.month = 1; calState.year++; }
  pages['calendar']._renderNav();
  pages['calendar']._load();
});

document.getElementById('calTodayBtn').addEventListener('click', () => {
  const now = new Date();
  calState.year = now.getFullYear();
  calState.month = now.getMonth() + 1;
  pages['calendar']._renderNav();
  pages['calendar']._load();
});

// ── PANCHANG ─────────────────────────────────────────────────
let panchangData = null;
let panchangFmt  = '12h';

function renderAajKaPanchang(data, slots, fmt) {
  const card = document.getElementById('aajKaPanchangCard');
  if (!card) return;

  const ft = t => formatTime((t || '').slice(0, 5), fmt);
  const rk = data.rahu_kaal;
  const shubhSlots  = slots.filter(s => s.nature === 'auspicious');
  const ashubhSlots = slots.filter(s => s.nature === 'inauspicious');

  function slotRow(slot, colorClass) {
    const start = ft(slot.start_time);
    const end   = ft(slot.end_time);
    return `<div class="akp-muhurta-row ${colorClass}">
      <span class="akp-muhurta-name">${slot.name}</span>
      <span class="akp-muhurta-time">${start} – ${end}</span>
    </div>`;
  }

  card.innerHTML = `
    <div class="aaj-ka-panchang-title">Aaj Ka Muhurta</div>

    ${shubhSlots.length ? `
    <div class="akp-section-header akp-section-header--shubh">✓ Shubh Muhurta (Choghadiya)</div>
    ${shubhSlots.map(s => slotRow(s, 'akp-shubh')).join('')}` : `
    <div class="akp-section-header">Choghadiya</div>
    <div class="akp-muhurta-row"><span class="akp-muhurta-name" style="color:var(--text-muted)">No auspicious slots today</span></div>`}

    <div class="akp-section-header akp-section-header--ashubh">✗ Ashubh Timings</div>
    ${rk ? `<div class="akp-muhurta-row akp-ashubh">
      <span class="akp-muhurta-name">Rahu Kaal${rk.is_active_now ? ' <span class="akp-active-dot"></span>' : ''}</span>
      <span class="akp-muhurta-time">${ft(rk.start?.time)} – ${ft(rk.end?.time)}</span>
    </div>` : ''}
    ${ashubhSlots.length ? ashubhSlots.map(s => slotRow(s, 'akp-ashubh')).join('') : ''}
  `;
}

registerPage('panchang', {
  onEnter(params) {
    panchangFmt = getState().timeFormat || '12h';
    const date = params.date || todayStr();
    this.currentDate = date;
    this._updateToggleUI();

    const labelDate = new Date(date + 'T12:00:00');
    const labelEl = document.getElementById('panchangDateLabel');
    if (labelEl) {
      labelEl.textContent = labelDate.toLocaleDateString('en-IN', {
        weekday: 'short', day: 'numeric', month: 'short', year: 'numeric'
      });
    }

    const moonEl   = document.getElementById('panchangMoon');
    const gregEl   = document.getElementById('panchangGregorianDate');
    const detailEl = document.getElementById('panchangBannerDetails');
    gregEl.textContent   = '—';
    detailEl.textContent = '—';

    const content = document.getElementById('panchangContent');
    content.innerHTML = '<div class="loading-spinner">Calculating...</div>';

    const state = getState();
    if (!state.lat || !state.lon) {
      content.innerHTML = '<div class="error-msg">Set a location to calculate the Panchang.</div>';
      return;
    }

    apiFetch('/generate-panchang', 'POST', {
      date, lat: state.lat, lon: state.lon, ayanamsa: state.ayanamsa || 'Lahiri'
    }).then(data => {
      panchangData = data;
      renderDateBanner(moonEl, gregEl, detailEl, data);
      this._render(data);
      apiFetch('/choghadiya', 'POST', { date, lat: state.lat, lon: state.lon })
        .then(chog => renderAajKaPanchang(data, chog.slots, panchangFmt))
        .catch(() => renderAajKaPanchang(data, [], panchangFmt));
    }).catch(e => {
      content.innerHTML = `<div class="error-msg">${e.message}</div>`;
    });
  },

  _updateToggleUI() {
    document.querySelectorAll('[data-fmt]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.fmt === panchangFmt);
    });
  },

  _render(data) {
    const fmt = panchangFmt;
    const ev  = data.events || {};
    const p   = data.panchang || {};
    const content = document.getElementById('panchangContent');

    const ft = t => formatTime(t?.slice(0,5), fmt);

    const sunrise = ev.sunrise?.time ? ft(ev.sunrise.time) : '—';
    const sunset = ev.sunset?.time ? ft(ev.sunset.time) : '—';

    const rows = [
      ...tithiRows(p.tithi, data.date, ft).map(r => ({ ...r, label: r.label === 'Tithi' ? 'Hindu Tithi' : r.label })),
      { label: 'Nakshatra', value: `${p.nakshatra?.name || '—'} (Pada ${p.nakshatra?.pada || '—'})`, sub: p.nakshatra?.ends?.time ? `upto ${ft(p.nakshatra.ends.time)}` : '' },
      { label: 'Yoga', value: p.yoga?.name || '—', sub: '' },
      { label: 'Karana', value: p.karana?.name || '—', sub: '' },
      { label: 'Weekday', value: p.vara?.name || '—', sub: '' },
      { label: 'Moon Rashi', value: p.moon_rashi || '—', sub: '' },
      { label: 'Sun Rashi', value: p.sun_rashi || '—', sub: '' },
    ];

    const pk = data.panchak_kaal;
    if (pk) {
      const pkLabel = pk.has_window
        ? pk.windows.map(w => `${ft(w.start?.time)} – ${ft(w.end?.time)}`).join(', ')
        : (pk.next_period?.entry?.time ? `Next: ${ft(pk.next_period.entry.time)}` : 'None today');
      rows.push({ label: 'Panchak Kaal', value: pkLabel, sub: '', _panchak: true });
    }

    content.innerHTML = `
      <div class="panchang-card">
        <div class="panchang-sun-moon">
          <div class="sun-moon-cell">
            <div class="sun-moon-label">Sunrise</div>
            <div class="sun-moon-time">${sunrise}</div>
          </div>
          <div class="sun-moon-cell">
            <div class="sun-moon-label">Sunset</div>
            <div class="sun-moon-time">${sunset}</div>
          </div>
        </div>
        <div class="panchang-sun-moon" style="border-bottom:1px solid var(--gold-dark)">
          <div class="sun-moon-cell">
            <div class="sun-moon-label">Moonrise</div>
            <div class="sun-moon-time">${ft(ev.moonrise?.time)}</div>
          </div>
          <div class="sun-moon-cell">
            <div class="sun-moon-label">Moonset</div>
            <div class="sun-moon-time">${ft(ev.moonset?.time)}</div>
          </div>
        </div>
        ${rows.map(r => `
          <div class="panchang-row${r._panchak ? ' panchak-table-row' : ''}" ${r._panchak ? 'data-panchak-row="1"' : ''}>
            <div class="panchang-label">${r.label}</div>
            <div class="panchang-value">
              ${r.value || '—'}
              ${r.sub ? `<br><span class="panchang-endtime">${r.sub}</span>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
      ${(() => {
        const rk = data.rahu_kaal;
        if (!rk) return '';
        const startTime = (rk.start?.time || '').slice(0, 5);
        const endTime   = (rk.end?.time   || '').slice(0, 5);
        const badge = rk.is_active_now
          ? '<span class="rahu-badge rahu-badge--active">Active now</span>'
          : '<span class="rahu-badge rahu-badge--inactive">Not active</span>';
        return `
          <div class="panchang-card rahu-kaal-card">
            <div class="rahu-kaal-title">Rahu Kaal</div>
            <div class="panchang-row">
              <div class="panchang-label">Time</div>
              <div class="panchang-value">${startTime} – ${endTime} ${badge}</div>
            </div>
            <div class="panchang-row">
              <div class="panchang-label">Duration</div>
              <div class="panchang-value">${rk.duration_minutes} min</div>
            </div>
            <div class="rahu-kaal-note">Avoid important activities during this period.</div>
          </div>`;
      })()}
      <div id="aajKaPanchangCard" class="aaj-ka-panchang-card">
        <div class="aaj-ka-panchang-title">Aaj Ka Panchang</div>
        <div class="aaj-ka-panchang-loading">Loading Choghadiya…</div>
      </div>
      ${(() => {
        const bk = data.bhadra_kaal;
        if (!bk) return '';
        let segmentsHTML = '';
        if (bk.has_windows) {
          segmentsHTML = bk.windows.map(w => {
            const startTime = (w.start?.time || '').slice(0, 5);
            const endTime   = (w.end?.time   || '').slice(0, 5);
            const activeBadge = w.is_active
              ? '<span class="bhadra-badge bhadra-badge--active">Active now</span>'
              : '';
            const riskClass = w.risk_level === 'High' ? 'bhadra-badge--risk-high' : 'bhadra-badge--risk-low';
            const riskBadge = `<span class="bhadra-badge ${riskClass}">${w.risk_level} Risk</span>`;
            return `
              <div class="bhadra-segment" style="border-top: 1px solid rgba(140, 90, 42, 0.08); padding: 10px 0;">
                <div class="panchang-row" style="padding: 4px 0; border: none;">
                  <div class="panchang-label" style="min-width: 90px; color: var(--brand-dark);">Time</div>
                  <div class="panchang-value">${startTime} – ${endTime} ${activeBadge}</div>
                </div>
                <div class="panchang-row" style="padding: 4px 0; border: none;">
                  <div class="panchang-label" style="min-width: 90px; color: var(--brand-dark);">Moon Rashi</div>
                  <div class="panchang-value">${w.moon_rashi}</div>
                </div>
                <div class="panchang-row" style="padding: 4px 0; border: none;">
                  <div class="panchang-label" style="min-width: 90px; color: var(--brand-dark);">Residence</div>
                  <div class="panchang-value">${w.residence} ${riskBadge}</div>
                </div>
              </div>
            `;
          }).join('');
        } else {
          segmentsHTML = `
            <div class="panchang-row" style="padding: 6px 0; border: none;">
              <div class="panchang-value" style="color: var(--text-muted);">No Bhadra Kaal active today.</div>
            </div>
          `;
        }
        const cardTitle = 'Bhadra Kaal (भद्रा काल)';
        const cardClass = bk.has_windows ? 'bhadra-kaal-card' : 'bhadra-kaal-card bhadra-kaal-card--inactive';
        return `
          <div class="panchang-card ${cardClass}" style="padding: 18px; margin-top: 16px;">
            <div class="bhadra-kaal-title">${cardTitle}</div>
            ${segmentsHTML}
            <div class="rahu-kaal-note" style="margin-top: 8px;">
              ${bk.has_windows ? 'Avoid starting new auspicious works during Bhadra.' : 'Auspicious day: No Bhadra effects.'}
            </div>
          </div>
        `;
      })()}
      ${(() => {
        const pk = data.panchak_kaal;
        if (!pk) return '';
        let segmentsHTML = '';
        if (pk.has_window) {
          segmentsHTML = pk.windows.map(w => {
            const startTime = (w.start?.time || '').slice(0, 5);
            const endTime   = (w.end?.time   || '').slice(0, 5);
            const activeBadge = w.is_active
              ? '<span class="panchak-badge panchak-badge--active">Active now</span>'
              : '';
            return `
              <div class="panchak-segment" style="border-top: 1px solid rgba(93, 78, 117, 0.1); padding: 10px 0;">
                <div class="panchang-row" style="padding: 4px 0; border: none;">
                  <div class="panchang-label" style="min-width: 90px; color: #5d4e75;">Time</div>
                  <div class="panchang-value">${startTime} – ${endTime} ${activeBadge}</div>
                </div>
                <div class="panchang-row" style="padding: 4px 0; border: none;">
                  <div class="panchang-label" style="min-width: 90px; color: #5d4e75;">Nakshatra</div>
                  <div class="panchang-value">${w.nakshatra || '—'}</div>
                </div>
              </div>
            `;
          }).join('');
        } else {
          const nextEntry = pk.next_period?.entry?.time;
          const nextExit  = pk.next_period?.exit?.time;
          const nextStr   = nextEntry ? `${nextEntry.slice(0,5)} – ${(nextExit||'').slice(0,5)}` : '';
          segmentsHTML = `
            <div class="panchang-row" style="padding: 6px 0; border: none;">
              <div class="panchang-value" style="color: var(--text-muted);">No Panchak today.</div>
            </div>
            ${nextStr ? `<div class="panchang-row" style="padding: 4px 0; border: none;">
              <div class="panchang-label" style="min-width: 90px; color: #5d4e75;">Next Period</div>
              <div class="panchang-value" style="color: var(--text-muted);">${nextStr}</div>
            </div>` : ''}
          `;
        }
        const cardClass = pk.has_window ? 'panchak-kaal-card' : 'panchak-kaal-card panchak-kaal-card--inactive';
        return `
          <div class="panchang-card ${cardClass}" style="padding: 18px; margin-top: 16px;">
            <div class="panchak-kaal-title">Panchak Kaal (पंचक काल)</div>
            ${segmentsHTML}
            <div class="rahu-kaal-note" style="margin-top: 8px;">
              ${pk.has_window ? 'Avoid starting important works during Panchak.' : 'No Panchak active today.'}
            </div>
          </div>
        `;
      })()}
    `;

    const pkRow = content.querySelector('[data-panchak-row]');
    if (pkRow) {
      pkRow.style.cursor = 'pointer';
      pkRow.addEventListener('click', () => navigate('panchak', { date: data.date }));
    }
  }
});

// Panchang time format toggle
document.querySelectorAll('[data-fmt]').forEach(btn => {
  btn.addEventListener('click', () => {
    panchangFmt = btn.dataset.fmt;
    saveState({ timeFormat: panchangFmt });
    pages['panchang']._updateToggleUI();
    if (panchangData) {
      pages['panchang']._render(panchangData);
      const card = document.getElementById('aajKaPanchangCard');
      if (card && !card.querySelector('.aaj-ka-panchang-loading')) {
        const state = getState();
        apiFetch('/choghadiya', 'POST', { date: panchangData.date, lat: state.lat, lon: state.lon })
          .then(chog => renderAajKaPanchang(panchangData, chog.slots, panchangFmt))
          .catch(() => renderAajKaPanchang(panchangData, [], panchangFmt));
      }
    }
  });
});

document.getElementById('panchangBack').addEventListener('click', () => history.back());

function shiftDateStr(dateStr, offset) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(y, m - 1, d + offset);
  return `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,'0')}-${String(dt.getDate()).padStart(2,'0')}`;
}

document.getElementById('panchangPrev').addEventListener('click', () => {
  const ctrl = pages['panchang'];
  if (ctrl.currentDate) {
    navigate('panchang', { date: shiftDateStr(ctrl.currentDate, -1) });
  }
});

document.getElementById('panchangNext').addEventListener('click', () => {
  const ctrl = pages['panchang'];
  if (ctrl.currentDate) {
    navigate('panchang', { date: shiftDateStr(ctrl.currentDate, 1) });
  }
});

// ── MUHURTA ──────────────────────────────────────────────────
registerPage('muhurta', { onEnter() {} });

['horaCard','lagnaCard','chandraCard','taraCard'].forEach(id => {
  document.getElementById(id)?.addEventListener('click', () => {
    alert('Coming soon');
  });
});

// ── CHOGHADIYA ───────────────────────────────────────────────
const chogState = {
  date: todayStr(),
  fmt: '12h',
  slots: [],
  sunrise: '',
  sunset: '',
  timerInterval: null,
};

function chogDateFromOffset(baseDate, offset) {
  const [y, m, d] = baseDate.split('-').map(Number);
  const dt = new Date(y, m - 1, d + offset);
  return `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,'0')}-${String(dt.getDate()).padStart(2,'0')}`;
}

function chogWeekStart(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  const day = dt.getDay(); // 0=Sun
  const start = new Date(dt);
  start.setDate(d - day);
  return start;
}

function renderWeekdayTabs(currentDate) {
  const tabs = document.getElementById('weekdayTabs');
  const weekStart = chogWeekStart(currentDate);
  const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  tabs.innerHTML = '';
  for (let i = 0; i < 7; i++) {
    const dt = new Date(weekStart);
    dt.setDate(weekStart.getDate() + i);
    const ds = `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,'0')}-${String(dt.getDate()).padStart(2,'0')}`;
    const btn = document.createElement('button');
    btn.className = 'weekday-tab' + (ds === currentDate ? ' active' : '');
    btn.textContent = DAYS[i];
    btn.addEventListener('click', () => {
      chogState.date = ds;
      loadChoghadiya();
    });
    tabs.appendChild(btn);
  }
}

function parseTimeToday(timeStr, dateStr) {
  if (!timeStr) return null;
  const [y, m, d] = dateStr.split('-').map(Number);
  const [h, min]  = timeStr.split(':').map(Number);
  return new Date(y, m - 1, d, h, min, 0).getTime();
}

function parseSlotTime(slot, field, fallbackDate) {
  const local = slot[`${field}_local`];
  if (local) return new Date(local).getTime();
  return parseTimeToday(slot[`${field}_time`], fallbackDate);
}

function findCurrentSlot(slots, dateStr) {
  const now = Date.now();
  return slots.find(s => {
    const start = parseSlotTime(s, 'start', dateStr);
    const end = parseSlotTime(s, 'end', dateStr);
    return start !== null && end !== null && now >= start && now < end;
  }) || null;
}

function startCountdown(slot, dateStr) {
  if (chogState.timerInterval) clearInterval(chogState.timerInterval);
  if (!slot) {
  document.getElementById('chogCountdown').textContent = '--:--:--';
    return;
  }

  const endMs = parseSlotTime(slot, 'end', dateStr);

  function tick() {
    const remaining = Math.max(0, endMs - Date.now());
    const h = Math.floor(remaining / 3_600_000);
    const m = Math.floor((remaining % 3_600_000) / 60_000);
    const s = Math.floor((remaining % 60_000) / 1_000);
    document.getElementById('chogCountdown').textContent =
      `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;

    if (remaining === 0) {
      clearInterval(chogState.timerInterval);
      loadChoghadiya(); // refresh when slot ends
    }
  }

  tick();
  chogState.timerInterval = setInterval(tick, 1000);
}

function chogFormatTime(t, fmt) {
  if (!t) return '—';
  if (fmt === '24plus') {
    const [h, m] = t.split(':').map(Number);
    if (h < 6) return `${String(h + 24).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
  }
  return formatTime(t, fmt);
}

function chogDateSuffix(localIso, baseDate) {
  if (!localIso || localIso.slice(0, 10) === baseDate) return '';
  const label = new Date(localIso).toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short',
  });
  return `, ${label}`;
}

function chogSlotDisplayTime(slot, field, fmt, baseDate) {
  const label = slot[`${field}_label`];
  if (fmt === '12h' && label) return label;
  return `${chogFormatTime(slot[`${field}_time`], fmt)}${chogDateSuffix(slot[`${field}_local`], baseDate)}`;
}

function renderChoghadiya(data) {
  const { slots, sunrise, sunset, date } = data;
  chogState.slots   = slots;
  chogState.sunrise = sunrise;
  chogState.sunset  = sunset;

  const fmt = chogState.fmt;

  // Date label
  document.getElementById('chogDateLabel').textContent = formatDateLabel(date);

  // Banner date
  document.getElementById('chogBannerDate').textContent = formatDateLabel(date);

  // Weekday tabs
  renderWeekdayTabs(date);

  // Current slot
  const current = findCurrentSlot(slots, date);
  if (current) {
    document.getElementById('chogCurrentTime').textContent =
      `${chogSlotDisplayTime(current, 'start', fmt, date)} – ${chogSlotDisplayTime(current, 'end', fmt, date)}`;
    document.getElementById('chogCurrentName').textContent = current.name;
    document.getElementById('chogCurrentQuality').textContent = chogQualityLabel(current.nature);
    const bannerRight = document.getElementById('chogCurrentSlot');
    bannerRight.style.background = current.nature === 'auspicious' ? 'var(--green-slot)'
                                 : current.nature === 'inauspicious' ? 'var(--red-slot)'
                                 : 'var(--gray-slot)';
    startCountdown(current, date);
  } else {
    document.getElementById('chogCurrentTime').textContent = 'No active slot';
    document.getElementById('chogCurrentName').textContent = '—';
    document.getElementById('chogCurrentQuality').textContent = '—';
    startCountdown(null, date);
  }

  // Render slot rows
  const daySlots   = slots.filter(s => s.period === 'day');
  const nightSlots = slots.filter(s => s.period === 'night');

  function makeSlotHTML(slot) {
    const isCurrent = current && slot.start_time === current.start_time && slot.period === current.period;
    const icon = '';
    const startText = chogSlotDisplayTime(slot, 'start', fmt, date);
    const endText = chogSlotDisplayTime(slot, 'end', fmt, date);
    return `
      <div class="chog-slot ${slot.nature}${isCurrent ? ' current' : ''}">
        <div class="chog-slot-name">
          <div class="chog-slot-name-text">
            ${slot.name}
            <small>${slot.meaning}</small>
          </div>
          <span></span>
        </div>
        <div class="chog-slot-time">
          <span>${startText} to ${endText}</span>
          <span class="chog-slot-icon">${icon}</span>
        </div>
      </div>
    `;
  }

  const ft = t => chogFormatTime(t, fmt);
  const content = document.getElementById('chogContent');
  content.innerHTML = `
    <div class="chog-section-header">
      Day
      <span>Sunrise - ${ft(sunrise)}</span>
    </div>
    ${daySlots.map(makeSlotHTML).join('')}
    <div class="chog-section-header">
      Night
      <span>Sunset - ${ft(sunset)}</span>
    </div>
    ${nightSlots.map(makeSlotHTML).join('')}
  `;
}

async function loadChoghadiya() {
  const state = getState();
  const content = document.getElementById('chogContent');
  content.innerHTML = '<div class="loading-spinner">Calculating...</div>';

  document.getElementById('chogDateLabel').textContent = formatDateLabel(chogState.date);
  renderWeekdayTabs(chogState.date);

  if (!state.lat || !state.lon) {
    content.innerHTML = '<div class="error-msg">Set a location to calculate Choghadiya.</div>';
    return;
  }

  try {
    const data = await apiFetch('/choghadiya', 'POST', {
      date: chogState.date, lat: state.lat, lon: state.lon
    });
    renderChoghadiya({ ...data, date: chogState.date });
  } catch (e) {
    content.innerHTML = `<div class="error-msg">${e.message}</div>`;
  }
}

registerPage('choghadiya', {
  onEnter(params) {
    chogState.date = params.date || todayStr();
    chogState.fmt  = getState().timeFormat || '12h';
    this._updateToggleUI();
    loadChoghadiya();
  },

  onLeave() {
    if (chogState.timerInterval) clearInterval(chogState.timerInterval);
  },

  _updateToggleUI() {
    document.querySelectorAll('[data-chog-fmt]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.chogFmt === chogState.fmt);
    });
  }
});

document.querySelectorAll('[data-chog-fmt]').forEach(btn => {
  btn.addEventListener('click', () => {
    chogState.fmt = btn.dataset.chogFmt;
    pages['choghadiya']._updateToggleUI();
    if (chogState.slots.length) {
      renderChoghadiya({ slots: chogState.slots, sunrise: chogState.sunrise, sunset: chogState.sunset, date: chogState.date });
    }
  });
});

document.getElementById('chogPrev').addEventListener('click', () => {
  chogState.date = chogDateFromOffset(chogState.date, -1);
  loadChoghadiya();
});
document.getElementById('chogNext').addEventListener('click', () => {
  chogState.date = chogDateFromOffset(chogState.date, 1);
  loadChoghadiya();
});

// ── PANCHAK ──────────────────────────────────────────────────
const panchakState = { date: todayStr() };

function renderPanchakDateTabs(currentDate) {
  const tabs = document.getElementById('panchakDateTabs');
  tabs.innerHTML = '';
  for (let offset = -3; offset <= 3; offset++) {
    const ds = chogDateFromOffset(currentDate, offset);
    const dt = new Date(ds + 'T00:00:00');
    const label = dt.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric' });
    const btn = document.createElement('button');
    btn.className = 'weekday-tab' + (ds === currentDate ? ' active' : '');
    btn.textContent = label;
    btn.style.cssText = 'font-size:11px; padding:4px 8px; white-space:nowrap;';
    btn.addEventListener('click', () => {
      panchakState.date = ds;
      loadPanchak();
    });
    tabs.appendChild(btn);
  }
}

function renderPanchak(pk) {
  const content = document.getElementById('panchakContent');
  if (!pk) {
    content.innerHTML = '<div class="error-msg">Panchak data unavailable.</div>';
    return;
  }

  const ft = t => (t || '').slice(0, 5);

  let bodyHTML = '';
  if (pk.has_window) {
    const windowsHTML = pk.windows.map(w => {
      const startT = ft(w.start?.time);
      const endT   = ft(w.end?.time);
      const activeBadge = w.is_active
        ? '<span class="panchak-badge panchak-badge--active">Active now</span>'
        : '';
      const clippedNote = [
        w.clipped_start ? 'started before sunrise' : '',
        w.clipped_end   ? 'continues past midnight' : '',
      ].filter(Boolean).join(', ');
      return `
        <div class="panchak-window-card">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
            <span style="font-weight:700; color:#5d4e75; font-size:15px;">${startT} – ${endT}</span>
            ${activeBadge}
          </div>
          <div class="panchang-row" style="border:none; padding:3px 0;">
            <div class="panchang-label" style="color:#5d4e75;">Nakshatra</div>
            <div class="panchang-value">${w.nakshatra || '—'}</div>
          </div>
          ${clippedNote ? `<div style="font-size:11px; color:var(--text-muted); margin-top:4px;">(${clippedNote})</div>` : ''}
        </div>`;
    }).join('');

    const periodEntry = ft(pk.period?.entry?.time);
    const periodExit  = ft(pk.period?.exit?.time);
    bodyHTML = `
      <div style="padding: 0 16px;">
        <div style="text-align:center; margin-bottom:12px;">
          <span class="panchak-badge panchak-badge--active" style="font-size:12px; padding:4px 12px;">Panchak Active</span>
        </div>
        ${windowsHTML}
        ${periodEntry ? `
          <div class="panchak-window-card" style="background:rgba(93,78,117,0.06);">
            <div style="font-size:11px; color:var(--text-muted); margin-bottom:4px;">Full Panchak Period</div>
            <div style="font-weight:600; color:#5d4e75;">${periodEntry} – ${periodExit}</div>
          </div>` : ''}
      </div>`;
  } else {
    const nextEntry = ft(pk.next_period?.entry?.time);
    const nextExit  = ft(pk.next_period?.exit?.time);
    bodyHTML = `
      <div style="padding: 0 16px;">
        <div style="text-align:center; margin-bottom:16px;">
          <span class="panchak-badge panchak-badge--inactive" style="font-size:12px; padding:4px 12px;">No Panchak Today</span>
        </div>
        ${nextEntry ? `
          <div class="panchak-window-card" style="background:rgba(235,247,241,0.95);">
            <div style="font-size:11px; color:var(--text-muted); margin-bottom:4px;">Next Panchak Period</div>
            <div style="font-weight:600; color:var(--green);">${nextEntry} – ${nextExit}</div>
          </div>` : ''}
      </div>`;
  }

  const infoId = 'panchakInfoBody_' + panchakState.date.replace(/-/g, '');
  content.innerHTML = `
    ${bodyHTML}
    <div style="padding: 0 16px 16px;">
      <div class="panchak-info-toggle" id="${infoId}_toggle" onclick="
        var b = document.getElementById('${infoId}');
        b.style.display = b.style.display === 'none' ? 'block' : 'none';
        this.textContent = b.style.display === 'none' ? '▶ What is Panchak?' : '▼ What is Panchak?';
      ">▶ What is Panchak?</div>
      <div id="${infoId}" class="panchak-info-body" style="display:none;">
        Panchak (पंचक) is a ~5-day period when the Moon transits through the last five nakshatras:
        <strong>Dhanishta, Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada,</strong> and <strong>Revati</strong>
        (Moon sidereal longitude 300°–360°). Traditionally, some families avoid activities like
        starting construction, collecting wood, travel southward, or major ceremonies during this period.
        Practices vary across traditions and regions.
      </div>
    </div>
  `;
}

async function loadPanchak() {
  const state = getState();
  const content = document.getElementById('panchakContent');
  content.innerHTML = '<div class="loading-spinner">Calculating…</div>';
  renderPanchakDateTabs(panchakState.date);

  if (!state.lat || !state.lon) {
    content.innerHTML = '<div class="error-msg">Set a location to calculate Panchak.</div>';
    return;
  }

  try {
    const data = await apiFetch('/generate-panchang', 'POST', {
      date: panchakState.date, lat: state.lat, lon: state.lon, ayanamsa: state.ayanamsa || 'Lahiri'
    });
    renderPanchak(data.panchak_kaal);
  } catch (e) {
    content.innerHTML = `<div class="error-msg">${e.message}</div>`;
  }
}

registerPage('panchak', {
  onEnter(params) {
    panchakState.date = params.date || todayStr();
    loadPanchak();
  }
});

document.getElementById('panchakBack').addEventListener('click', () => history.back());
document.getElementById('panchakPrev').addEventListener('click', () => {
  panchakState.date = chogDateFromOffset(panchakState.date, -1);
  loadPanchak();
});
document.getElementById('panchakNext').addEventListener('click', () => {
  panchakState.date = chogDateFromOffset(panchakState.date, 1);
  loadPanchak();
});
document.getElementById('panchakCard')?.addEventListener('click', () => navigate('panchak'));

// ── LOCATION ─────────────────────────────────────────────────
registerPage('location', {
  onEnter() {
    const state = getState();
    const nameEl = document.getElementById('locationCurrentName');
    nameEl.textContent = state.locationName || 'No location set';
    if (state.lat) {
      document.getElementById('latInput').value = state.lat;
      document.getElementById('lonInput').value = state.lon;
      document.getElementById('locationNameInput').value = state.locationName || '';
    }
    document.getElementById('locationError').classList.add('hidden');
  }
});

// Location search autocomplete
let searchTimer = null;
document.getElementById('locationSearch').addEventListener('input', function() {
  const q = this.value.trim();
  clearTimeout(searchTimer);
  const results = document.getElementById('locationResults');
  if (!q) { results.classList.add('hidden'); return; }

  searchTimer = setTimeout(async () => {
    try {
      const data = await apiFetch(`/search-location?q=${encodeURIComponent(q)}`);
      results.innerHTML = '';
      if (!data.results?.length) {
        results.innerHTML = '<div class="search-result-item">No results</div>';
      } else {
        data.results.forEach(r => {
          const item = document.createElement('div');
          item.className = 'search-result-item';
          item.textContent = r.display_name;
          item.addEventListener('click', () => {
            document.getElementById('latInput').value = r.lat;
            document.getElementById('lonInput').value = r.lon;
            document.getElementById('locationNameInput').value = r.display_name;
            document.getElementById('locationSearch').value = r.display_name;
            results.classList.add('hidden');
          });
          results.appendChild(item);
        });
      }
      results.classList.remove('hidden');
    } catch { results.classList.add('hidden'); }
  }, 350);
});

document.addEventListener('click', e => {
  if (!e.target.closest('.search-box')) {
    document.getElementById('locationResults').classList.add('hidden');
  }
});

document.getElementById('locationSaveBtn').addEventListener('click', () => {
  const lat  = parseFloat(document.getElementById('latInput').value);
  const lon  = parseFloat(document.getElementById('lonInput').value);
  const name = document.getElementById('locationNameInput').value.trim();
  const errEl = document.getElementById('locationError');

  if (isNaN(lat) || isNaN(lon)) {
    errEl.textContent = 'Please enter valid latitude and longitude.';
    errEl.classList.remove('hidden');
    return;
  }
  if (lat < -90 || lat > 90) {
    errEl.textContent = 'Latitude must be between -90 and 90.';
    errEl.classList.remove('hidden');
    return;
  }
  if (lon < -180 || lon > 180) {
    errEl.textContent = 'Longitude must be between -180 and 180.';
    errEl.classList.remove('hidden');
    return;
  }
  errEl.classList.add('hidden');

  saveState({ lat, lon, locationName: name || `${lat.toFixed(4)}, ${lon.toFixed(4)}` });
  navigate('home');
});

document.getElementById('locationBack').addEventListener('click', () => history.back());

// ── SETTINGS ─────────────────────────────────────────────────
registerPage('settings', {
  onEnter() {
    const state = getState();

    // Language toggle
    document.querySelectorAll('[data-lang]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === (state.lang || 'en'));
    });

    // Time format toggle
    document.querySelectorAll('[data-timefmt]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.timefmt === (state.timeFormat || '12h'));
    });

    // Ayanamsa
    const sel = document.getElementById('ayanamsaSelect');
    sel.value = state.ayanamsa || 'Lahiri';
  }
});

document.querySelectorAll('[data-lang]').forEach(btn => {
  btn.addEventListener('click', () => {
    saveState({ lang: btn.dataset.lang });
    document.querySelectorAll('[data-lang]').forEach(b => b.classList.toggle('active', b === btn));
  });
});

document.querySelectorAll('[data-timefmt]').forEach(btn => {
  btn.addEventListener('click', () => {
    saveState({ timeFormat: btn.dataset.timefmt });
    document.querySelectorAll('[data-timefmt]').forEach(b => b.classList.toggle('active', b === btn));
  });
});

document.getElementById('ayanamsaSelect').addEventListener('change', function() {
  saveState({ ayanamsa: this.value });
});

// PDF Export
document.getElementById('pdfExportBtn').addEventListener('click', async () => {
  const state = getState();
  const year  = parseInt(document.getElementById('pdfYear').value, 10);
  const result = document.getElementById('pdfResult');
  result.innerHTML = 'Generating…';
  result.classList.add('visible');

  if (!state.lat || !state.lon) {
    result.innerHTML = 'Please set a location first.';
    return;
  }

  try {
    const data = await apiFetch('/generate-pdf-panchang', 'POST', {
      year, lat: state.lat, lon: state.lon, ayanamsa: state.ayanamsa || 'Lahiri'
    });
    result.innerHTML = `<a href="${data.file.download_url}" target="_blank">⬇ Download ${data.file.name}</a>`;
  } catch (e) {
    result.innerHTML = `Error: ${e.message}`;
  }
});

// Range Export
document.getElementById('rangeExportBtn').addEventListener('click', async () => {
  const state  = getState();
  const start  = parseInt(document.getElementById('rangeStart').value, 10);
  const end    = parseInt(document.getElementById('rangeEnd').value, 10);
  const format = document.getElementById('rangeFormat').value;
  const result = document.getElementById('rangeResult');
  result.innerHTML = 'Generating…';
  result.classList.add('visible');

  if (!state.lat || !state.lon) {
    result.innerHTML = 'Please set a location first.';
    return;
  }

  try {
    const data = await apiFetch('/generate-range-panchang', 'POST', {
      start_year: start, end_year: end,
      lat: state.lat, lon: state.lon,
      ayanamsa: state.ayanamsa || 'Lahiri',
      format, monthly: false
    });
    result.innerHTML = data.files.map(f =>
      `<a href="${f.download_url}" target="_blank">⬇ ${f.name}</a>`
    ).join('<br>');
  } catch (e) {
    result.innerHTML = `Error: ${e.message}`;
  }
});

// ── JAIN FESTIVALS ───────────────────────────────────────────
const festState = {
  year: new Date().getFullYear(),
  profile: getState().jainProfile || 'shwetambar_murtipujak_tapagachchha',
  view: 'calendar', // 'calendar' | 'list'
  filter: 'all', // 'all' | 'kalyanak' | 'festival' | 'fast' | 'parva' | 'review'
  selectedSource: 'all',
  searchQuery: '',
  festivals: [],
  upcoming: [],
};

// Initialize elements
const profileSelect = document.getElementById('festProfileSelect');
if (profileSelect) {
  profileSelect.value = festState.profile;
  profileSelect.addEventListener('change', (e) => {
    festState.profile = e.target.value;
    saveState({ jainProfile: festState.profile });
    loadJainFestivals();
  });
}

const sourceSelect = document.getElementById('festSourceSelect');
if (sourceSelect) {
  sourceSelect.value = festState.selectedSource;
  sourceSelect.addEventListener('change', (e) => {
    festState.selectedSource = e.target.value;
    renderJainFestivalsView();
  });
}

document.getElementById('festPrev')?.addEventListener('click', () => {
  festState.year--;
  document.getElementById('festYearLabel').textContent = festState.year;
  loadJainFestivals();
});

document.getElementById('festNext')?.addEventListener('click', () => {
  festState.year++;
  document.getElementById('festYearLabel').textContent = festState.year;
  loadJainFestivals();
});

// Toggle grid / list view
document.querySelectorAll('#festViewToggle button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#festViewToggle button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    festState.view = btn.dataset.view;
    renderJainFestivalsView();
  });
});

// Search input
document.getElementById('festSearchInput')?.addEventListener('input', (e) => {
  festState.searchQuery = e.target.value.toLowerCase().trim();
  renderJainFestivalsView();
});

// Filter chips
document.querySelectorAll('#festFilterChips button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#festFilterChips button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    festState.filter = btn.dataset.filter;
    renderJainFestivalsView();
  });
});

// Export toggle
const exportBtn = document.getElementById('festExportBtn');
const exportDrawer = document.getElementById('festExportDrawer');
exportBtn?.addEventListener('click', () => {
  exportDrawer?.classList.toggle('hidden');
});
document.getElementById('festExportDrawerClose')?.addEventListener('click', () => {
  exportDrawer?.classList.add('hidden');
});

// Export triggers
exportDrawer?.querySelectorAll('[data-expfmt]').forEach(btn => {
  btn.addEventListener('click', async () => {
    const format = btn.dataset.expfmt;
    const state = getState();
    const resultEl = document.getElementById('festExportResult');
    if (resultEl) resultEl.innerHTML = 'Generating export…';
    try {
      const res = await apiFetch('/generate-jain-festival-exports', 'POST', {
        year: festState.year,
        lat: state.lat,
        lon: state.lon,
        ayanamsa: state.ayanamsa || 'Lahiri',
        profile: festState.profile,
        source: festState.selectedSource,
        format
      });
      if (resultEl) {
        resultEl.innerHTML = res.files.map(f =>
          `<a href="${f.download_url}" target="_blank" style="color:#27AE60; font-weight:bold; text-decoration:underline;">⬇ Download ${f.name}</a>`
        ).join('<br/>');
      }
    } catch (e) {
      if (resultEl) resultEl.innerHTML = `Error: ${e.message}`;
    }
  });
});

// Details modal close
const modalOverlay = document.getElementById('festModalOverlay');
const modal = document.getElementById('festModal');
const modalClose = document.getElementById('festModalClose');

function formatJainTithiLabel(f) {
  if (!f) return '—';
  const month  = (f.jain_month && f.jain_month !== 'undefined' && f.jain_month !== 'null') ? f.jain_month : '';
  const paksha = (f.paksha && f.paksha !== 'undefined' && f.paksha !== 'null') ? f.paksha : '';
  let tithiName = '';

  if (typeof f.tithi === 'string' && f.tithi !== 'undefined' && f.tithi !== 'null') {
    tithiName = f.tithi;
  } else if (typeof f.tithi === 'number') {
    tithiName = `Tithi ${f.tithi}`;
  } else if (f.tithi && typeof f.tithi === 'object') {
    const tM = f.tithi.masa || f.tithi.month || '';
    const tP = f.tithi.paksha || '';
    const tN = f.tithi.name || f.tithi.number || f.tithi.tithi || '';
    const combined = [tM, tP, tN].filter(Boolean).join(' ');
    if (combined) return combined;
  }

  const parts = [month, paksha, tithiName].filter(Boolean);
  return parts.length ? parts.join(' ') : '—';
}

function openFestivalModal(f) {
  if (typeof f === 'string') {
    f = (festState.festivals || []).find(x => x.occurrence_id === f || x.id === f);
  }
  if (!f) return;

  const modalBody = document.getElementById('festModalBody');
  const modalTitle = document.getElementById('festModalTitle');
  if (!modalBody) return;

  if (modalTitle) modalTitle.textContent = f.name;

  const statusBadge = f.status === 'review_needed'
    ? `<span class="fest-badge fest-badge--review">⚠️ Review Needed</span>`
    : getCategoryPill(f); // Use our new pill function!

  const getDaysCount = (s, e) => {
    if (!s || !e || s === e) return 1;
    const d1 = new Date(s);
    const d2 = new Date(e);
    return Math.round((d2 - d1) / (1000 * 60 * 60 * 24)) + 1;
  };

  const rangeDisplay = f.start_date === f.end_date
    ? f.start_date
    : `${f.start_date} to ${f.end_date} <span style="font-weight:normal; font-size:12px; color:#8E44AD; margin-left:4px;">(${getDaysCount(f.start_date, f.end_date)} Days)</span>`;

  // Daily Schedule Progress Tracker
  let dailyProgressHTML = '';
  if (f.daily_schedule && f.daily_schedule.length > 0) {
    dailyProgressHTML = `
      <div class="modal-detail-row">
        <div class="modal-detail-label">Multi-Day Progress Tracker</div>
        <div class="modal-detail-value" style="display:flex; flex-direction:column; gap:6px;">
          ${f.daily_schedule.map((d, i) => `
            <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
              <input type="checkbox" style="accent-color: var(--brand);">
              <span style="font-size:13px; color: var(--text-primary);"><strong>Day ${i+1} (${d.date.slice(5)}):</strong> ${d.virtue}</span>
            </label>
          `).join('')}
        </div>
      </div>
    `;
  }

  // Tithi & Timing Breakdown
  const timingBreakdown = `
    <div class="modal-detail-row">
      <div class="modal-detail-label">Tithi & Astronomical Timing Breakdown</div>
      <div class="modal-detail-value" style="background: var(--surface-soft); padding:8px; border-radius:6px; border:1px solid var(--border); font-size:12px; color: var(--text-primary);">
        <div><strong>Tithi/Nakshatra:</strong> ${formatJainTithiLabel(f)}</div>
        <div style="margin-top:4px;"><strong>Jain Astronomical Cutoff:</strong> <span style="color: var(--accent); font-family:monospace;">t<sub>sunrise</sub> + 144 mins</span></div>
        <div style="margin-top:2px; font-size:11px; color: var(--text-secondary);">Vrats generally commence 144 minutes after local sunrise.</div>
      </div>
    </div>
  `;

  // Notification Button
  const remindBtnHTML = `
    <button class="btn-primary" style="width:100%; margin-top:16px; display:flex; align-items:center; justify-content:center; gap:8px; background: var(--brand);" onclick="alert('Notification scheduled for ${f.name.replace(/'/g, "\\'")}!')">
      🔔 Remind Me
    </button>
  `;

  modalBody.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
      <div>${statusBadge}</div>
    </div>
    
    <div class="modal-detail-row">
      <div class="modal-detail-label">Event Description & Significance</div>
      <div class="modal-detail-value" style="font-size:14px; line-height:1.4; color: var(--text-primary);">
        ${f.meaning || 'No description available.'}
      </div>
    </div>
    
    <div class="modal-detail-row">
      <div class="modal-detail-label">Date & Span</div>
      <div class="modal-detail-value" style="color: var(--text-primary);">${rangeDisplay}</div>
    </div>
    
    <div class="modal-detail-row">
      <div class="modal-detail-label">Fasting / Vrat Guidelines</div>
      <div class="modal-detail-value" style="color: var(--green); font-weight:600;">
        ${f.observance || 'Standard Vrat rules apply. (Ekasana, Upvas, Ayambil, etc.)'}
      </div>
    </div>
    
    ${timingBreakdown}
    ${dailyProgressHTML}
    ${remindBtnHTML}
  `;
  
  
  modalOverlay.classList.remove('hidden');
  modal.classList.remove('hidden');
  requestAnimationFrame(() => {
    modalOverlay.classList.add('visible');
    modal.classList.add('visible');
  });
}

function closeFestivalModal() {
  modalOverlay.classList.remove('visible');
  modal.classList.remove('visible');
  setTimeout(() => {
    modalOverlay.classList.add('hidden');
    modal.classList.add('hidden');
  }, 300);
}

modalClose?.addEventListener('click', closeFestivalModal);
modalOverlay?.addEventListener('click', closeFestivalModal);

async function loadJainFestivals() {
  const state = getState();
  const locationHeader = document.getElementById('festLocationHeader');
  if (locationHeader) {
    locationHeader.textContent = state.locationName ? `📍 ${state.locationName}` : 'No location set';
  }
  
  const grid = document.getElementById('festGrid');
  const list = document.getElementById('festList');
  const upcoming = document.getElementById('festUpcomingList');
  
  if (grid) grid.innerHTML = '<div class="cal-loading">Loading festival grid...</div>';
  if (list) list.innerHTML = '<div class="cal-loading">Loading list...</div>';
  if (upcoming) upcoming.innerHTML = '<div style="font-size:12px; color:#7F8C8D; padding:10px;">Calculating upcoming events...</div>';
  
  if (!state.lat || !state.lon) {
    if (grid) grid.innerHTML = '<div class="cal-loading">Set a location to view Jain Festivals.</div>';
    return;
  }
  
  try {
    const data = await apiFetch('/generate-jain-festivals', 'POST', {
      year: festState.year,
      lat: state.lat,
      lon: state.lon,
      ayanamsa: state.ayanamsa || 'Lahiri',
      profile: festState.profile
    });
    
    festState.festivals = data.festivals || [];
    festState.upcoming  = data.upcoming || [];
    festState.panchang_tithi_map = data.panchang_tithi_map || {};
    
    // Render upcoming
    if (upcoming) {
      upcoming.innerHTML = '';
      if (!festState.upcoming.length) {
        upcoming.innerHTML = '<div style="font-size:11px; color:#95A5A6; padding:10px;">No major events in next 30 days</div>';
      } else {
        festState.upcoming.forEach(f => {
          const card = document.createElement('div');
          card.className = 'upcoming-festival-card';
          card.innerHTML = `
            <div style="font-size:12px; font-weight:bold; color:#2C3E50; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${f.name}</div>
            <div style="font-size:10px; color:#7F8C8D;">${f.start_date}</div>
            <div><span class="fest-badge fest-badge--${f.category}" style="font-size:8px; padding:2px 4px;">${f.category}</span></div>
          `;
          card.addEventListener('click', () => openFestivalModal(f));
          upcoming.appendChild(card);
        });
      }
    }
    
    renderJainFestivalsView();
  } catch (e) {
    if (grid) grid.innerHTML = `<div class="cal-loading">Error: ${e.message}</div>`;
  }
}

function getFilteredFestivals() {
  return festState.festivals.filter(f => {
    // Search query filter
    const matchesSearch = !festState.searchQuery || 
      f.name.toLowerCase().includes(festState.searchQuery) ||
      f.meaning.toLowerCase().includes(festState.searchQuery) ||
      f.jain_month.toLowerCase().includes(festState.searchQuery);
      
    // Category filter
    let matchesFilter = true;
    if (festState.filter !== 'all') {
      const cat = f.category ? f.category.toLowerCase() : '';
      const name = f.name ? f.name.toLowerCase() : '';
      if (festState.filter === 'vrats') {
        matchesFilter = (cat === 'fast' || cat === 'parva' || cat === 'mahaparv' || name.includes('vrat')) && !name.includes('parva tithi') && !name.includes('pakhi');
      } else if (festState.filter === 'kalyanaks') {
        matchesFilter = cat === 'kalyanak' || name.includes('kalyanak');
      } else if (festState.filter === 'parva') {
        matchesFilter = cat === 'parva_tithi' || name.includes('parva tithi') || name.includes('pakhi');
      } else if (festState.filter === 'review') {
        matchesFilter = f.status === 'review_needed';
      }
    }
    
    // School / Source filter
    let matchesSource = true;
    if (festState.selectedSource && festState.selectedSource !== 'all') {
      const sourceQuery = festState.selectedSource.toLowerCase();
      const sourcesList = f.sources || [];
      const hasSelectedSource = sourcesList.some(s => s.toLowerCase().includes(sourceQuery));
      
      const specificSchools = ["vrindavan", "uttarapurana", "ashadhara"];
      const hasOtherSpecificSchool = sourcesList.some(s => {
        const val = s.toLowerCase();
        return specificSchools.some(sch => sch !== sourceQuery && val.includes(sch));
      });
      
      matchesSource = hasSelectedSource || !hasOtherSpecificSchool;
    }
    
    return matchesSearch && matchesFilter && matchesSource;
  });
}

function renderJainFestivalsView() {
  const filtered = getFilteredFestivals();
  
  if (festState.view === 'calendar') {
    document.getElementById('festCalendarContainer').classList.remove('hidden');
    document.getElementById('festListContainer').classList.add('hidden');
    renderJainGrid(filtered);
  } else {
    document.getElementById('festCalendarContainer').classList.add('hidden');
    document.getElementById('festListContainer').classList.remove('hidden');
    renderJainList(filtered);
  }
}

function renderJainGrid(filteredList) {
  const grid = document.getElementById('festGrid');
  if (!grid) return;
  grid.innerHTML = '';
  
  // We can render a monthly grid for a selected month, or since we are showing the whole year,
  // let's show a month picker in Year Controls, or show a simple summary grid!
  // Wait, let's render a month selection dropdown dynamically so the calendar view is highly functional!
  // Let's add a month picker dropdown to the Year Controls if not already there, or we can just render the current month!
  // Let's check which month to render: let's default to the current month or March/April where festivals commonly reside.
  // Actually, we can add a month selector select inside our JS code dynamically!
  let monthSelector = document.getElementById('festMonthSelect');
  if (!monthSelector) {
    // Add month selector dynamically to settings-card
    const yearLabelParent = document.getElementById('festYearLabel').parentElement;
    monthSelector = document.createElement('select');
    monthSelector.id = 'festMonthSelect';
    monthSelector.className = 'form-select';
    monthSelector.style.width = '100px';
    monthSelector.style.padding = '4px 8px';
    monthSelector.style.fontSize = '12px';
    MONTH_NAMES.forEach((m, idx) => {
      const opt = document.createElement('option');
      opt.value = idx + 1;
      opt.textContent = m;
      monthSelector.appendChild(opt);
    });
    // Default to current month
    monthSelector.value = new Date().getMonth() + 1;
    monthSelector.addEventListener('change', () => renderJainFestivalsView());
    yearLabelParent.insertBefore(monthSelector, document.getElementById('festNext'));
  }
  
  const selectedMonth = parseInt(monthSelector.value, 10);
  const year = festState.year;
  const numDays = new Date(year, selectedMonth, 0).getDate();
  const firstDayIndex = new Date(year, selectedMonth - 1, 1).getDay(); // 0=Sun
  
  // Empty cells before first day
  for (let i = 0; i < firstDayIndex; i++) {
    const empty = document.createElement('div');
    empty.className = 'cal-cell empty';
    grid.appendChild(empty);
  }
  
  // Render each calendar cell
  for (let dayNum = 1; dayNum <= numDays; dayNum++) {
    const dStr = `${year}-${String(selectedMonth).padStart(2,'0')}-${String(dayNum).padStart(2,'0')}`;
    const cell = document.createElement('div');
    cell.className = 'cal-cell';
    
    // Find matching festivals for this day
    const dayEvents = filteredList.filter(f => {
      return f.start_date <= dStr && dStr <= f.end_date;
    });
    
    const isReview = dayEvents.some(f => f.status === 'review_needed');
    if (isReview) cell.className += ' review-needed-cell';
    
    let markersHTML = '';
    if (dayEvents.length) {
      markersHTML = `<div class="fest-markers-container">` + 
        dayEvents.map(f => {
          const catClass = f.status === 'review_needed' ? 'review' : f.category;
          return `<div class="fest-marker fest-marker--${catClass}">${f.name}</div>`;
        }).join('') + `</div>`;
    }
    
    cell.innerHTML = `
      <div class="cal-cell-header" style="justify-content:space-between;">
        <span class="cal-date">${dayNum}</span>
      </div>
      <div style="flex:1;">
        ${markersHTML}
      </div>
    `;
    
    if (dayEvents.length) {
      cell.addEventListener('click', () => {
        // Open modal for the first festival or show choices if multiple
        if (dayEvents.length === 1) {
          openFestivalModal(dayEvents[0]);
        } else {
          // Open choice modal or first one
          openFestivalModal(dayEvents[0]);
        }
      });
    }
    grid.appendChild(cell);
  }
}

function getCategoryPill(f) {
  let cat = f.category ? f.category.toLowerCase() : '';
  let name = f.name ? f.name.toLowerCase() : '';
  
  if (cat === 'mahaparv' || name.includes('daslakshan') || name.includes('raksha bandhan')) {
    return `<span class="fest-badge" style="background:#3498DB; color:#FFF; font-size:10px; font-weight:600; padding:3px 6px; border-radius:10px;">🔵 Mahaparv</span>`;
  }
  if (cat === 'kalyanak' || name.includes('kalyanak') || name.includes('janma') || name.includes('moksha')) {
    return `<span class="fest-badge" style="background:#2ECC71; color:#FFF; font-size:10px; font-weight:600; padding:3px 6px; border-radius:10px;">🟢 Kalyanak</span>`;
  }
  if (name.includes('parva tithi') || cat === 'parva_tithi' || name.includes('pakhi')) {
    return `<span class="fest-badge" style="background:#E67E22; color:#FFF; font-size:10px; font-weight:600; padding:3px 6px; border-radius:10px;">🟠 Parva Tithi</span>`;
  }
  return `<span class="fest-badge" style="background:#9B59B6; color:#FFF; font-size:10px; font-weight:600; padding:3px 6px; border-radius:10px;">🟣 Parva / Vrat</span>`;
}

function renderJainList(filteredList) {
  const listContainer = document.getElementById('festList');
  if (!listContainer) return;
  listContainer.innerHTML = '';
  
  if (!filteredList.length) {
    listContainer.innerHTML = '<div class="cal-loading" style="padding:20px;">No matching festivals found.</div>';
    return;
  }
  
  // Group by Date
  const dateGroups = {};
  filteredList.forEach(f => {
    // 1. Add to start date
    if (f.start_date.startsWith(String(festState.year))) {
      if (!dateGroups[f.start_date]) dateGroups[f.start_date] = [];
      if (!dateGroups[f.start_date].some(x => x.occurrence_id === f.occurrence_id)) {
        dateGroups[f.start_date].push(f);
      }
    }
    
    // 2. For Bhaktambar Vrat, also add to end date (so it appears on both 8 and 14)
    const isBhaktambar = f.name && f.name.toLowerCase().includes("bhaktambar");
    if (isBhaktambar && f.end_date && f.end_date !== f.start_date) {
      const endDates = [f.end_date];
      
      // If the end date's tithi is repeated, add the adjacent days with the same tithi
      const endTithi = festState.panchang_tithi_map?.[f.end_date];
      if (endTithi) {
        const prevDay = shiftDateStr(f.end_date, -1);
        if (festState.panchang_tithi_map?.[prevDay] === endTithi) {
          endDates.push(prevDay);
        }
        const nextDay = shiftDateStr(f.end_date, 1);
        if (festState.panchang_tithi_map?.[nextDay] === endTithi) {
          endDates.push(nextDay);
        }
      }

      endDates.forEach(dStr => {
        if (dStr.startsWith(String(festState.year))) {
          if (!dateGroups[dStr]) dateGroups[dStr] = [];
          if (!dateGroups[dStr].some(x => x.occurrence_id === f.occurrence_id)) {
            dateGroups[dStr].push(f);
          }
        }
      });
    }
  });
  
  const sortedDates = Object.keys(dateGroups).sort();
  
  sortedDates.forEach(dateStr => {
    const dayEvents = dateGroups[dateStr];
    const dateTitle = formatDateLabel(dateStr).split(',')[0];
    
    const groupDiv = document.createElement('div');
    groupDiv.className = 'settings-card';
    groupDiv.style.marginBottom = '12px';
    groupDiv.style.padding = '12px';
    
    const tithiDisplay = (festState.panchang_tithi_map && festState.panchang_tithi_map[dateStr]) 
      ? festState.panchang_tithi_map[dateStr] 
      : `${dayEvents[0].jain_month} ${dayEvents[0].paksha} ${dayEvents[0].tithi}`;
      
    let html = `<div style="font-size:13px; font-weight:bold; color:#2C3E50; margin-bottom:8px; border-bottom:1px solid #ECF0F1; padding-bottom:6px;">
      [ ${dateStr.slice(5)} | ${dateTitle} ] ─── ${tithiDisplay}
    </div>`;
    
    dayEvents.forEach((f, idx) => {
      const isLast = idx === dayEvents.length - 1;
      const branch = isLast ? '└──' : '├──';
      const isMultiDay = f.start_date && f.end_date && f.start_date !== f.end_date;
      const rangeTag = isMultiDay 
        ? `<span style="font-size:10px; background:rgba(142,68,173,0.12); color:#8E44AD; padding:2px 6px; border-radius:4px; margin-left:6px;">Span: ${f.start_date.slice(5)} – ${f.end_date.slice(5)}</span>`
        : '';
        
      let progressHTML = '';
      if (f.daily_schedule && f.daily_schedule.length > 0) {
        progressHTML = `<div style="margin-top:6px; margin-left:24px; display:flex; flex-wrap:wrap; gap:4px; font-size:10px;">`;
        f.daily_schedule.forEach((d, i) => {
           let v = d.virtue.includes('(') ? d.virtue.split('(')[0] : d.virtue;
           progressHTML += `<span style="background:#F0F3F4; padding:3px 6px; border-radius:4px; color:#34495E; border:1px solid #E5E8E8;">Day ${i+1}: ${v}</span>`;
        });
        progressHTML += `</div>`;
      }
      
      html += `
      <div style="display:flex; align-items:flex-start; margin-bottom:10px; cursor:pointer;" onclick="openFestivalModal('${f.occurrence_id}')">
        <div style="color:#BDC3C7; font-family:monospace; margin-right:8px; font-size:14px; user-select:none;">${branch}</div>
        <div style="flex:1;">
          ${getCategoryPill(f)} <strong style="color:#2C3E50; margin-left:6px; font-size:14px;">${f.name}</strong> ${rangeTag}
          ${progressHTML}
        </div>
      </div>`;
    });
    
    groupDiv.innerHTML = html;
    listContainer.appendChild(groupDiv);
  });
}

registerPage('festivals', {
  onEnter() {
    document.getElementById('festYearLabel').textContent = festState.year;
    loadJainFestivals();
  }
});

// ── YOGA MUHURTA ──────────────────────────────────────────────
const yogaState = { date: todayStr() };

const YOGA_RECOMMENDATION_LABELS = {
  highly_auspicious: 'Highly Auspicious',
  auspicious: 'Auspicious',
  caution: 'Caution',
  avoid: 'Avoid',
  neutral: 'No Listed Yoga',
};

const YOGA_BADGE_COLORS = {
  highly_auspicious: '#1a7f4e',
  auspicious: '#1a5276',
  caution: '#7d6608',
  avoid: '#922b21',
  neutral: '#566573',
};

const YOGA_BADGE_BG = {
  highly_auspicious: '#c6efce',
  auspicious: '#daeaf7',
  caution: '#fff3cd',
  avoid: '#ffd5d5',
  neutral: '#f2f2f2',
};

function yogaOffsetDate(base, offset) {
  const [y, m, d] = base.split('-').map(Number);
  const dt = new Date(y, m - 1, d + offset);
  return `${dt.getFullYear()}-${String(dt.getMonth()+1).padStart(2,'0')}-${String(dt.getDate()).padStart(2,'0')}`;
}

async function loadYogaMuhurta() {
  const content = document.getElementById('yogaMuhurtaContent');
  const badge = document.getElementById('yogaMuhurtaBadge');
  const label = document.getElementById('yogaMuhurtaDateLabel');
  label.textContent = formatDateLabel(yogaState.date);
  content.innerHTML = '<div class="loading-spinner">Calculating…</div>';
  badge.innerHTML = '';

  const st = getState();
  try {
    const data = await apiFetch('/dainika-muhurta', 'POST', {
      date: yogaState.date,
      lat: st.lat,
      lon: st.lon,
      ayanamsa: st.ayanamsa || 'Lahiri',
    });

    const rec = data.recommendation;
    badge.innerHTML = `
      <span style="display:inline-block;padding:6px 18px;border-radius:20px;
        font-size:13px;font-weight:700;
        background:${YOGA_BADGE_BG[rec] || '#f2f2f2'};
        color:${YOGA_BADGE_COLORS[rec] || '#333'};">
        ${YOGA_RECOMMENDATION_LABELS[rec] || rec}
      </span>
      <div style="font-size:11px;color:#888;margin-top:4px;">
        Vara ${data.vara} · Tithi ${data.tithi} · Nakshatra ${data.nakshatra}
      </div>`;

    // Normalize a yoga name for deduplication comparison:
    // strip trailing " Yoga"/" Nakshatra", lowercase, unify u→i (Sanskrit transliteration variants).
    function normYogaName(s) {
      return s.toLowerCase()
        .replace(/\s+yoga$/i, '')
        .replace(/\s+nakshatra$/i, '')
        .replace(/u/g, 'i');
    }
    // Aanandadi yoga base-names, pre-normalized.
    const aanandadiBaseNames = (data.aanandadi_yogas || []).map(y => normYogaName(y.name));

    // Returns true if a Dainika yoga name is conceptually covered by an active Aanandadi yoga:
    // exact normalized match (e.g. Amrit/Amrut → both "amrit"), or prefix match when the names
    // differ by at most 2 characters (e.g. "rakshas" ⊂ "rakshasa", diff=1).
    function shadowedByAanandadi(yogaName) {
      const base = normYogaName(yogaName);
      return aanandadiBaseNames.some(an => {
        if (an === base) return true;
        const longer  = an.length > base.length ? an : base;
        const shorter = an.length <= base.length ? an : base;
        return longer.startsWith(shorter) && (longer.length - shorter.length) <= 2;
      });
    }

    const activeYogas = data.yogas.filter(y => !y.cancelled && !shadowedByAanandadi(y.name));
    const shubh = activeYogas.filter(y => y.nature === 'shubh');
    const ashubh = activeYogas.filter(y => y.nature === 'ashubh');
    // Ravi Yoga (Sun-Moon distance formula) renders in the inauspicious Dainika table.
    const raviYogas = data.ravi_yogas || [];
    const ashubhWithRavi = [...ashubh, ...raviYogas];

    function severityBadge(sev) {
      const bg = sev==='highly_inauspicious'?'#ffd5d5':sev==='highly_auspicious'?'#c6efce':sev==='inauspicious'?'#ffeb9c':'#daeaf7';
      return `<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:${bg};color:#333;">${sev.replace(/_/g,' ')}</span>`;
    }

    // Group yogas that share the exact same time window into a single table row.
    // The first yoga in each group becomes the primary (drives all columns);
    // extras appear as compact sub-tags beneath the primary name.
    function groupByWindow(yogas) {
      const map = new Map();
      for (const y of yogas) {
        const key = `${y.start_time}|${y.end_time}`;
        if (!map.has(key)) map.set(key, []);
        map.get(key).push(y);
      }
      return [...map.values()];
    }

    function yogaSection(title, yogas, color) {
      if (!yogas.length) return '';
      const groups = groupByWindow(yogas);
      const rows = groups.map((group, i) => {
        const y = group[0];
        const isNullified = y.is_nullified;
        const rowBg = isNullified ? 'opacity:0.45;background:transparent;'
          : (i % 2 === 1 ? 'background:#fafafa;' : 'background:#fff;');
        const timing = (y.start_time && y.end_time)
          ? `<div style="font-size:11px;color:#666;margin-top:3px;white-space:nowrap;">${y.start_time} – ${y.end_time}</div>`
          : '';
        const nullBadge = isNullified
          ? `<div style="font-size:10px;color:#999;margin-top:2px;font-style:italic;">Nullified by ${y.nullified_by}</div>`
          : '';
        const conflictBadge = y.is_conflict
          ? `<div style="font-size:10px;color:#c0392b;background:#fdf2f0;border-radius:3px;padding:1px 5px;margin-top:3px;display:inline-block;">⚠ Conflicts with: ${(y.conflicts_with||[]).join(', ')}</div>`
          : '';
        const extraTags = group.slice(1).map(extra =>
          `<span style="display:inline-block;margin-top:4px;margin-right:4px;font-size:10px;
            padding:1px 7px;border-radius:8px;background:#efefef;color:#555;">${extra.name}</span>`
        ).join('');
        const triggerLabel = y.trigger_detail || y.trigger_kind || '';
        return `
        <tr style="${rowBg}border-bottom:1px solid #f0f0f0;">
          <td style="font-weight:600;font-size:13px;padding:7px 10px;vertical-align:top;">
            ${y.name}${y.diminished ? ' <span style="font-size:10px;color:#e67e22;">(diminished)</span>' : ''}
            ${timing}
            ${extraTags ? `<div style="margin-top:3px;">${extraTags}</div>` : ''}
            ${nullBadge}${conflictBadge}
          </td>
          <td style="font-size:12px;padding:7px 8px;vertical-align:top;font-weight:600;color:${y.nature==='shubh'?'#1a7f4e':'#922b21'};text-transform:capitalize;">${y.nature}</td>
          <td style="font-size:11px;padding:7px 8px;vertical-align:top;color:#555;">${triggerLabel}</td>
          <td style="padding:7px 8px;vertical-align:top;">${severityBadge(y.severity)}</td>
          <td style="font-size:12px;color:#555;padding:7px 8px;vertical-align:top;">${y.meaning}</td>
        </tr>`;
      }).join('');
      return `
        <div style="margin-bottom:18px;border-radius:6px;overflow:hidden;border:1px solid #e8e8e8;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
          <div style="font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:0.4px;
            color:${color};padding:7px 12px;background:${color}15;border-bottom:1px solid ${color}25;">${title}</div>
          <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
              <thead>
                <tr style="background:#f8f8f8;border-bottom:1px solid #e8e8e8;">
                  <th style="text-align:left;padding:6px 10px;font-size:11px;color:#777;font-weight:600;">Yoga &amp; Time</th>
                  <th style="text-align:left;padding:6px 8px;font-size:11px;color:#777;font-weight:600;">Nature</th>
                  <th style="text-align:left;padding:6px 8px;font-size:11px;color:#777;font-weight:600;">Active When</th>
                  <th style="text-align:left;padding:6px 8px;font-size:11px;color:#777;font-weight:600;">Severity</th>
                  <th style="text-align:left;padding:6px 8px;font-size:11px;color:#777;font-weight:600;">Meaning</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>`;
    }

    function aanandadiSection(yogas) {
      if (!yogas || !yogas.length) return '';
      const rec = data.aanandadi_recommendation || 'neutral';
      const recLabel = YOGA_RECOMMENDATION_LABELS[rec] || rec;
      const recBadge = `<span style="display:inline-block;padding:3px 12px;border-radius:12px;font-size:12px;font-weight:700;
        background:${YOGA_BADGE_BG[rec]||'#f2f2f2'};color:${YOGA_BADGE_COLORS[rec]||'#333'};">${recLabel}</span>`;

      const aShubh = yogas.filter(y => y.nature === 'ashubh');
      const aShubhYogas = yogas.filter(y => y.nature === 'shubh');

      function aanandadiSubTable(title, list, color) {
        if (!list.length) return '';
        const rows = list.map(y => {
          const timing = (y.start_time && y.end_time)
            ? `<div style="font-size:10px;color:#666;">${y.start_time} – ${y.end_time}</div>` : '';
          let varjyaHtml;
          if (y.varjya_minutes === 'full_day') {
            varjyaHtml = `<span style="color:#c0392b;font-weight:700;font-size:11px;">Entire period</span>`;
          } else if (y.varjya_minutes) {
            varjyaHtml = `<span style="font-size:11px;">${y.varjya_start_time}–${y.varjya_end_time}<br><span style="color:#888;">${y.varjya_minutes.toFixed(1)} min</span></span>`;
          } else {
            varjyaHtml = `<span style="color:#888;font-size:11px;">–</span>`;
          }
          return `
          <tr>
            <td style="font-weight:600;font-size:13px;padding:6px 10px;">${y.name}${timing}</td>
            <td style="font-size:12px;padding:6px 8px;">${y.triggering_planet}</td>
            <td style="font-size:12px;padding:6px 8px;">${y.trigger_nakshatra}</td>
            <td style="padding:6px 8px;">${severityBadge(y.severity)}</td>
            <td style="font-size:12px;padding:6px 8px;color:#555;">${y.fal}</td>
            <td style="padding:6px 8px;">${varjyaHtml}</td>
            <td style="font-size:11px;color:#666;padding:6px 8px;max-width:220px;">${y.meaning}</td>
          </tr>`;
        }).join('');
        return `
          <div style="margin-bottom:10px;">
            <div style="font-weight:600;font-size:11px;text-transform:uppercase;
              color:${color};padding:4px 10px;background:${color}18;">${title}</div>
            <div style="overflow-x:auto;">
              <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead>
                  <tr style="background:#f5f5f5;">
                    <th style="text-align:left;padding:5px 10px;font-size:11px;">Yoga &amp; Time</th>
                    <th style="text-align:left;padding:5px 8px;font-size:11px;">Planet</th>
                    <th style="text-align:left;padding:5px 8px;font-size:11px;">Nakshatra</th>
                    <th style="text-align:left;padding:5px 8px;font-size:11px;">Severity</th>
                    <th style="text-align:left;padding:5px 8px;font-size:11px;">Fal</th>
                    <th style="text-align:left;padding:5px 8px;font-size:11px;">Varjya</th>
                    <th style="text-align:left;padding:5px 8px;font-size:11px;">Meaning</th>
                  </tr>
                </thead>
                <tbody>${rows}</tbody>
              </table>
            </div>
          </div>`;
      }

      return `
        <div style="margin-top:20px;border-top:2px solid #e8e8e8;padding-top:14px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
            <span style="font-weight:700;font-size:13px;color:#5d4037;">Aanandadi Yogas (आनन्दादि योग)</span>
            ${recBadge}
          </div>
          ${aanandadiSubTable('Auspicious', aShubhYogas, '#1a7f4e')}
          ${aanandadiSubTable('Inauspicious', aShubh, '#922b21')}
        </div>`;
    }

    function specialYogasSection(yogas) {
      if (!yogas || yogas.length === 0) return '';
      const rows = yogas.map(y => {
        const timing = y.start_time && y.end_time ? `${y.start_time}–${y.end_time}` : 'All day';
        const clipped = (y.clipped_start ? '◀ ' : '') + timing + (y.clipped_end ? ' ▶' : '');
        const specificNak = y.name === 'Gandmool Nakshatra'
          ? (y.trigger_detail || '').replace('Moon in ', '')
          : '';
        const nameCell = specificNak
          ? `${y.name}<div style="font-size:11px;color:#c0392b;font-weight:600;margin-top:2px;">${specificNak}</div>`
          : y.name;
        return `<tr>
          <td style="font-weight:600">${nameCell}</td>
          <td style="font-size:11px;color:#666">${clipped}</td>
          <td style="font-size:11px;color:#666">${y.trigger_detail || ''}</td>
          <td style="font-size:12px">${y.meaning}</td>
        </tr>`;
      }).join('');
      return `
        <div style="margin-top:20px;border-top:2px solid #e8e8e8;padding-top:14px;">
          <div style="font-weight:700;font-size:13px;color:#7b2d00;margin-bottom:8px;">Special Yogas (Panchak / Gandmool / Jwalamukhi)</div>
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead><tr style="background:#f5e6d0;font-size:12px;">
              <th style="text-align:left;padding:5px 8px">Yoga</th>
              <th style="text-align:left;padding:5px 8px">Window</th>
              <th style="text-align:left;padding:5px 8px">Trigger</th>
              <th style="text-align:left;padding:5px 8px">Meaning</th>
            </tr></thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;
    }

    const traditionalHtml = (activeYogas.length === 0 && raviYogas.length === 0)
      ? `<div style="text-align:center;padding:24px 16px;color:#888;font-size:14px;">No traditional yoga active for this date.</div>`
      : yogaSection('Auspicious Yogas', shubh, '#1a7f4e') + yogaSection('Inauspicious Yogas', ashubhWithRavi, '#922b21');

    content.innerHTML = traditionalHtml + aanandadiSection(data.aanandadi_yogas) + specialYogasSection(data.special_yogas);

  } catch (err) {
    content.innerHTML = `<div style="padding:20px;color:#c0392b;">Error: ${err.message}</div>`;
    badge.innerHTML = '';
  }
}

document.getElementById('yogaMuhurtaPrev').addEventListener('click', () => {
  yogaState.date = yogaOffsetDate(yogaState.date, -1);
  loadYogaMuhurta();
});
document.getElementById('yogaMuhurtaNext').addEventListener('click', () => {
  yogaState.date = yogaOffsetDate(yogaState.date, 1);
  loadYogaMuhurta();
});

document.getElementById('yogaExportBtn').addEventListener('click', async () => {
  const [y, m] = yogaState.date.split('-').map(Number);
  const st = getState();
  const btn = document.getElementById('yogaExportBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Generating…';
  try {
    const data = await apiFetch('/dainika-muhurta-export', 'POST', {
      year: y, month: m, lat: st.lat, lon: st.lon,
      ayanamsa: st.ayanamsa || 'Lahiri',
    });
    const a = document.createElement('a');
    a.href = data.download_url;
    a.download = data.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } catch (err) {
    alert('Export failed: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '⬇ Export Month Excel';
  }
});

registerPage('yoga-muhurta', {
  onEnter() {
    loadYogaMuhurta();
  }
});

// ── Boot ──────────────────────────────────────────────────────
initTheme();
initDrawer();
initNavButtons();
window.addEventListener('hashchange', route);
route();
