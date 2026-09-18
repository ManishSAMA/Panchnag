"""Launcher: runs the Panchang Flask app with the correct working directory."""
import os
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "python_engine")
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from app import app  # noqa: E402

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
