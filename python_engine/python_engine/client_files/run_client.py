"""Client launcher: serve the Panchang web app locally and open it in the browser."""

from __future__ import annotations

import os
import threading
import webbrowser

HOST, PORT = "127.0.0.1", 5000
URL = f"http://{HOST}:{PORT}"

# Exports are written relative to the working directory; keep them in this folder
# however the launcher was started.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app  # noqa: E402

if __name__ == "__main__":
    threading.Timer(1.5, lambda: webbrowser.open(URL)).start()
    print(f"Jain Panchang is running at {URL}. Close this window to stop it.")
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
