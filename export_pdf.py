import argparse
import sys
import calendar
from datetime import date, datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from astronomy import local_time_to_jd, jd_to_local_time_string, get_sunrise, get_sunset, get_planetary_longitude, get_rashi_name, get_sun_rashi
from export import apply_element_continuity_formatting, format_row_data
from panchang import (
    calculate_bhadra_kaal,
    calculate_panchak_kaal,
    calculate_jain_tithi_from_sunrise,
    calculate_rahu_kaal,
    find_chaitra_shukla_1,
    find_diwali,
    generate_daily_panchang,
    get_vara_from_date,
    get_vikram_samvat,
    get_vira_nirvana_samvat,
)

def generate_pdf_calendar(year: int, out_filename: str, lat: float=26.9124, lon: float=75.7873, tz_offset: float=5.5, ayanamsa: str='Lahiri', profile: str='shwetambar_murtipujak_tapagachchha'):
    doc = SimpleDocTemplate(
        out_filename, 
        pagesize=landscape(letter),
        rightMargin=30, leftMargin=30, 
        topMargin=30, bottomMargin=30
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        alignment=1, # Center
        fontSize=16,
        spaceAfter=5
    )

    subtitle_style = ParagraphStyle(
        name='SubtitleStyle',
        parent=styles['Normal'],
        alignment=1,
        fontSize=12,
        spaceAfter=10,
    )

    cell_style = ParagraphStyle(
        name='CellStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=1 # Center
    )
    
    chaitra_shukla_1 = find_chaitra_shukla_1(year, lat, lon, tz_offset, ayanamsa)
    diwali = find_diwali(year, lat, lon, tz_offset, ayanamsa)

    from jain_festival_service import generate_jain_festivals
    jain_fest_data = generate_jain_festivals(year, lat, lon, ayanamsa, profile)
    date_to_fests = {}
    for f in jain_fest_data.get("festivals", []):
        start_d = datetime.strptime(f["start_date"], "%Y-%m-%d").date()
        end_d = datetime.strptime(f["end_date"], "%Y-%m-%d").date()
        curr_d = start_d
        while curr_d <= end_d:
            d_str = curr_d.isoformat()
            if d_str not in date_to_fests:
                date_to_fests[d_str] = []
            date_to_fests[d_str].append(f)
            curr_d += timedelta(days=1)

    all_rows: list[dict] = []
    for month in range(1, 13):
        num_days = calendar.monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            jd_start = local_time_to_jd(year, month, day, 0.0, tz_offset)
            jd_sr = get_sunrise(jd_start, lat, lon)
            jd_ss = get_sunset(jd_start, lat, lon)

            moon_lon = get_planetary_longitude(jd_sr, 'Moon', ayanamsa)
            sun_lon = get_planetary_longitude(jd_sr, 'Sun', ayanamsa)
            civil_date = date(year, month, day)
            panchang = generate_daily_panchang(
                jd_sr,
                ayanamsa,
                sun_lon=sun_lon,
                moon_lon=moon_lon,
                local_date=civil_date,
            )
            jain_tithi = calculate_jain_tithi_from_sunrise(jd_sr, ayanamsa)

            jd_next_day_start = local_time_to_jd(year, month, day, 0.0, tz_offset) + 1.0
            jd_next_sr = get_sunrise(jd_next_day_start, lat, lon)
            bhadra = calculate_bhadra_kaal(jd_sr, jd_next_sr, ayanamsa)
            panchak_raw = calculate_panchak_kaal(jd_sr, jd_next_sr, ayanamsa)
            panchak_segs = panchak_raw["windows"]

            civil_date_str = f"{year:04d}-{month:02d}-{day:02d}"
            day_fests = date_to_fests.get(civil_date_str, [])
            fests_list = [f for f in day_fests if f["category"] != "parva"]
            parva_list = [f for f in day_fests if f["category"] == "parva"]

            row = format_row_data(
                date_str=civil_date_str,
                julian_date=jd_sr,
                planets={"Sun": sun_lon, "Moon": moon_lon},
                panchang=panchang,
                jain_tithi=jain_tithi,
                sunrise_str=jd_to_local_time_string(jd_sr, tz_offset),
                sunset_str=jd_to_local_time_string(jd_ss, tz_offset),
                moonrise_str="",
                moonset_str="",
                ayanamsa_dec=0.0,
                ayanamsa_name=ayanamsa,
                tz_offset=tz_offset,
                tz_label="PDF",
                vikram_samvat=get_vikram_samvat(civil_date, chaitra_shukla_1),
                vira_nirvana_samvat=get_vira_nirvana_samvat(civil_date, diwali),
                bhadra_kaal=bhadra,
                panchak_segments=panchak_segs,
                jain_festivals=fests_list,
                jain_parva_tithis=parva_list,
                festival_profile=profile,
                festival_review_needed=any(f.get("status") == "review_needed" for f in day_fests),
            )
            row["Moon_Rashi"] = get_rashi_name(moon_lon).split(' (')[0]
            row["Sun_Rashi"] = get_sun_rashi(jd_sr)
            rahu = calculate_rahu_kaal(jd_sr, jd_ss, panchang["Vara_Index"])
            row["Rahu_Kaal"] = (
                jd_to_local_time_string(rahu["start_jd"], tz_offset)[:5]
                + "–"
                + jd_to_local_time_string(rahu["end_jd"], tz_offset)[:5]
            )
            row["Bhadra_Segments"] = bhadra
            row["Panchak_Segments"] = panchak_segs
            row["Jain_Fests_PDF"] = day_fests
            all_rows.append(row)

    for i, row in enumerate(all_rows):
        prev_rashi = all_rows[i - 1]["Sun_Rashi"] if i > 0 else None
        curr_rashi = row["Sun_Rashi"]
        row["Sun_Rashi_Display"] = (
            f"{prev_rashi} \u2192 {curr_rashi}" if prev_rashi and prev_rashi != curr_rashi
            else curr_rashi
        )

    formatted_rows = apply_element_continuity_formatting(all_rows, tz_offset=tz_offset)

    # Collect unique lunar months per Gregorian month, in order of first appearance.
    month_lunar_months: dict[int, list[tuple[str, str]]] = {}
    for m in range(1, 13):
        m_rows = [r for r in all_rows if datetime.fromisoformat(r["Date"]).month == m]
        seen: dict[tuple[str, str], None] = {}
        for r in m_rows:
            key = (r['Hindu_Month'], r['Hindu_Month_Common'])
            seen[key] = None  # dict preserves insertion order, deduplicates
        month_lunar_months[m] = list(seen.keys())

    for month in range(1, 13):
        month_name = calendar.month_name[month]
        month_rows_pre = [r for r in all_rows if datetime.fromisoformat(r["Date"]).month == month]

        unique_months = month_lunar_months[month]  # [(Sanskrit, Common), ...]

        # Detect if the first lunar month on this page continues from the previous page.
        prev_last = month_lunar_months.get(month - 1, [])
        is_continuation = bool(unique_months and prev_last and unique_months[0][0] == prev_last[-1][0])
        contd_suffix = " (contd.)" if is_continuation else ""

        common_str   = " / ".join(common   for _, common   in unique_months)
        sanskrit_str = " / ".join(sanskrit for sanskrit, _ in unique_months)

        vs_years = sorted({r['Vikram_Samvat'] for r in month_rows_pre})
        vns_years = sorted({r['Vira_Nirvana_Samvat'] for r in month_rows_pre})
        vs_str = '/'.join(str(y) for y in vs_years)
        vns_str = '/'.join(str(y) for y in vns_years)

        elements.append(Paragraph(
            f"{common_str} {year}{contd_suffix}  —  {month_name}  |  {vs_str} VS  |  {vns_str} VNS",
            title_style,
        ))
        elements.append(Paragraph(f"({sanskrit_str})", subtitle_style))
        
        # Header Info
        loc_info = Paragraph(f"<b>Location:</b> Lat {lat}, Lon {lon} | <b>Timezone:</b> UTC+{tz_offset} | <b>Ayanamsa:</b> {ayanamsa}", styles['Normal'])
        loc_info_profile = Paragraph(f"<b>Festival Profile:</b> {profile.replace('_', ' ').title()}", styles['Normal'])
        elements.append(loc_info)
        elements.append(loc_info_profile)
        elements.append(
            Paragraph(
                "<b>Legend:</b> Hindu Tithi is sunrise-based. Jain Tithi is the Tithi active 2 hours 24 minutes after sunrise. "
                "<font color='#7D3C98'>* Indicates festival date has a source conflict / review needed.</font>",
                styles['Normal'],
            )
        )
        elements.append(Spacer(1, 10))

        data = [[
            "Date", "Day", "Month", "Tithi",
            "Jain Tithi",
            "Nakshatra", "Yoga", "Karana",
            "Moon Rashi", "Sun Rashi", "Sunrise", "Sunset", "Rahu Kaal", "Bhadra Kaal", "Panchak Kaal"
        ]]

        month_rows = [
            row for row in formatted_rows
            if datetime.fromisoformat(row["Date"]).month == month
        ]
        for row_data in month_rows:
            civil_date = datetime.fromisoformat(row_data["Date"]).date()
            vara_idx = get_vara_from_date(civil_date)
            vara_name = ['Ravivara', 'Somavara', 'Mangalavara', 'Budhavara',
                         'Guruvara', 'Shukravara', 'Shanivara'][vara_idx]

            # Format Bhadra segments as compact multiline summaries
            bhadra_segs = row_data.get("Bhadra_Segments", [])
            if bhadra_segs:
                bhadra_summaries = []
                for w in bhadra_segs:
                    start_t = jd_to_local_time_string(w["start_jd"], tz_offset)[:5]
                    end_t = jd_to_local_time_string(w["end_jd"], tz_offset)[:5]
                    bhadra_summaries.append(
                        f"{start_t}–{end_t}<br/><font size='5'>{w['residence']} ({w['risk_level']})</font>"
                    )
                bhadra_str = "<br/>".join(bhadra_summaries)
            else:
                bhadra_str = "None"

            # Format Panchak segments as compact time range
            panchak_segs = row_data.get("Panchak_Segments", [])
            if panchak_segs:
                panchak_parts = []
                for pw in panchak_segs:
                    start_t = jd_to_local_time_string(pw["start_jd"], tz_offset)[:5]
                    end_t   = jd_to_local_time_string(pw["end_jd"],   tz_offset)[:5]
                    panchak_parts.append(
                        f"{start_t}–{end_t}<br/><font size='5'>{pw['nakshatra']}</font>"
                    )
                panchak_str = "<br/>".join(panchak_parts)
            else:
                panchak_str = "None"

            # Format Jain Tithi + compact festivals list
            jain_tithi_display = row_data['Jain_Tithi_PDF']
            day_fests = row_data.get("Jain_Fests_PDF", [])
            if day_fests:
                fest_short_names = []
                for f in day_fests:
                    name = f["name"]
                    if "Ayambil Oli" in name:
                        name = "Oli"
                    elif "Paryushan Start" in name:
                        name = "Paryushan"
                    elif "Samvatsari" in name:
                        name = "Samvatsari"
                    elif "Mahavir Janma" in name:
                        name = "Mahavir Jayanti"
                    if f.get("status") == "review_needed":
                        name += "*"
                    fest_short_names.append(name)
                deduped_names = []
                for n in fest_short_names:
                    if n not in deduped_names:
                        deduped_names.append(n)
                jain_tithi_display += f"<br/><font size='5' color='#7D3C98'>({', '.join(deduped_names)})</font>"

            row = [
                Paragraph(civil_date.strftime("%d-%m-%Y"), cell_style),
                Paragraph(vara_name, cell_style),
                Paragraph(row_data['Hindu_Month_Common'], cell_style),
                Paragraph(row_data['Tithi'], cell_style),
                Paragraph(jain_tithi_display, cell_style),
                Paragraph(row_data['Nakshatra'], cell_style),
                Paragraph(row_data['Yoga'], cell_style),
                Paragraph(
                    f"{row_data['Karana']}<br/>"
                    f"<font size='6'>{row_data['Karana Start']} – {row_data['Karana End']}</font>",
                    cell_style,
                ),
                Paragraph(row_data['Moon_Rashi'], cell_style),
                Paragraph(row_data['Sun_Rashi_Display'], cell_style),
                Paragraph(row_data['Sunrise (PDF)'], cell_style),
                Paragraph(row_data['Sunset (PDF)'], cell_style),
                Paragraph(row_data.get('Rahu_Kaal', ''), cell_style),
                Paragraph(bhadra_str, cell_style),
                Paragraph(panchak_str, cell_style),
            ]
            data.append(row)

        t = Table(data, colWidths=[50, 50, 40, 75, 75, 75, 45, 50, 45, 45, 35, 35, 40, 60, 55], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#ecf0f1')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        
        elements.append(t)
        elements.append(PageBreak())
        
    doc.build(elements)
    print(f"Generated PDF: {out_filename}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Export Panchang to a Monthly PDF Table")
    parser.add_argument('--year', type=int, required=True, help="Year to generate (e.g. 2025)")
    parser.add_argument('--out', type=str, default='panchang_tables.pdf', help="Output filename")
    args = parser.parse_args()
    
    generate_pdf_calendar(args.year, args.out)
