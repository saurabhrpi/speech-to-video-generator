---
name: Replit container restarts trigger startup events
description: Replit health-checks and auto-scales containers, each restart fires FastAPI @app.on_event("startup") — never put expensive API calls there
type: reference
---

Replit periodically restarts deployed containers (health checks, auto-scaling, idle eviction). Each restart triggers FastAPI's `@app.on_event("startup")`.

Any expensive work gated by a Replit Secret (like `RUN_STARTUP_DIAGNOSTIC=1`) will run on EVERY container restart — potentially hourly — not just on manual deploys. This silently drained AIMLAPI credits (~$0.39/restart) for days while the user's laptop was closed.

**How to apply:** Never leave expensive startup hooks enabled in Replit Secrets after the initial diagnostic run. Treat startup events as frequent, not rare. If a one-shot diagnostic is needed, delete the secret immediately after capturing results.
