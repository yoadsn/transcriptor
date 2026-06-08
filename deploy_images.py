#!/usr/bin/env python3
"""Upload data_sample images to xhost as base64 .b64 files, and update install.sh to decode them."""
import base64
import json
import os
import ssl
import urllib.request

XHOST_TOKEN = "xh_d2zP4gObQpdT0UY0IaC98HoCzS9axSDCiCLjtAXpZiZ"
APP_ID = "0b7fc7d5-64f5-4fd4-b87e-c19702bcfb27"
CHANNEL_ID = "4e0f9aa8-72c2-4753-9891-3c1c67bbe328"
API_BASE = "https://api.xhostd.com"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data_sample")

INSTALL_SH = '''#!/bin/sh
set -e
pip install -e .
# Decode base64-encoded images in data_sample/
python3 -c "
import base64, os
d = 'data_sample'
if os.path.exists(d):
    for fn in os.listdir(d):
        if fn.endswith('.b64'):
            src = os.path.join(d, fn)
            dst = os.path.join(d, fn[:-4])
            with open(src) as f:
                raw = base64.b64decode(f.read())
            with open(dst, 'wb') as f:
                f.write(raw)
            print('decoded', dst)
"
'''

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
print(f"Encoding {len(images)} images...")

changes = {"install.sh": INSTALL_SH}
for img in images:
    path = os.path.join(DATA_DIR, img)
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    key = f"data_sample/{img}.b64"
    changes[key] = encoded
    print(f"  {key}: {len(encoded)} chars")

print(f"\nUploading changeset ({len(changes)} files)...")
result = post(f"{API_BASE}/apps/{APP_ID}/changeset",
              {"message": "Add demo images as base64; update install.sh to decode on deploy", "changes": changes})
print(f"Changeset: {result}")

sha = result.get("sha") or result.get("id")
print(f"\nDeploying {sha}...")
deploy = post(f"{API_BASE}/apps/{APP_ID}/channels/{CHANNEL_ID}/deploy", {"sha": sha})
print(f"Deploy result: {deploy}")
