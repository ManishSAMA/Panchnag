import json
import urllib.error
import urllib.request

if __name__ == '__main__':
    url = 'http://127.0.0.1:5000/generate-jain-festivals'
    req = urllib.request.Request(url, method='POST')
    req.add_header('Content-Type', 'application/json')
    data = json.dumps({'year': 2026, 'lat': 28.6139, 'lon': 77.2090, 'ayanamsa': 'Lahiri', 'profile': 'shwetambar_murtipujak_tapagachchha'})
    try:
        response = urllib.request.urlopen(req, data=data.encode('utf-8'))
        result = json.loads(response.read())
        bhak_fests = [f for f in result['festivals'] if 'Bhaktambar' in f['name']]
        print(f"Found {len(bhak_fests)} Bhaktambar Vrat intervals:")
        for f in bhak_fests:
            info = []
            if f.get('has_kshaya'):
                info.append("KSHAYA ENFORCED")
            if f.get('has_vriddhi'):
                info.append("VRIDDHI EXTENSION")
                
            extra = f" ({', '.join(info)})" if info else ""
            print(f"{f['name']}: {f['start_date']} to {f['end_date']} [{f['duration_days']} days]{extra}")
    except urllib.error.HTTPError as e:
        print('HTTP Error', e.code, e.read().decode())
