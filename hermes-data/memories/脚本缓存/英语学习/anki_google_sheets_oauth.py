#!/usr/bin/env python3
"""Interactive local OAuth for the IELTS Google Sheets bridge. Secrets are never printed."""
from __future__ import annotations
import base64
import hashlib
import http.server
import json
import os
import secrets
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
import webbrowser
from pathlib import Path

SCOPE = "https://www.googleapis.com/auth/spreadsheets"
ADC = Path.home() / "AppData/Roaming/gcloud/application_default_credentials.json"
TOKEN_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "hermes" / "auth"
TOKEN_FILE = TOKEN_DIR / "google_sheets_anki_oauth.json"


def main():
    if not ADC.exists():
        print(json.dumps({"status": "blocked", "reason": "No local Google OAuth client metadata was found; use the official desktop OAuth setup."}))
        return 2
    cfg = json.loads(ADC.read_text(encoding="utf-8"))
    if cfg.get("type") != "authorized_user" or not cfg.get("client_id") or not cfg.get("client_secret"):
        print(json.dumps({"status": "blocked", "reason": "Existing local Google OAuth metadata is not a supported desktop client."}))
        return 2

    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    result = {}
    event = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            if params.get("state", [""])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"OAuth state mismatch. You may close this tab.")
                result["error"] = "state_mismatch"
            elif params.get("error"):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Google authorization was not completed. You may close this tab.")
                result["error"] = "authorization_denied"
            else:
                result["code"] = params.get("code", [""])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write("Google authorization received. You can close this tab.".encode("utf-8"))
            event.set()

        def log_message(self, format, *args):
            return

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    server.timeout = 1
    port = server.server_address[1]
    redirect_uri = f"http://127.0.0.1:{port}/"
    auth_params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "include_granted_scopes": "true",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(auth_params)
    auth_url_file = TOKEN_DIR / "google_sheets_authorization_url.txt"
    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    auth_url_file.write_text(auth_url, encoding="utf-8")
    print(json.dumps({"status": "authorization_ready", "authorization_url_file": str(auth_url_file), "instruction": "Open the local authorization URL in a browser and approve only the Google Sheets scope. Do not send passwords or codes in chat."}))

    deadline = time.time() + 300
    while time.time() < deadline and not event.is_set():
        server.handle_request()
    server.server_close()
    if not event.is_set() or not result.get("code"):
        print(json.dumps({"status": "authorization_not_completed", "reason": result.get("error", "timeout") }))
        return 3

    token_data = urllib.parse.urlencode({
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "code": result["code"],
        "code_verifier": verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }).encode()
    request = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            tokens = json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            error_body = json.load(exc)
            error_code = error_body.get("error", "oauth_http_error")
        except Exception:
            error_code = "oauth_http_error"
        print(json.dumps({"status": "token_exchange_failed", "http_status": exc.code, "error": error_code}))
        return 4
    except Exception as exc:
        print(json.dumps({"status": "token_exchange_failed", "error": type(exc).__name__}))
        return 4

    if not tokens.get("access_token") or not tokens.get("refresh_token"):
        print(json.dumps({"status": "token_exchange_incomplete", "has_access_token": bool(tokens.get("access_token")), "has_refresh_token": bool(tokens.get("refresh_token"))}))
        return 5

    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    saved = {
        "type": "authorized_user",
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
        "refresh_token": tokens["refresh_token"],
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": [SCOPE],
    }
    TOKEN_FILE.write_text(json.dumps(saved), encoding="utf-8")
    try:
        os.chmod(TOKEN_FILE, 0o600)
    except OSError:
        pass
    print(json.dumps({"status": "authorized", "scope": SCOPE, "credential_file": str(TOKEN_FILE), "token_values_printed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
