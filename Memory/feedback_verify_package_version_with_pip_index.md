---
name: Verify package versions with pip index, not WebFetch
description: For PyPI / npm / any package-manager version lookups, run the package-manager CLI (`pip index versions <pkg>`, `npm view <pkg> versions`) instead of trusting WebFetch summaries of PyPI/npm pages — WebFetch hallucinates versions and the wrong pin breaks install on first run
type: feedback
---

When deciding what version floor to pin for a package, the source of truth is the package manager's own index — NOT a WebFetch on a registry page.

**Why:** S62 (2026-05-10). I asked WebFetch for the latest `google-genai` version; it confidently reported `2.0.1` released `May 9, 2026`. Both fabricated — the actual latest per `pip index versions google-genai` was `1.47.0`. The bad pin (`>=2.0.0`) made it into `requirements.txt`, broke install on the user's first run, and burned a round-trip. WebFetch's summary of PyPI pages can read stale text, misparse version tables, or simply confabulate plausible-looking version numbers and dates.

**How to apply:**
- **Python / PyPI:** `pip index versions <package>` — first line of output is the actual latest stable.
- **JavaScript / npm:** `npm view <package> versions --json` (list) or `npm view <package> version` (latest).
- **Ruby / RubyGems:** `gem search -er <package>`.
- **Rust / crates.io:** `cargo search <package>` (top line) or `cargo info <package>`.
- Use direct registry JSON APIs as a second-source check if needed (e.g., `https://pypi.org/pypi/<pkg>/json`) — these are structured data, less prone to LLM misread than HTML.
- Use WebFetch only for human-prose changelogs / release notes / breaking-change summaries — not version numbers.
- If you've already written a WebFetch-derived version pin into a file, run the CLI check before declaring the work done.
