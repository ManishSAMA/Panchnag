import subprocess
import time
import json
import urllib.request


p = subprocess.Popen(['.\\venv\\Scripts\\python.exe', 'app.py'])
time.sleep(3) 

req = urllib.request.Request('http://127.0.0.1:5000/generate-jain-festivals', method='POST')
req.add_header('Content-Type', 'application/json')
data = json.dumps({"year": 2026, "lat": 28.61, "lon": 77.2, "profile": "shwetambar_murtipujak_tapagachchha"}).encode('utf-8')
try:
    with urllib.request.urlopen(req, data=data) as response:
        print("Warmup done! Status:", response.status)
except Exception as e:
    print("Warmup failed:", e)
