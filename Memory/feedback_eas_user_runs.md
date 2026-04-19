---
name: EAS inspect/submit — user runs
description: User executes `eas build:view`, `eas submit`, and similar inspection/submission EAS CLI commands personally — give them the command, don't run it yourself
type: feedback
---

For EAS CLI commands that inspect state or submit to Apple (`eas build:view`, `eas submit`, likely `eas build` when interactive), give the user the exact command and wait for them to paste the output back. Do NOT execute these yourself.

**Why:** In Session 38 the user rejected both `eas build:view <id>` and `eas submit --platform ios --latest --non-interactive` tool calls and asked to run them personally. These commands touch external systems (Apple, Expo servers, TestFlight) and often need interactive auth/credential prompts; user wants hands-on control over these boundary actions.

**How to apply:**
- Fire-and-forget queueing like `eas build --profile production --non-interactive --no-wait` is fine for me to run (precedent from same session — user accepted it).
- Status checks (`eas build:view`, `eas build:list`, `eas submit:list`) → output the command in a code block, wait for paste.
- Submissions (`eas submit ...`) → output the command, wait for paste.
- Don't build a polling loop around `eas build:view` — user will check manually and tell me when it's done.
- Same pattern likely applies to `eas credentials`, `eas device:*`, and anything that opens a browser or prompts for Apple ID.
