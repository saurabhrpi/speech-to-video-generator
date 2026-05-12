---
name: Replit Workspace Secrets vs Deployment Secrets — two separate stores
description: Replit splits secrets into Workspace Secrets (shells + dev runs) and Deployment Secrets (deployed process only). They do NOT auto-sync. Workspace pane can be hard to find or missing in some projects; if so, use `export` + a file path env var as a one-off workaround for shell smoke tests.
type: reference
---

Replit has **two separate secret stores** for any given project. Setting a secret in one does NOT propagate to the other.

| Store | Visible to | Where to find |
|---|---|---|
| **Workspace Secrets** | Workspace shells, dev runs (`Run` button) | Left sidebar → Tools → Secrets (🔒 icon). May also live behind a "+" / "Add tool" menu. |
| **Deployment Secrets** | Deployed/published process only | Deployments → [your deployment] → Configuration → Secrets |

**Symptoms of mixing them up:**
- Production app works fine but a workspace shell `python script.py` says env var unset.
- `env | grep MYVAR` in shell returns nothing despite the secret being "set" somewhere in Replit.

**Diagnostic command** (run in Replit shell):
```bash
env | grep -E "^(GOOGLE|VERTEX|FIREBASE|OPENAI|MINIMAX)" | sed 's/=.*/=<set>/'
```
Lists which secret names ARE injected into this shell, without leaking values. If a name is missing here, it's not in Workspace Secrets.

**Other gotchas:**
- **New shell required after adding a secret.** Existing shell sessions don't pick up secrets retroactively. Close + reopen the Shell tab.
- **Values stored literally.** Don't wrap with `'…'` or `"…"` — Replit stores the surrounding quotes as part of the value (unlike `.env` files where dotenv strips them).
- **Workspace Secrets pane may be missing entirely** in some Replit project tiers / older project setups — there's no left-sidebar entry. (Verified S62 on the speech-to-video project — Tools menu had no Secrets entry.)

**Workaround when Workspace Secrets pane is inaccessible** (e.g., for a one-off shell smoke test):

```bash
export SIMPLE_VAR=value

# For multi-line / JSON secrets, write to a tempfile and use a path-based env var
nano /tmp/key.json   # paste content, Ctrl+O, Enter, Ctrl+X
chmod 600 /tmp/key.json
export VAR_THAT_TAKES_PATH=/tmp/key.json

python scripts/smoke.py
rm /tmp/key.json    # clean up after — file is plaintext private key
```

Design any client/script that takes credentials to support **both** an inline-JSON env var AND a path-based env var fallback. The Vertex client + `scripts/test_vertex_auth.py` follow this pattern (`VERTEX_SERVICE_ACCOUNT_JSON` preferred, `VERTEX_SERVICE_ACCOUNT_PATH` fallback) — same for Firebase Admin (`FIREBASE_SERVICE_ACCOUNT_JSON` / `_PATH`).

**Verified S62 (2026-05-11).** Replit Workspace Secrets pane missing on this project; shell smoke completed via export + /tmp file using `VERTEX_SERVICE_ACCOUNT_PATH`.
