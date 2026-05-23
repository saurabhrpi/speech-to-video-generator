---
name: kling-runtime-config-commands
description: Operational CLI commands for flipping Kling runtime model/mode without a code deploy (AIV-101). Global config and per-template overrides both editable via Firestore, propagation ~30s.
metadata:
  type: reference
---

**What this is:** No-deploy switching of `mode` + `model_name` for the runtime Kling Motion Control call. Backend resolves per request through a 3-layer chain (per-template override → global Firestore config → hardcoded fallback), with a 30s in-memory cache. AIV-101 ([linear](https://linear.app/speech-to-video/issue/AIV-101)).

**Files:**
- `src/speech_to_video/utils/runtime_config.py` — Firestore read + TTL cache + fallback
- `src/speech_to_video/services/video_service.py:VideoService._resolve_kling_settings` — resolver used by both Pipeline A and B call sites
- `scripts/set_kling_runtime.py` — global CLI
- `scripts/set_template_kling_override.py` — per-template CLI

**Common flows:**

```bash
# See what's currently in effect globally
.venv/bin/python scripts/set_kling_runtime.py --show

# Flip global preset
.venv/bin/python scripts/set_kling_runtime.py --preset v3-pro
.venv/bin/python scripts/set_kling_runtime.py --preset v3-std
.venv/bin/python scripts/set_kling_runtime.py --preset v2-6-pro
.venv/bin/python scripts/set_kling_runtime.py --preset v2-6-std

# Or explicit (any subset)
.venv/bin/python scripts/set_kling_runtime.py --model kling-v3 --mode pro
.venv/bin/python scripts/set_kling_runtime.py --mode pro            # leaves model unchanged

# Inspect a template's override state
.venv/bin/python scripts/set_template_kling_override.py \
    --template-id viral-dances-smooth-criminal --show

# Pin a template to specific settings (wins over global)
.venv/bin/python scripts/set_template_kling_override.py \
    --template-id viral-dances-smooth-criminal --model kling-v2-6 --mode std

# Override only one dimension; the other still follows global
.venv/bin/python scripts/set_template_kling_override.py \
    --template-id viral-dances-smooth-criminal --model kling-v2-6

# Clear; template falls back to global
.venv/bin/python scripts/set_template_kling_override.py \
    --template-id viral-dances-smooth-criminal --clear
```

**Resolution order (per request):**
1. Per-template override (`template["kling_model_override"]` / `template["kling_mode_override"]` in the Firestore template doc).
2. Global runtime config (`config/runtime` doc, fields `kling_model_name` + `kling_mode`).
3. Hardcoded fallback in `runtime_config._DEFAULTS` — currently `kling-v2-6 + std`. Used ONLY when Firestore is unreachable or the doc is missing.

**Propagation latency:** writes are immediate to Firestore; backend pick-up takes ≤30s (cache TTL). Each backend instance has its own cache, so multiple replicas may briefly disagree.

**Recommended A/B pattern:**
1. Flip global to candidate (e.g. `--preset v3-pro`).
2. Wait 30s.
3. Run a real gen on the iPhone.
4. If one template regresses, pin it via per-template override rather than rolling back global (that's the whole point of the split).
5. Full revert: `--preset v2-6-std` for global + `--clear` for any per-template pins.

**Costs to remember when flipping:** v3 ~2× v2.6 (Kling-side); pro ~2× std. So `v3-pro` is ~$2/gen vs `v2-6-std` ~$0.50. Per-template `credit_cost` is 23-25, retail $2.30-$2.50; margin shifts accordingly. See `[[kling-v3-model-string-and-cost]]`, `[[kling-mode-split]]`.

**Cautions:**
- Don't bypass the resolver by re-introducing hardcoded `mode=` / `model_name=` at the call sites. The whole point of AIV-101 is one source of truth.
- The hardcoded fallback is intentional defense-in-depth — never delete it. If Firestore goes down mid-request, the request should still succeed at baseline.
- This is global state. A flip affects EVERY user's next gen within 30s. Test on a Replit branch deploy first if you're unsure, or pin to a single template via override before going global.

See related: `[[kling-mode-split]]` (the pre-AIV-101 hardcoded mode split this replaces), `[[kling-v3-model-string-and-cost]]` (cost math), `[[kling-mc-aspect-inherits-nbp]]` (model-choice quality interactions).
