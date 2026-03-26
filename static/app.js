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

let searchTimer = null;

dateInput.value = new Date().toISOString().slice(0, 10);

function setStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.style.color = isError ? "#9f2f16" : "";
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
    ]);

    jsonOutput.textContent = JSON.stringify(data.structured, null, 2);
    resultBox.classList.remove("hidden");
    setStatus("Panchang generated.");
  } catch (error) {
    setStatus(error.message, true);
  }
});
