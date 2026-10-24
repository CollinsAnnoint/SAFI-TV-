#!/usr/bin/env python3
"""
SAFI TV+ Public Static Server (Render-safe)

Serves the SAFI TV+ web app from ./web as static files only.

SECURITY: This file has NO /proxy endpoint. Do not add one.
The Booster/proxy is home LAN only and must never be published to the internet.

Run locally:
    python3 server-public.py          (port 8000)
    PORT=8080 python3 server-public.py

Deploy on Render as a Web Service:
    Start command: python server-public.py
    Render injects $PORT automatically.
"""
import http.server, socketserver, os, sys, mimetypes

WEB_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
PORT = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8000))

# Security headers for all responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "media-src 'self' blob:; "
        "object-src 'none'; "
        "base-uri 'self';"
    ),
}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_ROOT, **kwargs)

    def end_headers(self):
        for k, v in SECURITY_HEADERS.items():
            self.send_header(k, v)
        super().end_headers()

    def translate_path(self, path):
        # Prevent directory traversal — never serve outside WEB_ROOT
        path = super().translate_path(path)
        web_root_abs = os.path.abspath(WEB_ROOT)
        path_abs = os.path.abspath(path)
        if not path_abs.startswith(web_root_abs + os.sep) and path_abs != web_root_abs:
            self.send_error(404, "Not found")
            return ""
        return path

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, format, *args):
        # Keep logs minimal
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))

if __name__ == "__main__":
    class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    with Server(("0.0.0.0", PORT), Handler) as httpd:
        print(f"SAFI TV+ static server running on http://0.0.0.0:{PORT}  (web root: {WEB_ROOT})", flush=True)
        httpd.serve_forever()