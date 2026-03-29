from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, jsonify, render_template, request, send_file

from location_service import geocode_city, search_locations
from pdf_generation_service import generate_pdf_export
from panchang_service import generate_location_panchang
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
