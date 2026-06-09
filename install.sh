#!/bin/sh
set -e

uv run alembic upgrade head

# Decode base64-encoded images into data_sample/
python3 -c "
import base64, os
d = 'data_sample'
os.makedirs(d, exist_ok=True)
for fn in sorted(os.listdir(d)):
    if fn.endswith('.b64'):
        dst = os.path.join(d, fn[:-4])
        if not os.path.exists(dst):
            with open(os.path.join(d, fn)) as f:
                data = base64.b64decode(f.read().strip())
            with open(dst, 'wb') as f:
                f.write(data)
            print('decoded', dst)
"

# Seed demo data (idempotent)
uv run python scripts/seed_demo.py
