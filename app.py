#!/usr/bin/env python3
"""Local web UI for the drink recommender. Fully offline: no API keys, no network calls.

    python3 app.py            # then open http://127.0.0.1:8765
    python3 app.py --port 9000
"""
import argparse
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from drinkrec.engine import Recommender

PAGE = Path(__file__).resolve().parent / "ui" / "index.html"
REC = None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        if u.path == "/api/recommend":
            q = parse_qs(u.query)
            prompt = q.get("q", [""])[0][:300]
            try:
                servings = int(q.get("servings", ["1"])[0])
            except ValueError:
                servings = 1
            out = REC.recommend(prompt, servings=servings, n=3)
            return self._send(200, json.dumps(out, ensure_ascii=False).encode(), "application/json")
        self._send(404, b"not found", "text/plain")

    def log_message(self, *a):
        pass


def main():
    global REC
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    print("Loading FlavorGraph data...")
    REC = Recommender()
    url = f"http://127.0.0.1:{a.port}"
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"Drink recommender running at {url}  (Ctrl-C to stop)")
    if not a.no_browser:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
