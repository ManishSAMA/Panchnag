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
  location.hash = page + query;
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

window.addEventListener('hashchange', route);

// ── Drawer ────────────────────────────────────────────────────
function initDrawer() {
  const overlay = document.getElementById('drawerOverlay');
  const drawer  = document.getElementById('drawer');

  function open() {
    overlay.classList.add('open');
    drawer.classList.add('open');
  }
  function close() {
    overlay.classList.remove('open');
    drawer.classList.remove('open');
  }

  overlay.addEventListener('click', close);

  document.querySelectorAll('[id$="MenuBtn"]').forEach(btn => {
    btn.addEventListener('click', open);
  });
  document.getElementById('homeMenuBtn').addEventListener('click', open);

  drawer.querySelectorAll('[data-nav]').forEach(btn => {
    btn.addEventListener('click', () => { navigate(btn.dataset.nav); close(); });
  });
}

// ── Shared: data-nav buttons ──────────────────────────────────
function initNavButtons() {
  document.querySelectorAll('[data-nav]').forEach(el => {
    el.addEventListener('click', () => navigate(el.dataset.nav));
  });
}

// ── Date Banner render ────────────────────────────────────────
function renderDateBanner(moonEl, gregorianEl, detailsEl, data) {
  const p = data.panchang;
  const tithiIdx = p.tithi?.index || 1;
  moonEl.textContent = moonEmoji(tithiIdx);

  const dt = new Date(data.date + 'T00:00:00');
  gregorianEl.textContent = dt.toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  });

  const samvat   = p.vikram_samvat || '—';
  const month    = p.hindu_month?.name || '—';
  const tithi    = p.tithi?.name || '—';
  const location = data.location || '—';
  detailsEl.textContent = `VS ${samvat} | ${month} | ${tithi} | ${location}`;
}

// ── HOME ──────────────────────────────────────────────────────
registerPage('home', {
  onEnter() {
    const state = getState();
    const moonEl     = document.getElementById('homeBanner').querySelector('.date-banner-moon');
    const gregorian  = document.getElementById('homeGregorianDate');
    const details    = document.getElementById('homeBannerDetails');

    if (!state.lat || !state.lon) {
      const dt = new Date();
      gregorian.textContent = dt.toLocaleDateString('en-IN', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
      });
      details.textContent = 'Set a location for panchang data';
      return;
    }

    apiFetch('/generate-panchang', 'POST', {
      date: todayStr(), lat: state.lat, lon: state.lon, ayanamsa: state.ayanamsa || 'Lahiri'
    }).then(data => renderDateBanner(moonEl, gregorian, details, data))
      .catch(() => { details.textContent = 'Could not load panchang'; });
  }
});

// ── CALENDAR ──────────────────────────────────────────────────
const calState = { year: new Date().getFullYear(), month: new Date().getMonth() + 1 };

const MONTH_NAMES = ['January','February','March','April','May','June',
                     'July','August','September','October','November','December'];

