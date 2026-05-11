#!/usr/bin/env python3
"""
Lightweight proxy server for NVIDIA Daro Chatbot web UI.
Serves static files and proxies streaming chat requests to NVIDIA NIM API.
Accessible on local network for multi-device usage.
"""

import json
import http.server
import urllib.request
import urllib.error
import socket
import os
import sys

PORT = 8080
# Load .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

API_KEY = os.environ.get("NVIDIA_API_KEY", "")
BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

MIME_TYPES = {
    ".html": "text/html",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".webp": "image/webp",
}


def get_local_ip():
    """Get the local network IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class ChatProxyHandler(http.server.BaseHTTPRequestHandler):
    """Handles static files and proxies /api/chat to NVIDIA NIM."""

    def log_message(self, fmt, *args):
        client = self.client_address[0]
        print(f"  {client}  {fmt % args}")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            path = "/index.html"

        file_path = os.path.join(STATIC_DIR, path.lstrip("/"))
        if not os.path.isfile(file_path):
            self.send_error(404, "File not found")
            return

        ext = os.path.splitext(file_path)[1]
        content_type = MIME_TYPES.get(ext, "application/octet-stream")

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        with open(file_path, "rb") as f:
            self.wfile.write(f.read())

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        nim_payload = json.dumps({
            "model": payload.get("model", "meta/llama-3.1-8b-instruct"),
            "messages": payload.get("messages", []),
            "stream": True,
            "max_tokens": payload.get("max_tokens", 4096),
            "temperature": payload.get("temperature", 0.7),
        }).encode("utf-8")

        req = urllib.request.Request(
            BASE_URL,
            data=nim_payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
                "Accept": "text/event-stream",
            },
        )

        try:
            response = urllib.request.urlopen(req, timeout=120)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": error_body}).encode())
            return
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            for line in response:
                self.wfile.write(line)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            response.close()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    from http.server import ThreadingHTTPServer

    local_ip = get_local_ip()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), ChatProxyHandler)

    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║        NVIDIA Daro Chatbot — Web Server  🚀          ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()
    print(f"  🖥  Local:    http://localhost:{PORT}")
    print(f"  📱 Network:  http://{local_ip}:{PORT}")
    print()
    print(f"  📁 Serving:  {STATIC_DIR}")
    print(f"  🔑 API:      {BASE_URL}")
    print()
    print("  💡 Any device on the same Wi-Fi/LAN can open the")
    print(f"     Network URL above to use the chatbot.")
    print()
    print("  ⏹  Press Ctrl+C to stop")
    print("  " + "─" * 54)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
