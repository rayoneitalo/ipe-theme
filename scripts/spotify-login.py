#!/usr/bin/env python3
"""Connect the Ipê theme to Spotify. Optional: the theme works without it.

Runs Spotify's Authorization Code flow with PKCE, so no client secret exists
anywhere. The browser redirect only reaches 127.0.0.1, the request is checked
against a one-time state value, and the refresh token goes straight into the
macOS Keychain. No token is printed or written to a file.

  python3 scripts/spotify-login.py --client-id <id>            show what's playing
  python3 scripts/spotify-login.py --client-id <id> --control  also play/pause/next (Premium)
  python3 scripts/spotify-login.py --logout                    remove the stored tokens
"""

import argparse
import base64
import hashlib
import http.server
import json
import re
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

SERVICE = "ipe-theme-spotify"
SECURITY = "/usr/bin/security"
PORT = 8898
REDIRECT_URI = f"http://127.0.0.1:{PORT}/callback"
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
READ_SCOPES = ["user-read-currently-playing"]
CONTROL_SCOPES = ["user-read-playback-state", "user-modify-playback-state"]
CLIENT_ID_SHAPE = re.compile(r"^[0-9a-f]{32}$")
TOKEN_SHAPE = re.compile(r"^[A-Za-z0-9._~-]+$")
LOGIN_TIMEOUT_S = 180

PAGE = """<!doctype html><meta charset="utf-8"><title>Ipê · Spotify</title>
<body style="background:#0b0c0e;color:#e9ecef;font:16px Menlo,monospace;display:grid;place-items:center;height:100vh;margin:0">
<p>{}</p></body>"""


def keychain_store(account: str, value: str) -> None:
    if not TOKEN_SHAPE.match(value):
        sys.exit("Spotify returned a value in an unexpected format. Nothing was stored.")
    # stdin keeps the value out of the process argument list, where other
    # local processes could read it.
    subprocess.run(
        [SECURITY, "-i"],
        input=f"add-generic-password -U -s {SERVICE} -a {account} -w {value}\n",
        text=True,
        capture_output=True,
        check=True,
    )


def keychain_delete(account: str) -> bool:
    done = subprocess.run([SECURITY, "delete-generic-password", "-s", SERVICE, "-a", account], capture_output=True)
    return done.returncode == 0


def wait_for_code(state: str) -> dict:
    result: dict = {}

    class Callback(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            url = urllib.parse.urlparse(self.path)
            if url.path != "/callback":
                self.send_error(404)
                return
            query = urllib.parse.parse_qs(url.query)
            if not secrets.compare_digest(query.get("state", [""])[0], state):
                result["error"] = "the answer did not match this login"
                text = "Login refused: this answer did not come from the login you started. Close this tab and run the script again."
            elif "error" in query:
                result["error"] = query["error"][0][:60]
                text = "Spotify login was cancelled. You can close this tab."
            else:
                result["code"] = query.get("code", [""])[0]
                text = "Spotify is connected to the Ipê theme. You can close this tab."
            body = PAGE.format(text).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args) -> None:
            pass

    server = http.server.HTTPServer(("127.0.0.1", PORT), Callback)
    server.timeout = 5
    deadline = time.monotonic() + LOGIN_TIMEOUT_S
    try:
        while not result and time.monotonic() < deadline:
            server.handle_request()
    finally:
        server.server_close()
    return result


def exchange(client_id: str, code: str, verifier: str) -> dict:
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "code_verifier": verifier,
    }).encode()
    request = urllib.request.Request(TOKEN_URL, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        try:
            reason = json.load(err).get("error", "")
        except Exception:
            reason = ""
        sys.exit(f"Spotify refused the login ({err.code} {reason}). Nothing was stored.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Connect the Ipê theme to Spotify (optional).")
    parser.add_argument("--client-id", help="Client ID of your app on developer.spotify.com")
    parser.add_argument("--control", action="store_true", help="also allow play/pause/next (needs Spotify Premium)")
    parser.add_argument("--no-browser", action="store_true", help="print the login link instead of opening it")
    parser.add_argument("--logout", action="store_true", help="remove the stored Spotify tokens from the Keychain")
    args = parser.parse_args()

    if sys.platform != "darwin":
        sys.exit("The Spotify link stores its token in the macOS Keychain, so it needs macOS.")

    if args.logout:
        removed = [keychain_delete("refresh_token"), keychain_delete("client_id")]
        print("Removed the Spotify tokens from the Keychain." if any(removed) else "No Spotify tokens were stored.")
        print("To revoke access on Spotify's side too: https://www.spotify.com/account/apps/")
        return

    if not args.client_id or not CLIENT_ID_SHAPE.match(args.client_id):
        sys.exit("Pass --client-id with the 32-character Client ID from your app on developer.spotify.com.")

    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(24)
    scopes = READ_SCOPES + (CONTROL_SCOPES if args.control else [])
    url = AUTHORIZE_URL + "?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": args.client_id,
        "scope": " ".join(scopes),
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
    })

    print(f"Log in to Spotify within {LOGIN_TIMEOUT_S // 60} minutes:\n{url}\n")
    if not args.no_browser:
        webbrowser.open(url)

    result = wait_for_code(state)
    if not result.get("code"):
        sys.exit(f"Login did not finish ({result.get('error', 'timed out')}). Nothing was stored.")

    tokens = exchange(args.client_id, result["code"], verifier)
    refresh = tokens.get("refresh_token")
    if not isinstance(refresh, str):
        sys.exit("Spotify did not return a refresh token. Nothing was stored.")
    keychain_store("client_id", args.client_id)
    keychain_store("refresh_token", refresh)
    print(f"Connected. Spotify granted: {tokens.get('scope', '')}")
    print("In Claude, run /ipe spotify to start showing what's playing.")


if __name__ == "__main__":
    main()
