import os
import sys
import calendar
import subprocess
from datetime import date, datetime, timedelta

from astronomy import (
    local_time_to_jd,
    jd_to_local_time_string,
    get_sunrise,
    get_sunset,
    get_moonrise,
    get_moonset,
    get_planetary_longitude
)
from panchang import (
    generate_daily_panchang,
    calculate_jain_tithi_from_sunrise,
    find_chaitra_shukla_1,
    find_diwali,
    get_vikram_samvat,
    get_vira_nirvana_samvat,
    get_vara_from_date,
    get_hindu_month
)
from jain_observances.festival_service import generate_jain_festivals

# Mappings for Hindi
WEEKDAYS_HINDI = [
    "रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"
]

TITHI_NAMES_HINDI = {
    1: "प्रथमा (एकम)",
    2: "द्वितीया (दूज)",
    3: "तृतीया (तीज)",
    4: "चतुर्थी (चौथ)",
    5: "पंचमी",
    6: "षष्ठी (छठ)",
    7: "सप्तमी",
    8: "अष्टमी",
    9: "नवमी",
    10: "दशमी",
    11: "एकादशी (ग्यारस)",
    12: "द्वादशी (बारस)",
    13: "त्रयोदशी (तेरस)",
    14: "चतुर्दशी (चौदस)",
    15: "पूर्णिमा / अमावस्या"
}

MONTH_NAMES_HINDI = {
    "CHAITRA": "चैत्र", "CHAIT": "चैत्र", "CHET": "चैत्र",
    "VAISHAKHA": "वैशाख", "BAISAKH": "वैशाख", "VAISHAKH": "वैशाख",
    "JYESTHHA": "ज्येष्ठ", "JETH": "ज्येष्ठ", "JYESHTHA": "ज्येष्ठ",
    "ASHADHA": "आषाढ़", "ASAR": "आषाढ़", "ASADH": "आषाढ़", "ASHADH": "आषाढ़",
    "SHRAVANA": "श्रावण", "SAVAN": "श्रावण", "SHRAVAN": "श्रावण",
    "BHADRAPADA": "भाद्रपद", "BHADO": "भाद्रपद", "BHADRA": "भाद्रपद", "BHADARVO": "भाद्रपद",
    "ASHWIN": "आश्विन", "ASHVINA": "आश्विन", "ASO": "आश्विन", "AASO": "आश्विन",
    "KARTIKA": "कार्तिक", "KATAK": "कार्तिक", "KARTIK": "कार्तिक", "KARTAK": "कार्तिक",
    "MARGASHIRSHA": "मार्गशीर्ष", "MAGSAR": "मार्गशीर्ष", "AGRAHAYANA": "मार्गशीर्ष", "MANSIR": "मार्गशीर्ष", "MARGASHIRSA": "मार्गशीर्ष", "MAAGSAR": "मार्गशीर्ष",
    "PAUSHA": "पौष", "POSH": "पौष", "PAUSH": "पौष",
    "MAGHA": "माघ", "MAH": "माघ", "MHA": "माघ", "MAGH": "माघ", "MAHA": "माघ",
    "PHALGUNA": "फाल्गुन", "FALGUN": "फाल्गुन", "PHAGAN": "फाल्गुन", "PHALGUN": "फाल्गुन", "FAAGAN": "फाल्गुन"
}

GREG_MONTHS_HINDI = {
    (2026, 3): "मार्च 2026",
    (2026, 4): "अप्रैल 2026",
    (2026, 5): "मई 2026",
    (2026, 6): "जून 2026",
    (2026, 7): "जुलाई 2026",
    (2026, 8): "अगस्त 2026",
    (2026, 9): "सितंबर 2026",
    (2026, 10): "अक्टूबर 2026",
    (2026, 11): "नवंबर 2026",
    (2026, 12): "दिसंबर 2026",
    (2027, 1): "जनवरी 2027",
    (2027, 2): "फरवरी 2027",
    (2027, 3): "मार्च 2027",
}

