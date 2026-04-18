// ── Translations ──────────────────────────────────────────────
const T = {
  en: {
    appTitle:           "Jain Panchang",
    setLocation:        "Set Location",
    tools:              "Export",
    locationTitle:      "Choose Location",
    citySearch:         "City search",
    latitude:           "Latitude",
    longitude:          "Longitude",
    ayanamsa:           "Ayanamsa",
    save:               "Save",
    cancel:             "Cancel",
    toolsTitle:         "Export Tools",
    yearRangeTitle:     "Year-range Export",
    startYear:          "Start year",
    endYear:            "End year",
    format:             "Format",
    monthlyFiles:       "Monthly files",
    generateRange:      "Export",
    pdfTitle:           "PDF Panchang",
    year:               "Year",
    generatePdf:        "Generate PDF",
    loading:            "Loading…",
    error:              "Error",
    close:              "Close",
    purnima:            "🌕 Purnima",
    amavasya:           "🌑 Amavasya",
    ekadashi:           "✿ Ekadashi",
    panchangHeading:    "Panchang",
    eventsHeading:      "Events",
    samvatHeading:      "Samvat",
    tithi:              "◑ Tithi",
    tithiEnds:          "Tithi ends",
    jainTithi:          "◑ Jain Tithi",
    jainTithiEnds:      "Jain Tithi ends",
    jainRef:            "Jain reference",
    nakshatra:          "✦ Nakshatra",
    nakshatraEnds:      "Nakshatra ends",
    pada:               "Pada",
    yoga:               "⊕ Yoga",
    karana:             "◗ Karana",
    vara:               "☉ Vara",
    moonRashi:          "☽ Moon Rashi",
    sunRashi:           "☀ Sun Rashi",
    hinduMonth:         "Hindu Month",
    vikramSamvat:       "Vikram Samvat",
    viraSamvat:         "Vira Nirvana Samvat",
    sunrise:            "↑☀ Sunrise",
    sunset:             "↓☀ Sunset",
    moonrise:           "↑☽ Moonrise",
    moonset:            "↓☽ Moonset",
    locationRequired:   "Provide city or coordinates.",

    weekdays:     ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"],
    months:       ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"],
    hinduMonths:  ["Chaitra","Vaishakha","Jyeshtha","Ashadha","Shravana",
                   "Bhadrapada","Ashwin","Kartika","Agrahayana","Pausha","Magha","Phalguna"],
    tithiNames: [
      "Shukla Pratipada","Shukla Dwitiya","Shukla Tritiya","Shukla Chaturthi",
      "Shukla Panchami","Shukla Shashthi","Shukla Saptami","Shukla Ashtami",
      "Shukla Navami","Shukla Dashami","Shukla Ekadashi","Shukla Dwadashi",
      "Shukla Trayodashi","Shukla Chaturdashi","Purnima",
      "Krishna Pratipada","Krishna Dwitiya","Krishna Tritiya","Krishna Chaturthi",
      "Krishna Panchami","Krishna Shashthi","Krishna Saptami","Krishna Ashtami",
      "Krishna Navami","Krishna Dashami","Krishna Ekadashi","Krishna Dwadashi",
      "Krishna Trayodashi","Krishna Chaturdashi","Amavasya",
    ],
    nakshatraNames: [
      "Ashwini","Bharani","Krittika","Rohini","Mrigashirsha","Ardra",
      "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
      "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
      "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishta",
      "Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
    ],
    yogaNames: [
      "Vishkumbha","Priti","Ayushman","Saubhagya","Shobhana",
      "Atiganda","Sukarma","Dhriti","Shula","Ganda",
      "Vriddhi","Dhruva","Vyaghata","Harshana","Vajra",
      "Siddhi","Vyatipata","Variyana","Parigha","Shiva",
      "Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti",
    ],
    varaNames: [
      "Ravivara","Somavara","Mangalavara","Budhavara","Guruvara","Shukravara","Shanivara",
    ],
    rashiNames: [
      "Mesha (Aries)","Vrishabha (Taurus)","Mithuna (Gemini)","Karka (Cancer)",
      "Simha (Leo)","Kanya (Virgo)","Tula (Libra)","Vrischika (Scorpio)",
      "Dhanu (Sagittarius)","Makara (Capricorn)","Kumbha (Aquarius)","Meena (Pisces)",
    ],
    karanaNames: {
      "Bava":"Bava","Balava":"Balava","Kaulava":"Kaulava","Taitila":"Taitila",
      "Garaja":"Garaja","Vanija":"Vanija","Vishti (Bhadra)":"Vishti (Bhadra)",
      "Kimstughna":"Kimstughna","Shakuni":"Shakuni","Chatushpada":"Chatushpada","Naga":"Naga",
    },
  },

  hi: {
    appTitle:           "जैन पंचांग",
    setLocation:        "स्थान चुनें",
    tools:              "एक्सपोर्ट",
    locationTitle:      "स्थान चुनें",
    citySearch:         "शहर खोजें",
    latitude:           "अक्षांश",
    longitude:          "देशांतर",
    ayanamsa:           "अयनांश",
    save:               "सहेजें",
    cancel:             "रद्द करें",
    toolsTitle:         "निर्यात उपकरण",
    yearRangeTitle:     "वर्ष-श्रेणी निर्यात",
    startYear:          "प्रारंभ वर्ष",
    endYear:            "अंतिम वर्ष",
    format:             "प्रारूप",
    monthlyFiles:       "मासिक फ़ाइलें",
    generateRange:      "निर्यात करें",
    pdfTitle:           "PDF पंचांग",
    year:               "वर्ष",
    generatePdf:        "PDF बनाएं",
    loading:            "लोड हो रहा है…",
    error:              "त्रुटि",
    close:              "बंद करें",
    purnima:            "🌕 पूर्णिमा",
    amavasya:           "🌑 अमावस्या",
    ekadashi:           "✿ एकादशी",
    panchangHeading:    "पंचांग",
    eventsHeading:      "घटनाएं",
    samvatHeading:      "संवत",
    tithi:              "◑ तिथि",
    tithiEnds:          "तिथि समाप्ति",
    jainTithi:          "◑ जैन तिथि",
    jainTithiEnds:      "जैन तिथि समाप्ति",
    jainRef:            "जैन संदर्भ",
    nakshatra:          "✦ नक्षत्र",
    nakshatraEnds:      "नक्षत्र समाप्ति",
    pada:               "पाद",
    yoga:               "⊕ योग",
    karana:             "◗ करण",
    vara:               "☉ वार",
    moonRashi:          "☽ चंद्र राशि",
    sunRashi:           "☀ सूर्य राशि",
    hinduMonth:         "हिंदू मास",
    vikramSamvat:       "विक्रम संवत",
    viraSamvat:         "वीर निर्वाण संवत",
    sunrise:            "↑☀ सूर्योदय",
    sunset:             "↓☀ सूर्यास्त",
    moonrise:           "↑☽ चन्द्रोदय",
    moonset:            "↓☽ चन्द्रास्त",
    locationRequired:   "शहर या निर्देशांक दें।",

    weekdays:     ["रवि","सोम","मंगल","बुध","गुरु","शुक्र","शनि"],
    months:       ["जनवरी","फरवरी","मार्च","अप्रैल","मई","जून",
                   "जुलाई","अगस्त","सितंबर","अक्टूबर","नवंबर","दिसंबर"],
    hinduMonths:  ["चैत्र","वैशाख","ज्येष्ठ","आषाढ़","श्रावण",
                   "भाद्रपद","आश्विन","कार्तिक","मार्गशीर्ष","पौष","माघ","फाल्गुन"],
    tithiNames: [
      "शुक्ल प्रतिपदा","शुक्ल द्वितीया","शुक्ल तृतीया","शुक्ल चतुर्थी",
      "शुक्ल पंचमी","शुक्ल षष्ठी","शुक्ल सप्तमी","शुक्ल अष्टमी",
      "शुक्ल नवमी","शुक्ल दशमी","शुक्ल एकादशी","शुक्ल द्वादशी",
      "शुक्ल त्रयोदशी","शुक्ल चतुर्दशी","पूर्णिमा",
      "कृष्ण प्रतिपदा","कृष्ण द्वितीया","कृष्ण तृतीया","कृष्ण चतुर्थी",
      "कृष्ण पंचमी","कृष्ण षष्ठी","कृष्ण सप्तमी","कृष्ण अष्टमी",
      "कृष्ण नवमी","कृष्ण दशमी","कृष्ण एकादशी","कृष्ण द्वादशी",
      "कृष्ण त्रयोदशी","कृष्ण चतुर्दशी","अमावस्या",
    ],
    nakshatraNames: [
      "अश्विनी","भरणी","कृत्तिका","रोहिणी","मृगशिरा","आर्द्रा",
      "पुनर्वसु","पुष्य","आश्लेषा","मघा","पूर्व फाल्गुनी","उत्तर फाल्गुनी",
      "हस्त","चित्रा","स्वाती","विशाखा","अनुराधा","ज्येष्ठा",
      "मूल","पूर्व आषाढ़","उत्तर आषाढ़","श्रवण","धनिष्ठा",
      "शतभिषा","पूर्व भाद्रपद","उत्तर भाद्रपद","रेवती",
    ],
    yogaNames: [
      "विष्कुम्भ","प्रीति","आयुष्मान","सौभाग्य","शोभन",
      "अतिगण्ड","सुकर्मा","धृति","शूल","गण्ड",
      "वृद्धि","ध्रुव","व्याघात","हर्षण","वज्र",
      "सिद्धि","व्यतीपात","वरीयान","परिघ","शिव",
      "सिद्ध","साध्य","शुभ","शुक्ल","ब्रह्म","इन्द्र","वैधृति",
    ],
    varaNames: [
      "रविवार","सोमवार","मंगलवार","बुधवार","गुरुवार","शुक्रवार","शनिवार",
    ],
    // Rashi in Hindi (Devanagari)
    rashiNames: [
      "मेष","वृषभ","मिथुन","कर्क",
      "सिंह","कन्या","तुला","वृश्चिक",
      "धनु","मकर","कुंभ","मीन",
    ],
    karanaNames: {
      "Bava":"बव","Balava":"बालव","Kaulava":"कौलव","Taitila":"तैतिल",
      "Garaja":"गरजा","Vanija":"वणिजा","Vishti (Bhadra)":"विष्टि (भद्रा)",
      "Kimstughna":"किंस्तुघ्न","Shakuni":"शकुनि","Chatushpada":"चतुष्पाद","Naga":"नाग",
    },
  },
};

