JAIN PANCHANG
=============

Requirements
------------
- Windows 10 or 11
- Python 3.11, 3.12, 3.13, or 3.14 from https://www.python.org/downloads/
  (during install, tick "Add python.exe to PATH")
- Internet on the first run (to install packages) and for city search

Start
-----
Double-click start.bat.

The first run sets everything up (a few minutes). After that it starts in
seconds. Your browser opens at http://127.0.0.1:5000. Keep the black window
open while you use the app. Close it to stop.

What you can do (all inside the app)
------------------------------------
- Daily Panchang, Choghadiya, Muhurta and the month calendar
- Jain festivals for the three Shwetambar traditions
- Settings > Export Panchang Data:
    * PDF Export (Single Year)
    * Hindi Calendar PDF (हिन्दी पंचांग)
    * CSV / Excel / JSON for a range of years
  Set your location first. The ayanamsa you pick in Settings is used for exports too.

Hindi Calendar PDF
------------------
Microsoft Edge converts the calendar to PDF. If Edge is missing you get an
.html file instead: open it in your browser and press Ctrl+P, then choose
"Save as PDF".

Troubleshooting
---------------
- "Python (3.11, 3.12, 3.13, or 3.14) is required": install Python as described above.
- Setup failed: check your internet connection and run start.bat again.
- Port 5000 already in use: close any other Jain Panchang window first.
- To reinstall from scratch, delete the folder panchang_app\.venv and run
  start.bat again.