TRANSLATIONS_MAP = {
    "Shri": "श्री",
    "Bhagwan": "भगवान",
    "Conception Kalyanak": "गर्भ कल्याणक",
    "Birth Kalyanak": "जन्म कल्याणक",
    "Austerity Kalyanak": "दीक्षा कल्याणक",
    "Omniscience Kalyanak": "केवलज्ञान कल्याणक",
    "Liberation Kalyanak": "मोक्ष कल्याणक",
    "Navpad Oli - Day 1 (Arihant)": "नवपद ओली - दिन 1 (अरिहंत)",
    "Navpad Oli - Day 2 (Siddha)": "नवपद ओली - दिन 2 (सिद्ध)",
    "Navpad Oli - Day 3 (Acharya)": "नवपद ओली - दिन 3 (आचार्य)",
    "Navpad Oli - Day 4 (Upadhyay)": "नवपद ओली - दिन 4 (उपाध्याय)",
    "Navpad Oli - Day 5 (Sadhu)": "नवपद ओली - दिन 5 (साधु)",
    "Navpad Oli - Day 6 (Samyag Darshan)": "नवपद ओली - दिन 6 (सम्यग् दर्शन)",
    "Navpad Oli - Day 7 (Samyag Gyan)": "नवपद ओली - दिन 7 (सम्यग् ज्ञान)",
    "Navpad Oli - Day 8 (Samyag Charitra)": "नवपद ओली - दिन 8 (सम्यग् चरित्र)",
    "Navpad Oli - Day 9 (Samyag Tapa)": "नवपद ओली - दिन 9 (सम्यग् तप)",
    "Rishabhdev (Adinath)": "ऋषभदेव (आदिनाथ)",
    "Ajitnath": "अजितनाथ",
    "Sambhavnath": "संभवनाथ",
    "Abhinandan": "अभिनंदन नाथ",
    "Sumatinath": "सुमतिनाथ",
    "Padmaprabha": "पद्मप्रभ",
    "Suparshvanath": "सुपार्श्वनाथ",
    "Chandraprabha": "चंद्रप्रभ",
    "Pushpadanta (Suvidhinath)": "पुष्पदंत (सुविधिनाथ)",
    "Sheetalnath": "शीतलनाथ",
    "Shreyansnath": "श्रेयांसनाथ",
    "Vasupujya": "वासुपूज्य",
    "Vimalnath": "विमलनाथ",
    "Anantnath": "अनंतनाथ",
    "Dharmanath": "धर्मनाथ",
    "Shantinath": "शांतिनाथ",
    "Kunthunath": "कुंथुनाथ",
    "Aranatha": "अरनाथ",
    "Arahnath": "अरनाथ",
    "Mallinath": "मल्लिनाथ",
    "Munisuvrat": "मुनिसुव्रत",
    "Naminath": "नमिनाथ",
    "Neminath": "नेमिनाथ",
    "Parshvanath": "पार्श्वनाथ",
    "Mahavira": "महावीर",
    "Mahavir": "महावीर",
}

def translate_fest(f_obj: dict) -> str:
    name_h = f_obj.get("name_hindi")
    if name_h and any("\u0900" <= c <= "\u097f" for c in name_h):
        return name_h

    title = f_obj.get("title") or f_obj.get("name") or ""
    txt = title
    for eng, hin in TRANSLATIONS_MAP.items():
        txt = txt.replace(eng, hin)

    txt = txt.replace(" Ji - ", " भगवान ").replace(" Ji", "")
    return txt

def format_time_12h(jd: float, tz_offset: float = 5.5) -> str:
    if jd <= 0.0:
        return "--"
    t_str = jd_to_local_time_string(jd, tz_offset)
    if not t_str or ":" not in t_str:
        return "--"
    try:
        parts = t_str.split(":")
        h, m = int(parts[0]), int(parts[1])
        suffix = "प्रातः" if h < 12 else "सायं"
        h12 = h % 12
        if h12 == 0:
            h12 = 12
        return f"{h12:02d}:{m:02d} {suffix}"
    except Exception:
        return t_str[:5]

