---
name: kling-audio-test-policy
description: Dance templates ship with audio ON (audio_enabled=True). The driving video's soundtrack rides through into the gen output. Home-screen tile mutes client-side via isMuted. V3 will introduce an audio-swap step.
metadata:
  type: project
---

**Current stance (S70, user-affirmed):** All Pipeline A dance templates ship with audio ON. The driving video's audio passes through Kling Motion Control into the gen output, and plays back during detail-screen preview + generated-gen playback. The home grid mutes regardless via `isMuted` on the `<Video>` component (`mobile/app/index.tsx`) so multiple auto-playing tiles never blare music at once.

**Why:** The audio is part of the dance experience — Beat It, Smooth Criminal, Bad, Rasputin, Pinky Up all have a song that defines the move. Users expect to hear it. V3 will introduce an audio-swap step (licensed/royalty-free replacement); until then, the driving video's audio rides through. Copyright is a known V3-deferred concern, not a V2 blocker.

**How to apply:**
- **Seed:** `audio_enabled: True` in the per-template Firestore fixture.
- **Spike chain:** pass `--keep-audio` to `scripts/test_<slug>_chain.py` so the preview asset has audio.
- **Production dispatcher:** reads `template.audio_enabled`. Flip via `scripts/set_template_audio.py --template-id ... --enable/--disable` (no code change).
- **Home tile:** muted client-side, not template-controlled. Do not try to mute via `audio_enabled=False` — that would also silence the detail-screen playback.

**Superseded:** The S66/S67 "default off / spike scripts default silent" stance applied during early development. For shipping dance templates, that default no longer holds. New non-dance templates (kid content, ambient B-roll, scene-insertion) can still ship silent on a per-template basis.
