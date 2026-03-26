from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from location_service import geocode_city, search_locations
from panchang_service import generate_location_panchang

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/search-location")
def search_location():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": []})

    try:
        return jsonify({"results": search_locations(query)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.get("/get-coordinates")
def get_coordinates():
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"error": "Missing required query parameter: city"}), 400

    try:
        result = geocode_city(city)
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.post("/generate-panchang")
def generate_panchang():
    payload = request.get_json(silent=True) or {}

    input_date = payload.get("date")
    city = payload.get("city")
    lat = payload.get("lat")
    lon = payload.get("lon")
    ayanamsa_name = payload.get("ayanamsa", "Lahiri")

    if not input_date:
        return jsonify({"error": "Missing required field: date"}), 400

    try:
        lat_value = float(lat) if lat not in (None, "") else None
        lon_value = float(lon) if lon not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify({"error": "Latitude and longitude must be numeric."}), 400

    try:
        result = generate_location_panchang(
            input_date,
            city=city,
            lat=lat_value,
            lon=lon_value,
            ayanamsa_name=ayanamsa_name,
        )
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True)
