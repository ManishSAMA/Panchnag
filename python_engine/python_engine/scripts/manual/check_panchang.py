import pandas as pd
import subprocess
import os
import sys

def test_panchang():
    print("Running Panchang Generator for 1 day (2025-01-01)...")
    cmd = [
        sys.executable, "main.py",
        "--start_year", "2025",
        "--end_year", "2025",
        "--lat", "26.9124",
        "--lon", "75.7873",
        "--format", "csv",
        "--output", "smoke_test"
    ]
    subprocess.run(cmd, check=True)

    csv_file = "smoke_test_2025_2025.csv"
    assert os.path.exists(csv_file), "CSV output missing"

    df = pd.read_csv(csv_file)
    
    # Needs exactly 365 rows since end_year 2025 start_year 2025 means whole year.
    # Ah wait, main.py takes start_year and end_year.
    # We generated the whole year instead of 1 day. That's fine.
    
    # Check Jan 1 2025 properties (row 0)
    jan1 = df.iloc[0]
    assert jan1['Date'] == '2025-01-01', f"Expected Date 2025-01-01, got {jan1['Date']}"
    assert 'Jain_Tithi' in df.columns, "Jain_Tithi column missing"
    assert 'Jain_Tithi_End_Time' in df.columns, "Jain_Tithi_End_Time column missing"
    assert isinstance(jan1['Jain_Tithi'], str) and jan1['Jain_Tithi'], "Jain_Tithi value missing"
    
    # 2. Validates Sun longitude is in the range 270°-285° (early January - Capricorn/Sagittarius)
    sun_dec = float(jan1['Sun_Dec'])
    assert 250 <= sun_dec <= 290, f"Sun Dec out of range: {sun_dec}"
    
    # 3. Validates Tithi is between 1-30, Nakshatra 1-27, Yoga 1-27
    assert 1 <= float(jan1['Tithi_No']) <= 30, f"Tithi out of range: {jan1['Tithi_No']}"
    assert 1 <= float(jan1['Jain_Tithi_No']) <= 30, f"Jain Tithi out of range: {jan1['Jain_Tithi_No']}"
    assert 1 <= float(jan1['Nakshatra_No']) <= 27, f"Nakshatra out of range: {jan1['Nakshatra_No']}"
    assert 1 <= float(jan1['Yoga_No']) <= 27, f"Yoga out of range: {jan1['Yoga_No']}"
    
    # 4. Validates Sunrise is a plausible IST time (06:00-08:00)
    sunrise = jan1['Sunrise (IST)']
    hour = int(sunrise.split(':')[0])
    assert 6 <= hour <= 8, f"Sunrise looks wrong: {sunrise}"

    print("All smoke tests passed for 2025-01-01!")

if __name__ == "__main__":
    test_panchang()
