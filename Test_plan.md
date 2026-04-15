  Test 1 — FaceTime background (the actual Session-31 scenario):
  1. Start a speech-to-video generation with Hailuo.
  2. Within 5s of seeing "Generating video...", open FaceTime to someone and start an audio call.
  3. Wait 2 minutes.
  4. Return to the app.
  5. Expected: Gallery card may have flipped to the paused state briefly and resumed, OR stayed "Generating..." the whole time. Either way,
  you should see "Done!" and the completed video shortly after return. No "network connection was lost" alert.

  Test 2 — airplane mode (force CONNECTION_LOST):
  1. Start a generation.
  2. Toggle airplane mode ON immediately. Wait ~1 minute (enough for 10 fails at 5s each = 50s+).
  3. Expected: card switches to cloud-offline icon, text "Paused — will resume when back online". No alert.
  4. Toggle airplane mode OFF.
  5. Expected: NetInfo fires → resume triggers → card returns to "Generating..." → completes.

  Test 3 — force-quit during paused state:
  1. Repeat Test 2 through step 3 (card is paused).
  2. Force-quit the app via app switcher.
  3. Reopen.
  4. Expected: hydrate() restores the paused card → resume polling → completes.

  Test 4 — true server loss (404 path):
  Harder to force cleanly. Skip unless you want to verify that specific branch. Would require starting a job then triggering a backend
  republish mid-flight.

  Test 5 — happy path regression:
  1. Normal generation, no interference.
  2. Expected: same UX as before, just backed by polling instead of SSE. Progress messages may update every 5s instead of sub-second.