registerPage('calendar', {
  _abortCtrl: null,

  onEnter() {
    this._renderNav();
    this._load();
  },

  onLeave() {
    if (this._abortCtrl) this._abortCtrl.abort();
  },

  _renderNav() {
    const label = `${MONTH_NAMES[calState.month - 1]} ${calState.year}`;
    document.getElementById('calMonthTitle').textContent = label;
    document.getElementById('calNavTitle').textContent  = label;
  },

  async _load() {
    const state = getState();
    const grid  = document.getElementById('calGrid');
    grid.innerHTML = '<div class="cal-loading">Loading…</div>';

    if (!state.lat || !state.lon) {
      grid.innerHTML = '<div class="cal-loading">Please set a location first.</div>';
      return;
    }

    try {
      const data = await apiFetch(
        `/month-overview?year=${calState.year}&month=${calState.month}&lat=${state.lat}&lon=${state.lon}&ayanamsa=${state.ayanamsa || 'Lahiri'}`
      );

      document.getElementById('calSamvat').textContent = `Vikram Samvat ${data.vikram_samvat} | ${data.hindu_month}`;

      this._renderGrid(data.days);
    } catch (e) {
      grid.innerHTML = `<div class="cal-loading">Error: ${e.message}</div>`;
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
      const dayNum = parseInt(day.date.split('-')[2], 10);
      const tithiNum = day.tithi_index || '';

      cell.innerHTML = `
        <div class="cal-cell-top">
          <span class="cal-date">${dayNum}</span>
          <span class="cal-tithi">${tithiNum}</span>
        </div>
        <div class="cal-cell-bottom">
          <span class="cal-time" data-sr="">—</span>
          <span class="cal-time" data-ss="">—</span>
        </div>
        <div class="cal-nakshatra">${(day.nakshatra_name || '').split(' ')[0]}</div>
      `;

      cell.addEventListener('click', () => navigate('panchang', { date: day.date }));
      grid.appendChild(cell);
    });

    // Lazy-load sunrise/sunset for visible cells
    this._loadSunTimes(days, fmt);
  },

  async _loadSunTimes(days, fmt) {
    const state = getState();
    if (!state.lat || !state.lon) return;

    this._abortCtrl = new AbortController();
    const signal = this._abortCtrl.signal;
    const CONCURRENCY = 5;

    for (let i = 0; i < days.length; i += CONCURRENCY) {
      if (signal.aborted) break;
      const chunk = days.slice(i, i + CONCURRENCY);
      await Promise.all(chunk.map(async day => {
        if (signal.aborted) return;
        try {
          const data = await apiFetch('/generate-panchang', 'POST', {
            date: day.date, lat: state.lat, lon: state.lon, ayanamsa: state.ayanamsa || 'Lahiri'
          });
          const sr = data.events?.sunrise?.time?.slice(0, 5) || '';
          const ss = data.events?.sunset?.time?.slice(0, 5) || '';

          const cells = document.querySelectorAll('.cal-cell:not(.empty)');
          const dayNum = parseInt(day.date.split('-')[2], 10);
          const startWeekday = new Date(days[0].date + 'T00:00:00').getDay();
          const cellIndex = startWeekday + dayNum - 1;
          const allCells = document.getElementById('calGrid').children;
          const cell = allCells[cellIndex];
          if (cell) {
            const srEl = cell.querySelector('[data-sr]');
            const ssEl = cell.querySelector('[data-ss]');
            if (srEl) srEl.textContent = formatTime(sr, fmt);
            if (ssEl) ssEl.textContent = formatTime(ss, fmt);
          }
        } catch { /* skip */ }
      }));
    }
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

registerPage('panchang', {
  onEnter(params) {
    panchangFmt = getState().timeFormat || '12h';
    const date = params.date || todayStr();
    this._updateToggleUI();

    const moonEl   = document.getElementById('panchangMoon');
    const gregEl   = document.getElementById('panchangGregorianDate');
    const detailEl = document.getElementById('panchangBannerDetails');
    gregEl.textContent   = '—';
    detailEl.textContent = '—';

    const content = document.getElementById('panchangContent');
    content.innerHTML = '<div class="loading-spinner">Loading panchang…</div>';

    const state = getState();
    if (!state.lat || !state.lon) {
      content.innerHTML = '<div class="error-msg">Please set a location first.</div>';
      return;
    }

    apiFetch('/generate-panchang', 'POST', {
      date, lat: state.lat, lon: state.lon, ayanamsa: state.ayanamsa || 'Lahiri'
    }).then(data => {
      panchangData = data;
      renderDateBanner(moonEl, gregEl, detailEl, data);
      this._render(data);
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

    const rows = [
      { label: 'Tithi', value: p.tithi?.name, sub: p.tithi?.ends?.time ? `upto ${ft(p.tithi.ends.time)}` : '' },
      { label: 'Nakshatra', value: `${p.nakshatra?.name || '—'} (Pada ${p.nakshatra?.pada || '—'})`, sub: p.nakshatra?.ends?.time ? `upto ${ft(p.nakshatra.ends.time)}` : '' },
      { label: 'Yoga', value: p.yoga?.name || '—', sub: '' },
      { label: 'Karana', value: p.karana?.name || '—', sub: '' },
      { label: 'Weekday', value: p.vara?.name || '—', sub: '' },
      { label: 'Moon Rashi', value: p.moon_rashi || '—', sub: '' },
      { label: 'Sun Rashi', value: p.sun_rashi || '—', sub: '' },
    ];

    content.innerHTML = `
      <div class="panchang-card">
        <div class="panchang-sun-moon">
          <div class="sun-moon-cell">
            <div class="sun-moon-label">🌅 Sunrise</div>
            <div class="sun-moon-time">${ft(ev.sunrise?.time)}</div>
          </div>
          <div class="sun-moon-cell">
            <div class="sun-moon-label">🌇 Sunset</div>
            <div class="sun-moon-time">${ft(ev.sunset?.time)}</div>
          </div>
        </div>
        <div class="panchang-sun-moon" style="border-bottom:1px solid var(--gold-dark)">
          <div class="sun-moon-cell">
            <div class="sun-moon-label">🌕 Moonrise</div>
            <div class="sun-moon-time">${ft(ev.moonrise?.time)}</div>
          </div>
          <div class="sun-moon-cell">
            <div class="sun-moon-label">🌑 Moonset</div>
            <div class="sun-moon-time">${ft(ev.moonset?.time)}</div>
          </div>
        </div>
        ${rows.map(r => `
          <div class="panchang-row">
            <div class="panchang-label">${r.label}</div>
            <div class="panchang-value">
              ${r.value || '—'}
              ${r.sub ? `<br><span class="panchang-endtime">${r.sub}</span>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }
});

// Panchang time format toggle
document.querySelectorAll('[data-fmt]').forEach(btn => {
  btn.addEventListener('click', () => {
    panchangFmt = btn.dataset.fmt;
    saveState({ timeFormat: panchangFmt });
    pages['panchang']._updateToggleUI();
    if (panchangData) pages['panchang']._render(panchangData);
  });
});

document.getElementById('panchangBack').addEventListener('click', () => history.back());

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

function findCurrentSlot(slots, dateStr) {
  const now = Date.now();
  return slots.find(s => {
    const start = parseTimeToday(s.start_time, dateStr);
    let   end   = parseTimeToday(s.end_time, dateStr);
    if (end !== null && s.period === 'night' && end < start) {
      end += 24 * 60 * 60 * 1000;
    }
    return start !== null && end !== null && now >= start && now < end;
  }) || null;
}

function startCountdown(slot, dateStr) {
  if (chogState.timerInterval) clearInterval(chogState.timerInterval);
  if (!slot) {
    document.getElementById('chogCountdown').textContent = '--:--:--';
    return;
  }

  let endMs = parseTimeToday(slot.end_time, dateStr);
  if (slot.period === 'night') {
    const startMs = parseTimeToday(slot.start_time, dateStr);
    if (endMs < startMs) endMs += 24 * 60 * 60 * 1000;
  }

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
    const ft = t => chogFormatTime(t, fmt);
    document.getElementById('chogCurrentTime').textContent =
      `${ft(current.start_time)} – ${ft(current.end_time)}`;
    document.getElementById('chogCurrentName').textContent = `🪔 ${current.name}`;
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
    const icon = isCurrent ? '⏳' : slot.nature === 'inauspicious' ? '❌' : '';
    const ft = t => chogFormatTime(t, fmt);
    return `
      <div class="chog-slot ${slot.nature}${isCurrent ? ' current' : ''}">
        <div class="chog-slot-name">
          <div class="chog-slot-name-text">
            ${slot.name}
            <small>${slot.meaning}</small>
          </div>
          <span>🪔</span>
        </div>
        <div class="chog-slot-time">
          <span>${ft(slot.start_time)} to ${ft(slot.end_time)}</span>
          <span class="chog-slot-icon">${icon}</span>
        </div>
      </div>
    `;
  }

  const ft = t => chogFormatTime(t, fmt);
  const content = document.getElementById('chogContent');
  content.innerHTML = `
    <div class="chog-section-header">
      ☀️ Day
      <span>🌅 Sunrise – ${ft(sunrise)}</span>
    </div>
    ${daySlots.map(makeSlotHTML).join('')}
    <div class="chog-section-header">
      🌙 Night
      <span>🌇 Sunset – ${ft(sunset)}</span>
    </div>
    ${nightSlots.map(makeSlotHTML).join('')}
  `;
}

async function loadChoghadiya() {
  const state = getState();
  const content = document.getElementById('chogContent');
  content.innerHTML = '<div class="loading-spinner">Loading Choghadiya…</div>';

  document.getElementById('chogDateLabel').textContent = formatDateLabel(chogState.date);
  renderWeekdayTabs(chogState.date);

  if (!state.lat || !state.lon) {
    content.innerHTML = '<div class="error-msg">Please set a location first.</div>';
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

// ── Boot ──────────────────────────────────────────────────────
initDrawer();
initNavButtons();
route();
