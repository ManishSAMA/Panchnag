import argparse
import sys
import math
import calendar
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from astronomy import local_time_to_jd, jd_to_local_time_string, get_sunrise, get_sunset, get_planetary_longitude, get_rashi_name
from panchang import calculate_jain_tithi_from_sunrise, generate_daily_panchang, get_ishta_kaala

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
        spaceAfter=15
    )
    
    cell_style = ParagraphStyle(
        name='CellStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        alignment=1 # Center
    )
    
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        elements.append(Paragraph(f"Monthly Panchang Table - {month_name} {year}", title_style))
        
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
            "Date", "Day", "Tithi\nEnd (HH:MM | Ghati-Pala)",
            "Jain Tithi\nEnd (HH:MM | Ghati-Pala)",
            "Nakshatra\nEnd (HH:MM | Ghati-Pala)", "Yoga", "Karana", 
            "Moon Rashi", "Sunrise", "Sunset"
        ]]
        
        num_days = calendar.monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            # Midnight local
            jd_start = local_time_to_jd(year, month, day, 0.0, tz_offset)
            
            jd_sr = get_sunrise(jd_start, lat, lon)
            jd_ss = get_sunset(jd_start, lat, lon)
            
            # Important: We determine the active panchang elements at Sunrise
            moon_lon = get_planetary_longitude(jd_sr, 'Moon', ayanamsa)
            sun_lon = get_planetary_longitude(jd_sr, 'Sun', ayanamsa)
            panchang = generate_daily_panchang(jd_sr, ayanamsa, sun_lon=sun_lon, moon_lon=moon_lon)
            jain_tithi = calculate_jain_tithi_from_sunrise(jd_sr, ayanamsa)
            
            rashi = get_rashi_name(moon_lon).split(' (')[0] # Get only Sanskrit name
            
            sr_str = jd_to_local_time_string(jd_sr, tz_offset)
            ss_str = jd_to_local_time_string(jd_ss, tz_offset)
            
            # Tithi End processing
            t_end_jd = panchang['Tithi_End_JD']
            t_end_str = jd_to_local_time_string(t_end_jd, tz_offset)
            tg, tp = get_ishta_kaala(t_end_jd, jd_sr)
            tithi_disp = Paragraph(f"<b>{panchang['Tithi_Name']}</b><br/>{t_end_str} ({tg}g {tp}p)", cell_style)

            j_end_jd = jain_tithi['Jain_Tithi_End_JD']
            j_end_str = jd_to_local_time_string(j_end_jd, tz_offset)
            jg, jp = get_ishta_kaala(j_end_jd, jd_sr)
            jain_tithi_disp = Paragraph(
                f"<b>{jain_tithi['Jain_Tithi_Name']}</b><br/>{j_end_str} ({jg}g {jp}p)",
                cell_style,
            )
            
            # Nakshatra End processing
            n_end_jd = panchang['Nakshatra_End_JD']
            n_end_str = jd_to_local_time_string(n_end_jd, tz_offset)
            ng, np = get_ishta_kaala(n_end_jd, jd_sr)
            nak_disp = Paragraph(f"<b>{panchang['Nakshatra_Name']}</b><br/>{n_end_str} ({ng}g {np}p)", cell_style)
            
            # Use the civil date for the row's weekday label.
            vara_idx = int((math.floor(jd_start + 0.5) + 1) % 7)
            vara_name = ['Ravivara', 'Somavara', 'Mangalavara', 'Budhavara',
                         'Guruvara', 'Shukravara', 'Shanivara'][vara_idx]
            
            row = [
                Paragraph(f"{day:02d}-{month:02d}-{year}", cell_style),
                Paragraph(vara_name, cell_style),
                tithi_disp,
                jain_tithi_disp,
                nak_disp,
                Paragraph(panchang['Yoga_Name'], cell_style),
                Paragraph(panchang['Karana_Name'], cell_style),
                Paragraph(rashi, cell_style),
                Paragraph(sr_str, cell_style),
                Paragraph(ss_str, cell_style)
            ]
            data.append(row)

        t = Table(data, colWidths=[55, 55, 100, 100, 100, 60, 60, 60, 45, 45], repeatRows=1)
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
