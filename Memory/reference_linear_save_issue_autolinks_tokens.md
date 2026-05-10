---
name: Linear save_issue auto-links team-prefix tokens
description: Linear MCP save_issue parses plain `<PREFIX>-<N>` tokens (e.g. AIV-12) in the description and auto-resolves them to inline issue references on save
type: reference
---

The Linear MCP `save_issue` tool parses plain `<TEAM-PREFIX>-<N>` tokens (e.g. `AIV-12`) inside the `description` field and auto-resolves them to inline issue-reference markup (`<issue id="<uuid>">AIV-12</issue>`) on save. You don't need to construct the markup yourself.

**Verified S61 (2026-05-09):** Sent description text `Blocked on AIV-12 (R2 wiring) ...`. Follow-up `get_issue` returned that span as `<issue id="2da753c1-281d-49e1-9228-dc73e7d7c456">AIV-12</issue>`. Linear had auto-linked the bare token server-side.

**Implication.** A bulk substitution like `SPE-NN` → `AIV-NN` over plain body text would land cleanly on save — Linear re-resolves token strings. No need to fabricate `<issue id="…">…</issue>` markup.

**What this does NOT prove (still open if you ever need it):**
- Whether existing `<issue id="X">VISIBLE_TEXT</issue>` markup is preserved byte-exactly through a no-op round-trip (`get` → unchanged `save`).
- Whether visible text inside existing markup can be rewritten without breaking the link.
- Round-trip behavior for other inline forms (mentions, document refs, attachments).

For full bulk-rewrite confidence on issues that already contain inline markup, do a no-op round-trip on a sample issue first (covered in the discussion that produced this memory — see S61 conversation re: SPE→AIV opportunistic vs bulk).