def generate_hindi_pdf_calendar(out_pdf_path: str, lat: float = 26.9124, lon: float = 75.7873, tz_offset: float = 5.5, ayanamsa: str = "Lahiri", profile: str = "all"):
    # Load festivals for 2026 and 2027
    fest_2026 = generate_jain_festivals(2026, lat, lon, ayanamsa, profile)
    fest_2027 = generate_jain_festivals(2027, lat, lon, ayanamsa, profile)

    date_to_fests = {}
    for res in [fest_2026, fest_2027]:
        for f in res.get("festivals", []):
            try:
                start_d = datetime.strptime(f["start_date"], "%Y-%m-%d").date()
                end_d = datetime.strptime(f["end_date"], "%Y-%m-%d").date()
                curr_d = start_d
                while curr_d <= end_d:
                    d_str = curr_d.isoformat()
                    if d_str not in date_to_fests:
                        date_to_fests[d_str] = []
                    date_to_fests[d_str].append(f)
                    curr_d += timedelta(days=1)
            except Exception:
                pass

    # Anchor dates for Samvat
    cs1_2026 = find_chaitra_shukla_1(2026, lat, lon, tz_offset, ayanamsa)
    diwali_2026 = find_diwali(2026, lat, lon, tz_offset, ayanamsa)
    cs1_2027 = find_chaitra_shukla_1(2027, lat, lon, tz_offset, ayanamsa)
    diwali_2027 = find_diwali(2027, lat, lon, tz_offset, ayanamsa)

    # Build HTML structure
    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<title>जैन एवं वैदिक पंचांग (मार्च 2026 - मार्च 2027)</title>",
        "<style>",
        "@page { size: A4 landscape; margin: 10mm 8mm 10mm 8mm; }",
        "body { font-family: 'Segoe UI', 'Nirmala UI', 'Mangal', sans-serif; background: #fff; color: #1a1a1a; margin: 0; padding: 0; font-size: 10pt; }",
        ".month-header { background: linear-gradient(135deg, #4A154B, #6B1110); color: #fff; padding: 10px 15px; border-radius: 6px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }",
        ".month-title { font-size: 16pt; font-weight: bold; }",
        ".samvat-info { font-size: 11pt; color: #FFD700; font-weight: bold; }",
        ".panchang-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 9.5pt; table-layout: fixed; }",
        ".panchang-table th { background-color: #2C3E50; color: #ffffff; border: 1px solid #34495E; padding: 6px 4px; font-size: 9pt; text-align: center; word-wrap: break-word; }",
        ".panchang-table td { border: 1px solid #BDC3C7; padding: 5px 4px; text-align: center; vertical-align: middle; word-wrap: break-word; font-size: 9pt; }",
        ".panchang-table tr:nth-child(even) { background-color: #F8F9F9; }",
        ".panchang-table tr.sunday-row { background-color: #FDEDEC; }",
        ".panchang-table tr.parva-row { background-color: #FEF9E7; }",
        ".date-cell { font-weight: bold; color: #2C3E50; }",
        ".tithi-cell { color: #8E44AD; font-weight: 600; }",
        ".fest-cell { text-align: left !important; color: #C0392B; font-weight: 600; font-size: 8.5pt; line-height: 1.25; }",
        ".page-break { page-break-after: always; }",
        ".header-main { text-align: center; margin-bottom: 15px; border-bottom: 2px solid #8E44AD; padding-bottom: 8px; }",
        ".header-main h1 { color: #4A154B; font-size: 20pt; margin: 0 0 5px 0; }",
        ".header-main p { color: #555; margin: 0; font-size: 10pt; }",
        "</style>",
        "</head>",
        "<body>"
    ]

    html_parts.append("<div class='header-main'>")
    html_parts.append("<h1>जैन एवं वैदिक सम्पूर्ण पंचांग (मार्च 2026 – मार्च 2027)</h1>")
    html_parts.append("<p>सूर्योदय, सूर्यास्त, चंद्रोदय, चंद्रास्त, तिथि, पक्ष, वार एवं समस्त जैन/वैदिक पर्व एवं त्योहार</p>")
    html_parts.append("</div>")

    months_list = [
        (2026, 3), (2026, 4), (2026, 5), (2026, 6), (2026, 7), (2026, 8),
        (2026, 9), (2026, 10), (2026, 11), (2026, 12),
        (2027, 1), (2027, 2), (2027, 3)
    ]

    for idx, (yr, mo) in enumerate(months_list):
        greg_name = GREG_MONTHS_HINDI.get((yr, mo), f"{mo}/{yr}")
        num_days = calendar.monthrange(yr, mo)[1]

        h_months_seen = []
        rows_data = []

        for d in range(1, num_days + 1):
            c_date = date(yr, mo, d)
            c_date_str = c_date.isoformat()

            jd_start = local_time_to_jd(yr, mo, d, 0.0, tz_offset)
            jd_sr = get_sunrise(jd_start, lat, lon)
            jd_ss = get_sunset(jd_start, lat, lon)
            jd_mr = get_moonrise(jd_start, lat, lon)
            jd_ms = get_moonset(jd_start, lat, lon)

            moon_lon = get_planetary_longitude(jd_sr, 'Moon', ayanamsa)
            sun_lon = get_planetary_longitude(jd_sr, 'Sun', ayanamsa)

            panchang = generate_daily_panchang(
                jd_sr, ayanamsa, sun_lon=sun_lon, moon_lon=moon_lon, local_date=c_date
            )

            vara_idx = get_vara_from_date(c_date)
            vara_hindi = WEEKDAYS_HINDI[vara_idx]

            # Hindu Month using get_hindu_month
            h_month_raw, h_month_common, is_adhika = get_hindu_month(jd_sr, ayanamsa)
            clean_m = h_month_common.replace("Adhika ", "").replace("Adhik ", "").strip()
            h_m_h = MONTH_NAMES_HINDI.get(clean_m.upper(), clean_m)
            if is_adhika:
                h_m_h = f"अधिक {h_m_h}"

            if h_m_h and h_m_h not in h_months_seen:
                h_months_seen.append(h_m_h)

            t_idx = panchang.get("Tithi_Index", 1)
            if t_idx <= 15:
                paksha_hindi = "शुक्ल"
                tithi_num = t_idx
            else:
                paksha_hindi = "कृष्ण"
                tithi_num = t_idx - 15

            if paksha_hindi == "कृष्ण" and tithi_num == 15:
                tithi_display = "कृष्ण अमावस्या"
            elif paksha_hindi == "शुक्ल" and tithi_num == 15:
                tithi_display = "शुक्ल पूर्णिमा"
            else:
                tithi_name_h = TITHI_NAMES_HINDI.get(tithi_num, f"तिथि {tithi_num}")
                tithi_display = f"{paksha_hindi} {tithi_name_h}"

            # Vikram & Vira Nirvana Samvat
            cs1_anchor = cs1_2026 if yr == 2026 else cs1_2027
            diwali_anchor = diwali_2026 if yr == 2026 else diwali_2027
            vs_val = get_vikram_samvat(c_date, cs1_anchor)
            vns_val = get_vira_nirvana_samvat(c_date, diwali_anchor)

            # Festivals translated to Hindi
            day_fests = date_to_fests.get(c_date_str, [])
            fest_titles = []
            for f in day_fests:
                fn_h = translate_fest(f)
                if fn_h and fn_h not in fest_titles:
                    fest_titles.append(fn_h)
            fest_str = " • ".join(fest_titles) if fest_titles else ""

            sr_str = format_time_12h(jd_sr, tz_offset)
            ss_str = format_time_12h(jd_ss, tz_offset)
            mr_str = format_time_12h(jd_mr, tz_offset)
            ms_str = format_time_12h(jd_ms, tz_offset)

            rows_data.append({
                "date_str": f"{d:02d}-{mo:02d}-{yr}",
                "day_num": d,
                "vara": vara_hindi,
                "is_sunday": (vara_idx == 0),
                "h_month": h_m_h,
                "tithi": tithi_display,
                "sr": sr_str,
                "ss": ss_str,
                "mr": mr_str,
                "ms": ms_str,
                "festivals": fest_str,
                "vs": vs_val,
                "vns": vns_val
            })

        h_month_label = " / ".join(h_months_seen)
        vs_label = str(rows_data[0]["vs"])
        vns_label = str(rows_data[0]["vns"])

        html_parts.append("<div class='month-header'>")
        html_parts.append(f"<div class='month-title'>{greg_name} ({h_month_label})</div>")
        html_parts.append(f"<div class='samvat-info'>विक्रम संवत: {vs_label} | वीर निर्वाण संवत: {vns_label}</div>")
        html_parts.append("</div>")

        html_parts.append("<table class='panchang-table'>")
        html_parts.append("<thead><tr>")
        html_parts.append("<th style='width:7%;'>दिनांक</th>")
        html_parts.append("<th style='width:8%;'>वार</th>")
        html_parts.append("<th style='width:10%;'>हिंदू मास</th>")
        html_parts.append("<th style='width:15%;'>पक्ष एवं तिथि</th>")
        html_parts.append("<th style='width:9%;'>सूर्योदय</th>")
        html_parts.append("<th style='width:9%;'>सूर्यास्त</th>")
        html_parts.append("<th style='width:9%;'>चन्द्रोदय</th>")
        html_parts.append("<th style='width:9%;'>चन्द्रास्त</th>")
        html_parts.append("<th style='width:24%;'>पर्व एवं त्योहार</th>")
        html_parts.append("</tr></thead>")
        html_parts.append("<tbody>")

        for r in rows_data:
            row_cls = ""
            if r["is_sunday"]:
                row_cls = "sunday-row"
            elif r["festivals"]:
                row_cls = "parva-row"

            html_parts.append(f"<tr class='{row_cls}'>")
            html_parts.append(f"<td class='date-cell'>{r['date_str']}</td>")
            html_parts.append(f"<td>{r['vara']}</td>")
            html_parts.append(f"<td>{r['h_month']}</td>")
            html_parts.append(f"<td class='tithi-cell'>{r['tithi']}</td>")
            html_parts.append(f"<td>{r['sr']}</td>")
            html_parts.append(f"<td>{r['ss']}</td>")
            html_parts.append(f"<td>{r['mr']}</td>")
            html_parts.append(f"<td>{r['ms']}</td>")
            html_parts.append(f"<td class='fest-cell'>{r['festivals']}</td>")
            html_parts.append("</tr>")

        html_parts.append("</tbody></table>")

        if idx < len(months_list) - 1:
            html_parts.append("<div class='page-break'></div>")

    html_parts.append("</body></html>")

    html_file = out_pdf_path.replace(".pdf", ".html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    # Convert to PDF via Edge
    abs_html = os.path.abspath(html_file)
    abs_pdf = os.path.abspath(out_pdf_path)
    file_uri = "file:///" + abs_html.replace("\\", "/")

    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(edge_path):
        edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

    cmd = [edge_path, "--headless", "--disable-gpu", f"--print-to-pdf={abs_pdf}", file_uri]
    subprocess.run(cmd, capture_output=True, text=True)

    print(f"Generated PDF: {abs_pdf} (Exists: {os.path.exists(abs_pdf)}, Size: {os.path.getsize(abs_pdf) if os.path.exists(abs_pdf) else 0} bytes)")

if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    generate_hindi_pdf_calendar("output/Jain_Vedic_Panchang_March_2026_March_2027_Hindi.pdf")
