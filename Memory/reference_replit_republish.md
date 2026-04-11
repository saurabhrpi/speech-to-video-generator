---
name: Replit republish grace period
description: Republishing on Replit doesn't instantly kill the old container — there's a ~5 min grace period before SIGTERM
type: reference
---

Republishing a Replit deployment does NOT immediately kill the old process. The old container continues running for a grace period (~5 minutes observed) before receiving SIGTERM. During that window, in-flight work (daemon threads, API calls, video generation) keeps executing and burning credits.

**Incident:** On Apr 10, 2026, an orphan Hailuo pipeline kept generating transition videos for ~5 min after republish before receiving SIGTERM mid-transition 6→7.

**How to apply:** If an orphan job is burning expensive credits and you need to stop it urgently, republishing alone isn't instant. Stopping the deployment entirely may be the only guaranteed immediate kill. Factor this grace period into cost estimates when orphan jobs are running.
