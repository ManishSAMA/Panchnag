# Hindi Excel / CSV / JSON export

Status: implemented (approved 2026-10-10).

## Goal

The range export (`/generate-range-panchang`, `main.py`) gains a language choice.
With `language: "hi"` the same 70 columns are written, with Hindi headers and Hindi
text values. Numbers, dates and times stay in Latin digits, 24-hour clock, so Excel
can still sort and filter. Hindi only (no bilingual columns).

First use: Trenton, NJ (40.2203 N, 74.7658 W, US Eastern), Jan-Dec 2027.

## Design

- New pure module `hindi_export.py`: `translate_rows_to_hindi(rows) -> list[dict]`.
  It maps each row's keys to Hindi headers and translates text values, and is
  applied to the formatted rows just before `export_data` when language is `hi`.
- Reuses existing tables: `WEEKDAYS_HINDI`, `MONTH_NAMES_HINDI`, `TITHI_NAMES_HINDI`,
  `translate_fest` (hindi_calendar_pdf.py), `NAME_HI` (hindi_observance_map.py).
- New tables: nakshatra (27), yoga (27), karana (11), rashi (12), planets (9),
  common month names (12), Bhadra residence/risk, profiles (3).
- Festival names: the festival index already knows each festival's `name_hindi`;
  carry it to the row so the Hindi column uses the registry's Hindi name, falling
  back to `translate_fest`.
- Request: `language` = `en` (default) | `hi` in `RangeGenerationRequest`, validated
  in `request_parsing.py`. CLI: `--language {en,hi}`. Web UI: a language select
  (English / हिंदी) beside the range-export format select.
- File name gets a `_hi` suffix: `panchang_2027_2027_hi.xlsx`.
- English output is unchanged.

## Headers

| English | Hindi |
|---|---|
| Date | दिनांक |
| Vikram_Samvat / Vira_Nirvana_Samvat | विक्रम संवत / वीर निर्वाण संवत |
| Julian_Date | जूलियन दिनांक |
| Weekday | वार |
| Hindu_Month / Hindu_Month_Common | हिंदू मास / मास (प्रचलित) |
| Tithi_No / Tithi | तिथि क्रमांक / तिथि |
| Jain_Tithi_No / Jain_Tithi / Jain_Tithi_End_Time | जैन तिथि क्रमांक / जैन तिथि / जैन तिथि समाप्ति |
| Nakshatra_No / Nakshatra / Nakshatra_Pada | नक्षत्र क्रमांक / नक्षत्र / नक्षत्र चरण |
| Yoga_No / Yoga | योग क्रमांक / योग |
| Karana_No / Karana / Karana Start / Karana End | करण क्रमांक / करण / करण प्रारंभ / करण समाप्ति |
| Has_Bhadra / Bhadra_Windows / Bhadra_Max_Risk | भद्रा / भद्रा काल / भद्रा अधिकतम जोखिम |
| Has_Panchak / Panchak_Window | पंचक / पंचक काल |
| Jain_Festivals / Jain_Parva_Tithis | जैन पर्व / जैन पर्व तिथि |
| Festival_Profile / Festival_Review_Needed | परंपरा / समीक्षा आवश्यक |
| Sunrise / Sunset / Moonrise / Moonset (EST) | सूर्योदय / सूर्यास्त / चंद्रोदय / चंद्रास्त (EST) |
| {Planet}_Rashi / _Ansha / _Kala / _Vikala | {ग्रह} राशि / अंश / कला / विकला |
| Ayanamsa_Dec / Ayanamsa_DMS | अयनांश (दशमलव) / अयनांश (अंश-कला-विकला) |

Planets: सूर्य, चंद्र, मंगल, बुध, गुरु, शुक्र, शनि, राहु, केतु.

## Values

- Weekday: रविवार ... शनिवार.
- Rashi columns (numbers 1-12 today) become names: मेष, वृषभ, मिथुन, कर्क, सिंह,
  कन्या, तुला, वृश्चिक, धनु, मकर, कुंभ, मीन.
- Month: चैत्र ... फाल्गुन (Agrahayana = मार्गशीर्ष), "अधिक" prefix for Adhika.
  Common (Hindi forms, not the Gujarati-style English column): चैत, बैसाख, जेठ,
  आषाढ़, सावन, भादों, क्वार, कातिक, अगहन, पूस, माघ, फागुन.
- Tithi: as in the Hindi PDF, e.g. "कृष्ण दशमी [2027-01-02 03:54]".
- Nakshatra: अश्विनी, भरणी, कृत्तिका, रोहिणी, मृगशिरा, आर्द्रा, पुनर्वसु, पुष्य,
  आश्लेषा, मघा, पूर्वा फाल्गुनी, उत्तरा फाल्गुनी, हस्त, चित्रा, स्वाति, विशाखा,
  अनुराधा, ज्येष्ठा, मूल, पूर्वाषाढ़ा, उत्तराषाढ़ा, श्रवण, धनिष्ठा, शतभिषा,
  पूर्वा भाद्रपद, उत्तरा भाद्रपद, रेवती.
- Yoga: विष्कुम्भ, प्रीति, आयुष्मान, सौभाग्य, शोभन, अतिगण्ड, सुकर्मा, धृति, शूल,
  गण्ड, वृद्धि, ध्रुव, व्याघात, हर्षण, वज्र, सिद्धि, व्यतीपात, वरीयान, परिघ, शिव,
  सिद्ध, साध्य, शुभ, शुक्ल, ब्रह्म, इन्द्र, वैधृति.
- Karana: बव, बालव, कौलव, तैतिल, गर, वणिज, विष्टि (भद्रा), किंस्तुघ्न, शकुनि,
  चतुष्पद, नाग.
- True/False: हाँ / नहीं. "None" windows: कोई नहीं.
- Bhadra window: "15:13–03:54 (निवास: पाताल, राशि: तुला, जोखिम: निम्न)".
  Residence: स्वर्ग / पृथ्वी / पाताल. Risk: उच्च / निम्न.
- Panchak window: nakshatra in Hindi.
- Profile: श्वेतांबर मूर्तिपूजक तपागच्छ / श्वेतांबर स्थानकवासी / श्वेतांबर तेरापंथी.

## Tests (TDD, behaviour through public API)

- A Hindi export has the same number of rows and columns as the English one.
- No header and no text cell contains Latin letters, apart from the time-zone label
  and the date/time stamps. This is the invariant that catches a missed table entry.
- Every nakshatra / yoga / karana / rashi / tithi name has a Hindi entry.
- Festival names use the registry's `name_hindi`.
- `language` is validated (`en` | `hi`), defaults to `en`; English output unchanged.
- UI: the language select reaches the request (tests_ui smoke).

Translation status: machine-drafted, like hindi_observance_map.py.