// Rashi key extraction — API returns "Makara (Capricorn)" or just "Meen" etc.
const RASHI_KEY_MAP = {
  Mesha:1, Vrishabha:2, Mithuna:3, Karka:4,
  Simha:5, Kanya:6, Tula:7, Vrischika:8,
  Dhanu:9, Makara:10, Kumbha:11, Meena:12, Meen:12,
};

function translateRashi(apiValue) {
  if (!apiValue) return "—";
  const key = apiValue.split(/[\s(]/)[0];
  const idx = RASHI_KEY_MAP[key];
  if (idx == null) return apiValue;
  return T[state.lang].rashiNames[idx - 1] ?? apiValue;
}

function translateKarana(apiValue) {
  if (!apiValue) return "—";
  return T[state.lang].karanaNames[apiValue] ?? apiValue;
}

// ── State ──────────────────────────────────────────────────────
const state = {
  lang:         "hi",
  year:         new Date().getFullYear(),
  month:        new Date().getMonth() + 1,
  location:     null,   // { name, lat, lon, city, ayanamsa }
  monthData:    null,
  selectedDate: null,
  dayData:      null,
};

const STORAGE_KEY = "jain_panchang_v1";

// ── i18n helpers ───────────────────────────────────────────────
function t(key) {
  return T[state.lang][key] ?? T.en[key] ?? key;
}

function tithiName(index) {
  return T[state.lang].tithiNames[index - 1] ?? "";
}

function nakshatraName(index) {
  return T[state.lang].nakshatraNames[index - 1] ?? "";
}

function yogaName(index) {
  return T[state.lang].yogaNames[index - 1] ?? "";
}

function varaName(index) {
  return T[state.lang].varaNames[index] ?? "";
}

// ── DOM refs ───────────────────────────────────────────────────
const calWeekdays    = document.getElementById("cal-weekdays");
const calDays        = document.getElementById("cal-days");
const calLoading     = document.getElementById("cal-loading");
const calMonthYear   = document.getElementById("cal-month-year");
const calSamvat      = document.getElementById("cal-samvat");
const locationDisplay= document.getElementById("location-display");
const overlay        = document.getElementById("overlay");
const dayPanel       = document.getElementById("day-panel");
const panelDate      = document.getElementById("panel-date");
const panelLocLine   = document.getElementById("panel-location-line");
const panelLoading   = document.getElementById("panel-loading");
const panelBody      = document.getElementById("panel-body");
const panelPanchang  = document.getElementById("panel-panchang");
const panelEvents    = document.getElementById("panel-events");
const panelSamvat    = document.getElementById("panel-samvat");
const locationDialog = document.getElementById("location-dialog");
const toolsDialog    = document.getElementById("tools-dialog");
const cityInput      = document.getElementById("city");
const latInput       = document.getElementById("lat");
const lonInput       = document.getElementById("lon");
const ayanamsaInput  = document.getElementById("ayanamsa");
const suggestionsBox = document.getElementById("suggestions");
const locationError  = document.getElementById("location-error");

// ── Storage ────────────────────────────────────────────────────
function saveLocation() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state.location)); } catch {}
}

