from __future__ import annotations

import calendar
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, jsonify, render_template, request, send_file

from location_service import geocode_city, search_locations
from pdf_generation_service import generate_pdf_export
from panchang_service import generate_location_panchang, resolve_location
from range_generation_service import generate_year_range_exports
from request_parsing import (
    parse_panchang_request,
    parse_pdf_generation_request,
    parse_range_generation_request,
)

GENERATED_EXPORTS: dict[str, str] = {}


def create_app() -> Flask:
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
        try:
            parsed = parse_panchang_request(request.get_json(silent=True))
            result = generate_location_panchang(
                parsed.input_date,
                city=parsed.city,
                lat=parsed.lat,
                lon=parsed.lon,
                ayanamsa_name=parsed.ayanamsa_name,
            )
            return jsonify(result)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.post("/generate-range-panchang")
    def generate_range_panchang():
        try:
            parsed = parse_range_generation_request(request.get_json(silent=True))
            result = generate_year_range_exports(
                start_year=parsed.start_year,
                end_year=parsed.end_year,
                city=parsed.city,
                lat=parsed.lat,
                lon=parsed.lon,
                ayanamsa_name=parsed.ayanamsa_name,
                output_format=parsed.output_format,
                monthly=parsed.monthly,
                workers=parsed.workers,
            )

            files = []
            for generated_file in result["files"]:
                token = uuid4().hex
                GENERATED_EXPORTS[token] = generated_file.path
                files.append(
                    {
                        "name": generated_file.name,
                        "download_url": f"/downloads/{token}",
                    }
                )

            return jsonify(
                {
                    **{k: v for k, v in result.items() if k != "files"},
                    "files": files,
                }
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.post("/generate-pdf-panchang")
    def generate_pdf_panchang():
        try:
            parsed = parse_pdf_generation_request(request.get_json(silent=True))
            result = generate_pdf_export(
                year=parsed.year,
                city=parsed.city,
                lat=parsed.lat,
                lon=parsed.lon,
                ayanamsa_name=parsed.ayanamsa_name,
            )
            token = uuid4().hex
            GENERATED_EXPORTS[token] = result["file"]["path"]

            return jsonify(
                {
                    "year": result["year"],
                    "ayanamsa": result["ayanamsa"],
                    "location": result["location"],
                    "file": {
                        "name": result["file"]["name"],
                        "download_url": f"/downloads/{token}",
                    },
                }
            )
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.get("/month-overview")
    def month_overview():
        try:
            year_str = request.args.get("year")
            month_str = request.args.get("month")

            if not year_str:
                return jsonify({"error": "Missing required parameter: year"}), 400
            if not month_str:
                return jsonify({"error": "Missing required parameter: month"}), 400

            try:
                year = int(year_str)
                month = int(month_str)
            except ValueError:
                return jsonify({"error": "year and month must be integers"}), 400

            if not (1 <= month <= 12):
                return jsonify({"error": "month must be between 1 and 12"}), 400
            if not (1900 <= year <= 2200):
                return jsonify({"error": "year must be between 1900 and 2200"}), 400

            city = request.args.get("city") or None
            lat_str = request.args.get("lat")
            lon_str = request.args.get("lon")
            ayanamsa = request.args.get("ayanamsa", "Lahiri")

            lat = float(lat_str) if lat_str else None
            lon = float(lon_str) if lon_str else None

            if not city and not (lat is not None and lon is not None):
                return jsonify({"error": "Provide either a city name or both latitude and longitude."}), 400

            location = resolve_location(city=city, lat=lat, lon=lon)

            num_days = calendar.monthrange(year, month)[1]
            days = []
            first_result = None

            for day_num in range(1, num_days + 1):
                date_str = f"{year:04d}-{month:02d}-{day_num:02d}"
                result = generate_location_panchang(
                    date_str,
                    lat=location.lat,
                    lon=location.lon,
                    ayanamsa_name=ayanamsa,
                )
                if first_result is None:
                    first_result = result

                tithi_index = result["panchang"]["tithi"]["index"]
                nakshatra_index = result["panchang"]["nakshatra"]["index"]
                vara_index = result["panchang"]["vara"]["index"]

                tithi_end_raw = result["panchang"]["tithi"]["ends"]["time"]
                nakshatra_end_raw = result["panchang"]["nakshatra"]["ends"]["time"]
                days.append({
                    "date": date_str,
                    "tithi_index": tithi_index,
                    "tithi_name": result["panchang"]["tithi"]["name"],
                    "tithi_end_time": tithi_end_raw[:5] if tithi_end_raw else "",
                    "nakshatra_index": nakshatra_index,
                    "nakshatra_name": result["panchang"]["nakshatra"]["name"],
                    "nakshatra_end_time": nakshatra_end_raw[:5] if nakshatra_end_raw else "",
                    "vara_index": vara_index,
                    "vara_name": result["panchang"]["vara"]["name"],
                    "is_purnima": tithi_index == 15,
                    "is_amavasya": tithi_index == 30,
                    "is_ekadashi": tithi_index in (11, 26),
                })

            hindu_month_index = first_result["panchang"]["hindu_month"]["index"] if first_result else 0
            hindu_month = first_result["panchang"]["hindu_month"]["name"] if first_result else ""
            vikram_samvat = first_result["panchang"]["vikram_samvat"] if first_result else year + 57

            return jsonify({
                "year": year,
                "month": month,
                "location": location.name,
                "timezone": location.timezone,
                "hindu_month": hindu_month,
                "hindu_month_index": hindu_month_index,
                "vikram_samvat": vikram_samvat,
                "days": days,
            })
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.get("/downloads/<token>")
    def download_generated_file(token: str):
        file_path = GENERATED_EXPORTS.get(token)
        if not file_path:
            abort(404)

        path = Path(file_path)
        if not path.exists():
            abort(404)

        return send_file(path, as_attachment=True, download_name=path.name)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
