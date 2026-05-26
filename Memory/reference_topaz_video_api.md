---
name: topaz-video-api
description: Topaz Video API = fast/cheap cloud driver-upscale (replaces slow Replicate). Client scripts/upscale_topaz.py. How to find ACTUAL credits charged (GET /video/history → transactions commit), cost data, and the Kling-input-size re-encode gotcha.
metadata:
  type: reference
---

# Topaz Video API — driver upscale + how to check credits charged

Fast/cheap cloud upscaler for Kling driving videos (runs on Topaz's GPUs, ~1 min actual despite a ~5 min estimate). Replaces the slow Replicate Real-ESRGAN path (~60 min + re-time/re-mux). Confirmed end-to-end S79 (River + Give It Up).

- **Client:** `scripts/upscale_topaz.py` — its docstring has the full API flow (create → accept → multipart PUT → complete-upload → poll status). Base `https://api.topazlabs.com`, auth `X-API-Key` from `TOPAZ_API_KEY` in `.env`. Default model `prob-4` (Proteus v4).
- **OpenAPI spec (authoritative over the prose docs):** `docs/api-notes/topaz-video-api.yaml`.
- **Topaz preserves timing + audio** (`audioTransfer: Copy`, no fps change) → feed the output straight to Kling, NO re-time/re-mux (unlike Replicate).

## How to find ACTUAL credits charged for a request

The `POST /video/` create and `GET /video/{id}/status` responses only give the **estimate** range (`estimates.cost = [lo, hi]`). They do NOT report the final charge. There is **no** `GET /video/{id}` base endpoint (404).

The actual charge is in **`GET /video/history`** → `result[]` → each item's **`transactions`** array of `{operation, amount}` where operation ∈ `reserve | commit | rollback`. **Actual credits charged = sum of `commit` − sum of `rollback`.**

```python
import os, requests
from dotenv import load_dotenv; load_dotenv('.env', override=True)
h = {'X-API-Key': os.environ['TOPAZ_API_KEY'], 'Accept': 'application/json'}
d = requests.get('https://api.topazlabs.com/video/history', headers=h, params={'limit': 20}).json()
for it in d['result']:                      # NOTE: top key is 'result' (+ 'nextCursor')
    tx = it.get('transactions') or []
    charged = sum(t['amount'] for t in tx if t['operation'] == 'commit') \
            - sum(t['amount'] for t in tx if t['operation'] == 'rollback')
    print(it['id'], it['status'], 'charged:', charged)
```

## Cost (confirmed S79)

- Starter pay-as-you-go: **$0.12/credit**.
- A ~15s clip, **2× upscale** (1284×~1384 → 2568×~2768), `prob-4` = **9 credits actual** (~$1.08). Actual `commit` landed at the **low end** of the 9–10 estimate, so the estimate is reliable (slightly conservative). Cancel before processing → full refund; cancel mid-processing → partial refund (rollback transaction).

## Gotcha — re-encode before feeding Kling

Topaz output is **~90 Mbps** (e.g. 178 MB for 15s @ 2k). Kling Motion Control **rejects** an over-large driving video (`code 1201 "Video size is too large"`, S79 River). Re-encode to ~14 Mbps first (keeps 2k resolution; The Hills' working 2k driver was ~19 Mbps / 36 MB):

```bash
ffmpeg -i topaz_2k.mp4 -c:v libx264 -preset slow -b:v 14M -maxrate 18M -bufsize 28M \
  -pix_fmt yuv420p -movflags +faststart -c:a copy driver_2k_14m.mp4
```

fps does NOT need normalizing for a trackable source (the River 30fps experiment was a red herring — see [[kling-min-continuous-valid-motion]]). Upscaling helps detail/hands on an already-trackable driver; it does NOT rescue an untrackable source.

Related: [[replicate-video-retimes]] (the slow path this replaces), [[kling-min-continuous-valid-motion]].