function restoreLocation() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) { state.location = JSON.parse(raw); return true; }
  } catch {}
  return false;
}

// ── Apply data-i18n translations ───────────────────────────────
function applyTranslations() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const val = t(el.dataset.i18n);
    if (typeof val === "string") el.textContent = val;
  });
  document.getElementById("lang-toggle").textContent =
    state.lang === "hi" ? "EN" : "हि";
  document.title = t("appTitle");
}

// ── Calendar nav ───────────────────────────────────────────────
function renderCalNav() {
  const monthName = T[state.lang].months[state.month - 1];
  calMonthYear.textContent = `${monthName} ${state.year}`;

  if (state.monthData) {
    const vs  = state.monthData.vikram_samvat;
    const hmi = state.monthData.hindu_month_index;
    const hm  = T[state.lang].hinduMonths[hmi] ?? state.monthData.hindu_month;
    calSamvat.textContent = `${t("vikramSamvat")} ${vs}  ·  ${hm}`;
  } else {
    calSamvat.textContent = `${t("vikramSamvat")} ~${state.year + 57}`;
  }
}

// ── Weekday headers ────────────────────────────────────────────
function renderWeekdays() {
  calWeekdays.innerHTML = T[state.lang].weekdays
    .map(d => `<div class="wd-cell">${d}</div>`)
    .join("");
}

