#!/usr/bin/env python3
"""Deploy data_sample images (base64) + updated backend files to xhostd."""
import base64
import json
import os
import ssl
import urllib.request

XHOST_TOKEN = "xh_d2zP4gObQpdT0UY0IaC98HoCzS9axSDCiCLjtAXpZiZ"
APP_ID = "0b7fc7d5-64f5-4fd4-b87e-c19702bcfb27"
CHANNEL_ID = "4e0f9aa8-72c2-4753-9891-3c1c67bbe328"
API_BASE = "https://api.xhostd.com"
BASE = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE, "data_sample")


def read(path):
    with open(os.path.join(BASE, path), encoding="utf-8") as f:
        return f.read()


def post(url, payload):
    ctx = ssl.create_default_context()
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {XHOST_TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read())


images = sorted(f for f in os.listdir(DATA_DIR) if f.lower().endswith((".jpg", ".jpeg")))
print(f"Encoding {len(images)} images from data_sample/...")

changes = {
    "install.sh": read("install.sh"),
    "app/main.py": read("app/main.py"),
    "scripts/seed_demo.py": read("scripts/seed_demo.py"),
}

for img in images:
    path = os.path.join(DATA_DIR, img)
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    key = f"data_sample/{img}.b64"
    changes[key] = encoded
    print(f"  {key}: {len(encoded):,} chars")

print(f"\nUploading changeset ({len(changes)} files)...")
result = post(
    f"{API_BASE}/apps/{APP_ID}/changeset",
    {"message": "Add demo images and seed 10-line pages", "changes": changes},
)
print(f"Changeset: {result}")

sha = result.get("sha") or result.get("id")
if not sha:
    import sys; print("ERROR: no SHA"); sys.exit(1)

print(f"\nDeploying {sha}...")
deploy = post(f"{API_BASE}/apps/{APP_ID}/channels/{CHANNEL_ID}/deploy", {"sha": sha})
print(f"Deploy result: {deploy}")
