#!/usr/bin/env python3
"""Deploy latest code to xhostd via changeset API."""
import json
import urllib.request
import ssl

XHOST_TOKEN = "xh_d2zP4gObQpdT0UY0IaC98HoCzS9axSDCiCLjtAXpZiZ"
APP_ID = "0b7fc7d5-64f5-4fd4-b87e-c19702bcfb27"
CHANNEL_ID = "4e0f9aa8-72c2-4753-9891-3c1c67bbe328"
API_BASE = "https://api.xhostd.com"
BASE = "C:/Users/Yanir/Dropbox/Projects/transcriptor"


def read(path):
    with open(f"{BASE}/{path}", "r", encoding="utf-8") as f:
        return f.read()


def post(url, payload):
    ctx = ssl.create_default_context()
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {XHOST_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read())


changes = {
    "app/main.py": read("app/main.py"),
}

print(f"Uploading changeset with {len(changes)} file changes...")
for k, v in changes.items():
    sz = len(v) if v else 0
    print(f"  {'DEL' if v is None else 'UPD'} {k} ({sz} bytes)")

result = post(
    f"{API_BASE}/apps/{APP_ID}/changeset",
    {"message": "Fix SPA routing: catch-all serves index.html", "changes": changes},
)
print(f"\nChangeset result: {result}")

sha = result.get("sha") or result.get("id") or (result if isinstance(result, str) else None)
if not sha:
    print("ERROR: could not extract SHA")
    import sys; sys.exit(1)

print(f"\nDeploying SHA {sha} to channel {CHANNEL_ID}...")
deploy_result = post(
    f"{API_BASE}/apps/{APP_ID}/channels/{CHANNEL_ID}/deploy",
    {"sha": sha},
)
print(f"Deploy result: {deploy_result}")
