---
name: Replit republish grace period (and curl race window)
description: Republishing on Replit doesn't instantly kill the old container — there's a ~5 min grace period before SIGTERM. During that window, traffic can hit either container, so a single failed verification curl post-republish is NOT proof the deploy failed.
type: reference
---

Republishing a Replit deployment does NOT immediately kill the old process. The old container continues running for a grace period (~5 minutes observed) before receiving SIGTERM. During that window, in-flight work (daemon threads, API calls, video generation) keeps executing and burning credits.

**Incident (Apr 10, 2026):** an orphan Hailuo pipeline kept generating transition videos for ~5 min after republish before receiving SIGTERM mid-transition 6→7.

**Implication for cost control:** if an orphan job is burning expensive credits and you need to stop it urgently, republishing alone isn't instant. Stopping the deployment entirely may be the only guaranteed immediate kill. Factor this grace period into cost estimates when orphan jobs are running.

**Implication for post-deploy verification (S54):** during the same ~5 min handover window, a curl from outside can hit EITHER the old or the new container. We saw this verifying the Privacy Policy update — first `curl https://speech-2-video.ai/privacy | grep "OpenAI receives"` returned empty (hit old container, old text); a second curl ~30s later returned the full new text. **A single failed grep right after republish is not proof the deploy didn't work.** Either retry after 30-60s, or send a few requests in a row and take the majority/latest as truth.
