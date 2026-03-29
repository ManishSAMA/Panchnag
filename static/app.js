const form = document.getElementById("panchang-form");
const cityInput = document.getElementById("city");
const latInput = document.getElementById("lat");
const lonInput = document.getElementById("lon");
const dateInput = document.getElementById("date");
const ayanamsaInput = document.getElementById("ayanamsa");
const suggestionsBox = document.getElementById("suggestions");
const statusBox = document.getElementById("status");
const resultBox = document.getElementById("result");
const resultTitle = document.getElementById("result-title");
const resultSubtitle = document.getElementById("result-subtitle");
const eventsList = document.getElementById("events-list");
const panchangList = document.getElementById("panchang-list");
const rulesList = document.getElementById("rules-list");
const jsonOutput = document.getElementById("json-output");
const rangeForm = document.getElementById("range-form");
const startYearInput = document.getElementById("start-year");
const endYearInput = document.getElementById("end-year");
const rangeFormatInput = document.getElementById("range-format");
const rangeMonthlyInput = document.getElementById("range-monthly");
const rangeStatusBox = document.getElementById("range-status");
const rangeResultBox = document.getElementById("range-result");
const rangeResultTitle = document.getElementById("range-result-title");
const rangeResultSubtitle = document.getElementById("range-result-subtitle");
const rangeSummaryList = document.getElementById("range-summary-list");
const rangeFiles = document.getElementById("range-files");
const pdfForm = document.getElementById("pdf-form");
const pdfYearInput = document.getElementById("pdf-year");
const pdfStatusBox = document.getElementById("pdf-status");
const pdfResultBox = document.getElementById("pdf-result");
const pdfResultTitle = document.getElementById("pdf-result-title");
const pdfResultSubtitle = document.getElementById("pdf-result-subtitle");
const pdfSummaryList = document.getElementById("pdf-summary-list");
const pdfFile = document.getElementById("pdf-file");

let searchTimer = null;

dateInput.value = new Date().toISOString().slice(0, 10);
startYearInput.value = new Date().getFullYear();
endYearInput.value = new Date().getFullYear();
pdfYearInput.value = new Date().getFullYear();

function setStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.style.color = isError ? "#9f2f16" : "";
}

function setRangeStatus(message, isError = false) {
  rangeStatusBox.textContent = message;
  rangeStatusBox.style.color = isError ? "#9f2f16" : "";
}

function setPdfStatus(message, isError = false) {
  pdfStatusBox.textContent = message;
  pdfStatusBox.style.color = isError ? "#9f2f16" : "";
}

function renderDl(target, rows) {
  target.innerHTML = rows
    .map(([label, value]) => `<dt>${label}</dt><dd>${value ?? ""}</dd>`)
    .join("");
}

function clearSuggestions() {
  suggestionsBox.classList.remove("visible");
  suggestionsBox.innerHTML = "";
}

function buildReferenceCheckRows(items) {
  return items.map((item) => {
    const label = item.rule.includes("2h24")
      ? "Check at +2h24m"
      : item.rule.includes("2h45")
      ? "Check at +2h45m"
      : item.rule;
    return [label, `${item.reference.local} • ${item.tithi.name}`];
  });
}

async function searchLocations(query) {
  const response = await fetch(`/search-location?q=${encodeURIComponent(query)}`);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Failed to search locations.");
  }
  return data.results;
}

cityInput.addEventListener("input", () => {
  const query = cityInput.value.trim();
  clearSuggestions();

  if (query.length < 2) {
    return;
  }

  window.clearTimeout(searchTimer);
  searchTimer = window.setTimeout(async () => {
    try {
      const results = await searchLocations(query);
      if (!results.length) {
        return;
      }

      suggestionsBox.innerHTML = results
        .map(
          (item) =>
            `<button type="button" class="suggestion" data-name="${item.display_name}" data-lat="${item.lat}" data-lon="${item.lon}">${item.display_name}</button>`
        )
        .join("");
      suggestionsBox.classList.add("visible");
    } catch (error) {
      setStatus(error.message, true);
    }
  }, 250);
});

