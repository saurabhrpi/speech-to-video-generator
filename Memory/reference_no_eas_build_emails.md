---
name: EAS does not send email on build success
description: EAS never emails when an iOS build finishes; monitor via the build URL or eas build:list, not inbox
type: reference
---

EAS does not send email notifications when a build completes — neither on success nor (per user) reliably on failure. Confirmed S53.

**How to apply:** When kicking off an `eas build`, give the user the build URL printed by the CLI and tell them to watch that page (or run `eas build:list` / `eas build:view <id>`). Do NOT instruct the user to "watch for the build email" — there is no email. Submissions (`eas submit`) may behave differently, but treat builds as URL-or-CLI-only.
