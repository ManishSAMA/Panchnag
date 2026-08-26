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
        print('Found', len(result['panchang']['jain_festivals']), 'days with festivals')
    except urllib.error.HTTPError as e:
        print('HTTP Error', e.code, e.read().decode())