// ── Calendar cells ─────────────────────────────────────────────
// Moon phase symbol shown inline in the tithi label for special days
const CELL_SYMBOL = { purnima:"🌕", amavasya:"🌑", ekadashi:"✿" };

function renderCalDays(data) {
  const todayStr = new Date().toISOString().slice(0, 10);
  const firstWd  = new Date(state.year, state.month - 1, 1).getDay();

  let html = "";

  for (let i = 0; i < firstWd; i++) {
    html += `<div class="cal-day empty" aria-hidden="true"></div>`;
  }

  for (const day of data.days) {
    const dayNum = parseInt(day.date.slice(8, 10), 10);
    const tn = tithiName(day.tithi_index) || day.tithi_name;
    const nn = nakshatraName(day.nakshatra_index) || day.nakshatra_name;

    const cls = ["cal-day"];
    let phaseSym = "";
    if (day.is_purnima)  { cls.push("purnima");  phaseSym = CELL_SYMBOL.purnima;  }
    if (day.is_amavasya) { cls.push("amavasya"); phaseSym = CELL_SYMBOL.amavasya; }
    if (day.is_ekadashi) { cls.push("ekadashi"); phaseSym = CELL_SYMBOL.ekadashi; }
    if (day.date === todayStr)         cls.push("today");
    if (day.date === state.selectedDate) cls.push("selected");

    const symHtml = phaseSym
      ? `<span class="cell-phase" aria-hidden="true">${phaseSym}</span>`
      : "";

    const tithiTime     = day.tithi_end_time
      ? `<span class="day-tithi-time">${day.tithi_end_time}</span>` : "";
    const nakshatraTime = day.nakshatra_end_time
      ? `<span class="day-nakshatra-time">${day.nakshatra_end_time}</span>` : "";

    html += `<button class="${cls.join(" ")}" data-date="${day.date}"
               aria-label="${dayNum} — ${tn}">
      <span class="day-num">${dayNum}</span>
      ${symHtml}
      <span class="day-tithi">${tn}</span>
      <span class="day-nakshatra">${nn}</span>
      ${tithiTime}
      ${nakshatraTime}
    </button>`;
  }

  calDays.innerHTML = html;
}

