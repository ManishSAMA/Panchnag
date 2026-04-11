import argparse
import sys
import calendar
from datetime import date, datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from astronomy import local_time_to_jd, jd_to_local_time_string, get_sunrise, get_sunset, get_planetary_longitude, get_rashi_name, get_sun_rashi
from export import apply_element_continuity_formatting, format_row_data
from panchang import (
    calculate_jain_tithi_from_sunrise,
    find_chaitra_shukla_1,
    find_diwali,
    generate_daily_panchang,
    get_vara_from_date,
    get_vikram_samvat,
    get_vira_nirvana_samvat,
)

def generate_pdf_calendar(year: int, out_filename: str, lat: float=26.9124, lon: float=75.7873, tz_offset: float=5.5, ayanamsa: str='Lahiri'):
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

            row = format_row_data(
                date_str=f"{year:04d}-{month:02d}-{day:02d}",
                julian_date=jd_sr,
                planets={"Sun": sun_lon, "Moon": moon_lon},
                panchang=panchang,
                jain_tithi=jain_tithi,
                sunrise_str=jd_to_local_time_string(jd_sr, tz_offset),
                sunset_str=jd_to_local_time_string(jd_ss, tz_offset),
                moonrise_str="",
                moonset_str="",
                ayanamsa_dec=0.0,
                tz_offset=tz_offset,
                tz_label="PDF",
                vikram_samvat=get_vikram_samvat(civil_date, chaitra_shukla_1),
                vira_nirvana_samvat=get_vira_nirvana_samvat(civil_date, diwali),
            )
            row["Moon_Rashi"] = get_rashi_name(moon_lon).split(' (')[0]
            row["Sun_Rashi"] = get_sun_rashi(jd_sr)
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
        elements.append(loc_info)
        elements.append(
            Paragraph(
                "<b>Legend:</b> Hindu Tithi is sunrise-based. Jain Tithi is the Tithi active 2 hours 24 minutes after sunrise.",
                styles['Normal'],
            )
        )
        elements.append(Spacer(1, 10))

        data = [[
            "Date", "Day", "Month", "Tithi",
            "Jain Tithi",
            "Nakshatra", "Yoga", "Karana",
            "Moon Rashi", "Sun Rashi", "Sunrise", "Sunset"
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

            row = [
                Paragraph(civil_date.strftime("%d-%m-%Y"), cell_style),
                Paragraph(vara_name, cell_style),
                Paragraph(row_data['Hindu_Month_Common'], cell_style),
                Paragraph(row_data['Tithi'], cell_style),
                Paragraph(row_data['Jain_Tithi_PDF'], cell_style),
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
                Paragraph(row_data['Sunset (PDF)'], cell_style)
            ]
            data.append(row)

        t = Table(data, colWidths=[55, 55, 50, 100, 100, 100, 60, 60, 60, 55, 45, 45], repeatRows=1)
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