suggestionsBox.addEventListener("click", (event) => {
  const button = event.target.closest(".suggestion");
  if (!button) {
    return;
  }

  cityInput.value = button.dataset.name;
  latInput.value = button.dataset.lat;
  lonInput.value = button.dataset.lon;
  clearSuggestions();
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".field")) {
    clearSuggestions();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  setStatus("Generating Panchang...");
  resultBox.classList.add("hidden");

  const payload = {
    city: cityInput.value.trim() || null,
    lat: latInput.value.trim() || null,
    lon: lonInput.value.trim() || null,
    date: dateInput.value,
    ayanamsa: ayanamsaInput.value,
  };

  try {
    const response = await fetch("/generate-panchang", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Failed to generate Panchang.");
    }

    resultTitle.textContent = `${data.location}`;
    resultSubtitle.textContent = `${data.date} • ${data.timezone} • ${data.ayanamsa.name}`;

    renderDl(eventsList, [
      ["Sunrise", data.events.sunrise.local],
      ["Sunset", data.events.sunset.local],
      ["Moonrise", data.events.moonrise.local || "Unavailable"],
      ["Moonset", data.events.moonset.local || "Unavailable"],
      ["Next sunrise", data.events.next_sunrise.local],
    ]);

    renderDl(panchangList, [
      ["Tithi", data.panchang.tithi.name],
      ["Tithi ends", data.panchang.tithi.ends.local],
      ["Jain Tithi", data.panchang.jain_tithi.name],
      ["Jain Tithi ends", data.panchang.jain_tithi.ends.local],
      ["Jain reference", data.panchang.jain_tithi.reference.local],
      ["Nakshatra", `${data.panchang.nakshatra.name} (Pada ${data.panchang.nakshatra.pada})`],
      ["Nakshatra ends", data.panchang.nakshatra.ends.local],
      ["Yoga", data.panchang.yoga.name],
      ["Karana", data.panchang.karana.name],
      ["Vara", data.panchang.vara.name],
      ["Moon Rashi", data.panchang.moon_rashi],
    ]);

    renderDl(rulesList, [
      ["Primary rule", data.rules.primary_day_rule],
      ["Special time", data.rules.special_reference.reference.local],
      ["Special Tithi", data.rules.special_reference.tithi.name],
      ["Special Nakshatra", data.rules.special_reference.nakshatra.name],
      ...buildReferenceCheckRows(data.rules.reference_checks || []),
    ]);

    jsonOutput.textContent = JSON.stringify(data.structured, null, 2);
    resultBox.classList.remove("hidden");
    setStatus("Panchang generated.");
  } catch (error) {
    setStatus(error.message, true);
  }
});

rangeForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  setRangeStatus("Generating export files...");
  rangeResultBox.classList.add("hidden");

  const payload = {
    start_year: startYearInput.value,
    end_year: endYearInput.value,
    city: cityInput.value.trim() || null,
    lat: latInput.value.trim() || null,
    lon: lonInput.value.trim() || null,
    ayanamsa: ayanamsaInput.value,
    format: rangeFormatInput.value,
    monthly: rangeMonthlyInput.checked,
  };

  try {
    const response = await fetch("/generate-range-panchang", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Failed to generate year-range Panchang.");
    }

    rangeResultTitle.textContent = data.location.name;
    rangeResultSubtitle.textContent = `${data.start_year} - ${data.end_year} • ${data.location.timezone} • ${data.format.toUpperCase()}`;
    renderDl(rangeSummaryList, [
      ["Rows generated", data.rows_generated],
      ["Timezone", data.location.timezone_export_label],
      ["Offset used", `${data.location.timezone_export_offset_hours} hours`],
      ["Workers", data.workers],
      ["Monthly split", data.monthly ? "Yes" : "No"],
    ]);

    rangeFiles.innerHTML = data.files
      .map(
        (item) =>
          `<a class="download-link" href="${item.download_url}">${item.name}</a>`
      )
      .join("");

    rangeResultBox.classList.remove("hidden");
    setRangeStatus("Year-range Panchang generated.");
  } catch (error) {
    setRangeStatus(error.message, true);
  }
});

pdfForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  setPdfStatus("Generating PDF...");
  pdfResultBox.classList.add("hidden");

  const payload = {
    year: pdfYearInput.value,
    city: cityInput.value.trim() || null,
    lat: latInput.value.trim() || null,
    lon: lonInput.value.trim() || null,
    ayanamsa: ayanamsaInput.value,
  };

  try {
    const response = await fetch("/generate-pdf-panchang", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Failed to generate PDF Panchang.");
    }

    pdfResultTitle.textContent = data.location.name;
    pdfResultSubtitle.textContent = `${data.year} • ${data.location.timezone} • ${data.ayanamsa}`;
    renderDl(pdfSummaryList, [
      ["Year", data.year],
      ["Timezone", data.location.timezone_export_label],
      ["Offset used", `${data.location.timezone_export_offset_hours} hours`],
      ["Ayanamsa", data.ayanamsa],
    ]);
    pdfFile.innerHTML = `<a class="download-link" href="${data.file.download_url}">${data.file.name}</a>`;

    pdfResultBox.classList.remove("hidden");
    setPdfStatus("PDF Panchang generated.");
  } catch (error) {
    setPdfStatus(error.message, true);
  }
});