// ── Month overview ─────────────────────────────────────────────
async function loadMonthOverview() {
  if (!state.location) return;

  calLoading.classList.remove("hidden");
  calDays.innerHTML = "";

  const loc    = state.location;
  const params = new URLSearchParams({
    year:     state.year,
    month:    state.month,
    ayanamsa: loc.ayanamsa || "Lahiri",
  });

  if (loc.lat != null && loc.lon != null) {
    params.set("lat", loc.lat);
    params.set("lon", loc.lon);
  } else if (loc.city) {
    params.set("city", loc.city);
  }

  try {
    const res  = await fetch(`/month-overview?${params}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || t("error"));
    state.monthData = data;
    renderCalNav();
    renderCalDays(data);
  } catch (err) {
    calDays.innerHTML =
      `<p style="padding:20px;color:#c0392b;grid-column:1/-1">${t("error")}: ${err.message}</p>`;
  } finally {
    calLoading.classList.add("hidden");
  }
}

// ── Day detail panel ───────────────────────────────────────────
function renderDl(el, rows) {
  el.innerHTML = rows
    .filter(([, v]) => v != null && v !== "")
    .map(([label, value, hi]) =>
      `<dt>${label}</dt><dd${hi ? ' class="highlight"' : ""}>${value}</dd>`)
    .join("");
}

function fmt(timeStr) { return timeStr || "—"; }

function renderDayPanel(data) {
  const p  = data.panchang;
  const ev = data.events;

  const parts = data.date.split("-");
  panelDate.textContent =
    `${parseInt(parts[2], 10)} ${T[state.lang].months[parseInt(parts[1], 10) - 1]} ${parts[0]}`;

  const vn = varaName(p.vara.index) || p.vara.name;
  panelLocLine.textContent = `${vn}  ·  ${data.location}`;

  // ── Panchang section ──
  renderDl(panelPanchang, [
    [t("tithi"),       tithiName(p.tithi.index)    || p.tithi.name,     true],
    [t("tithiEnds"),   fmt(p.tithi.ends.time)],
    [t("jainTithi"),   tithiName(p.jain_tithi.index) || p.jain_tithi.name, true],
    [t("jainTithiEnds"), fmt(p.jain_tithi.ends.time)],
    [t("jainRef"),     fmt(p.jain_tithi.reference.time)],
    [t("nakshatra"),
     `${nakshatraName(p.nakshatra.index) || p.nakshatra.name} (${t("pada")} ${p.nakshatra.pada})`,
     true],
    [t("nakshatraEnds"), fmt(p.nakshatra.ends.time)],
    [t("yoga"),        yogaName(p.yoga.index)       || p.yoga.name],
    [t("karana"),      translateKarana(p.karana.name)],
    [t("vara"),        vn],
    [t("moonRashi"),   translateRashi(p.moon_rashi)],
    [t("sunRashi"),    translateRashi(p.sun_rashi)],
  ]);

  // ── Events section ──
  renderDl(panelEvents, [
    [t("sunrise"),  fmt(ev.sunrise?.time)],
    [t("sunset"),   fmt(ev.sunset?.time)],
    [t("moonrise"), fmt(ev.moonrise?.time)],
    [t("moonset"),  fmt(ev.moonset?.time)],
  ]);

  // ── Samvat section ──
  const hmi = p.hindu_month?.index ?? 0;
  renderDl(panelSamvat, [
    [t("hinduMonth"),   T[state.lang].hinduMonths[hmi] ?? p.hindu_month?.name],
    [t("vikramSamvat"), p.vikram_samvat],
    [t("viraSamvat"),   p.vira_nirvana_samvat],
  ]);
}

async function openDayPanel(dateStr) {
  state.selectedDate = dateStr;
  document.querySelectorAll(".cal-day.selected")
    .forEach(el => el.classList.remove("selected"));
  document.querySelector(`[data-date="${dateStr}"]`)?.classList.add("selected");

  const parts = dateStr.split("-");
  panelDate.textContent =
    `${parseInt(parts[2], 10)} ${T[state.lang].months[parseInt(parts[1], 10) - 1]} ${parts[0]}`;
  panelLocLine.textContent = state.location?.name || "";

  panelBody.hidden = true;
  panelLoading.style.display = "flex";
  dayPanel.classList.add("open");
  overlay.classList.add("visible");

  const loc = state.location;
  try {
    const res = await fetch("/generate-panchang", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        date:     dateStr,
        ayanamsa: loc.ayanamsa || "Lahiri",
        lat:      loc.lat ?? null,
        lon:      loc.lon ?? null,
        city:     (loc.lat == null && loc.city) ? loc.city : null,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || t("error"));

    state.dayData = data;
    renderDayPanel(data);
    panelLoading.style.display = "none";
    panelBody.hidden = false;
  } catch (err) {
    panelLoading.style.display = "none";
    panelBody.innerHTML =
      `<p style="padding:16px;color:#c0392b">${t("error")}: ${err.message}</p>`;
    panelBody.hidden = false;
  }
}

function closeDayPanel() {
  dayPanel.classList.remove("open");
  overlay.classList.remove("visible");
  document.querySelectorAll(".cal-day.selected")
    .forEach(el => el.classList.remove("selected"));
  state.selectedDate = null;
}

// ── Location dialog ────────────────────────────────────────────
function openLocationDialog() {
  if (state.location) {
    cityInput.value     = state.location.name ?? "";
    latInput.value      = state.location.lat  ?? "";
    lonInput.value      = state.location.lon  ?? "";
    ayanamsaInput.value = state.location.ayanamsa ?? "Lahiri";
  }
  locationError.hidden = true;
  locationDialog.showModal();
}

function closeLocationDialog() {
  clearSuggestions();
  locationDialog.close();
}

function updateLocationDisplay() {
  locationDisplay.textContent = state.location?.name
    ? state.location.name.split(",")[0]
    : t("setLocation");
}

// ── Autocomplete ───────────────────────────────────────────────
let searchTimer = null;

function clearSuggestions() {
  suggestionsBox.classList.remove("visible");
  suggestionsBox.innerHTML = "";
}

cityInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  clearSuggestions();
  const q = cityInput.value.trim();
  if (q.length < 2) return;

  searchTimer = setTimeout(async () => {
    try {
      const res  = await fetch(`/search-location?q=${encodeURIComponent(q)}`);
      const data = await res.json();
      if (!data.results?.length) return;
      suggestionsBox.innerHTML = data.results
        .map(r => `<button type="button" class="suggestion"
          data-name="${r.display_name}" data-lat="${r.lat}" data-lon="${r.lon}"
          >${r.display_name}</button>`)
        .join("");
      suggestionsBox.classList.add("visible");
    } catch {}
  }, 260);
});

suggestionsBox.addEventListener("click", e => {
  const btn = e.target.closest(".suggestion");
  if (!btn) return;
  cityInput.value = btn.dataset.name;
  latInput.value  = btn.dataset.lat;
  lonInput.value  = btn.dataset.lon;
  clearSuggestions();
});

document.addEventListener("click", e => {
  if (!e.target.closest(".field")) clearSuggestions();
});

// ── Location form ──────────────────────────────────────────────
document.getElementById("location-form").addEventListener("submit", async e => {
  e.preventDefault();
  const city = cityInput.value.trim() || null;
  const lat  = latInput.value.trim()  ? parseFloat(latInput.value)  : null;
  const lon  = lonInput.value.trim()  ? parseFloat(lonInput.value)  : null;

  if (!city && (lat == null || lon == null)) {
    locationError.textContent = t("locationRequired");
    locationError.hidden = false;
    return;
  }

  locationError.hidden = true;
  state.location = {
    name:     city || `${lat?.toFixed(4)}, ${lon?.toFixed(4)}`,
    city:     (lat == null) ? city : null,
    lat, lon,
    ayanamsa: ayanamsaInput.value,
  };
  saveLocation();
  updateLocationDisplay();
  closeLocationDialog();
  await loadMonthOverview();
});

document.getElementById("location-cancel").addEventListener("click", () => {
  if (state.location) closeLocationDialog();
});

document.getElementById("location-dialog-close").addEventListener("click", () => {
  if (state.location) closeLocationDialog();
});

// ── Tools dialog ───────────────────────────────────────────────
document.getElementById("tools-btn").addEventListener("click", () => {
  document.getElementById("start-year").value = state.year;
  document.getElementById("end-year").value   = state.year;
  document.getElementById("pdf-year").value   = state.year;
  toolsDialog.showModal();
});

document.getElementById("tools-dialog-close").addEventListener("click", () => {
  toolsDialog.close();
});

// ── Range export ───────────────────────────────────────────────
document.getElementById("range-form").addEventListener("submit", async e => {
  e.preventDefault();
  const statusEl = document.getElementById("range-status");
  const filesEl  = document.getElementById("range-files");
  statusEl.textContent = t("loading");
  filesEl.innerHTML    = "";

  const loc = state.location;
  try {
    const res = await fetch("/generate-range-panchang", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        start_year: parseInt(document.getElementById("start-year").value),
        end_year:   parseInt(document.getElementById("end-year").value),
        city:       (loc?.lat == null) ? loc?.city : null,
        lat:        loc?.lat ?? null,
        lon:        loc?.lon ?? null,
        ayanamsa:   loc?.ayanamsa ?? "Lahiri",
        format:     document.getElementById("range-format").value,
        monthly:    document.getElementById("range-monthly").checked,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    statusEl.textContent = `${data.rows_generated} rows`;
    filesEl.innerHTML = data.files
      .map(f => `<a class="download-link" href="${f.download_url}">${f.name}</a>`)
      .join("");
  } catch (err) {
    statusEl.textContent = `${t("error")}: ${err.message}`;
    statusEl.style.color = "#c0392b";
  }
});

// ── PDF export ─────────────────────────────────────────────────
document.getElementById("pdf-form").addEventListener("submit", async e => {
  e.preventDefault();
  const statusEl = document.getElementById("pdf-status");
  const fileEl   = document.getElementById("pdf-file");
  statusEl.textContent = t("loading");
  fileEl.innerHTML     = "";

  const loc = state.location;
  try {
    const res = await fetch("/generate-pdf-panchang", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        year:     parseInt(document.getElementById("pdf-year").value),
        city:     (loc?.lat == null) ? loc?.city : null,
        lat:      loc?.lat ?? null,
        lon:      loc?.lon ?? null,
        ayanamsa: loc?.ayanamsa ?? "Lahiri",
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    statusEl.textContent = `${data.year} — ${data.ayanamsa}`;
    fileEl.innerHTML = `<a class="download-link" href="${data.file.download_url}">${data.file.name}</a>`;
  } catch (err) {
    statusEl.textContent = `${t("error")}: ${err.message}`;
    statusEl.style.color = "#c0392b";
  }
});

// ── Language toggle ────────────────────────────────────────────
document.getElementById("lang-toggle").addEventListener("click", () => {
  state.lang = state.lang === "hi" ? "en" : "hi";
  applyTranslations();
  renderWeekdays();
  renderCalNav();
  if (state.monthData) renderCalDays(state.monthData);
  if (state.dayData && dayPanel.classList.contains("open")) renderDayPanel(state.dayData);
  updateLocationDisplay();
});

// ── Calendar navigation ────────────────────────────────────────
document.getElementById("prev-month").addEventListener("click", () => {
  if (--state.month < 1) { state.month = 12; --state.year; }
  state.selectedDate = null;
  closeDayPanel();
  renderCalNav();
  loadMonthOverview();
});

document.getElementById("next-month").addEventListener("click", () => {
  if (++state.month > 12) { state.month = 1; ++state.year; }
  state.selectedDate = null;
  closeDayPanel();
  renderCalNav();
  loadMonthOverview();
});

// ── Day cell click ─────────────────────────────────────────────
calDays.addEventListener("click", e => {
  const cell = e.target.closest(".cal-day:not(.empty)");
  if (!cell) return;
  openDayPanel(cell.dataset.date);
});

// ── Close panel ────────────────────────────────────────────────
document.getElementById("panel-close").addEventListener("click", closeDayPanel);
overlay.addEventListener("click", closeDayPanel);
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && dayPanel.classList.contains("open")) closeDayPanel();
});

// ── Location button ────────────────────────────────────────────
document.getElementById("location-btn").addEventListener("click", openLocationDialog);

// ── Init ───────────────────────────────────────────────────────
async function init() {
  applyTranslations();
  renderWeekdays();
  renderCalNav();

  if (restoreLocation()) {
    updateLocationDisplay();
    await loadMonthOverview();
  } else {
    openLocationDialog();
  }
}

init();
