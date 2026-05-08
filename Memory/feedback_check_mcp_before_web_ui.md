---
name: Check for an MCP server before defaulting to web-UI testing
description: Before recommending the user manually test an AI provider via web UI, check whether that provider publishes an MCP server — programmatic access via MCP saves manual work and lets Claude run the test directly.
type: feedback
---

When evaluating any AI provider (image/video/audio generation, tooling, anything an agent might drive), check whether they publish an MCP server BEFORE recommending manual web-UI testing.

**Why:** Session 56 spike — I dove into reading Higgsfield docs/pricing and lining up a manual web-UI test plan for the user. The user then asked, "why don't you use the built-in Higgsfield MCP?" Higgsfield publishes an official hosted MCP at `https://mcp.higgsfield.ai/mcp`. With it added, *I* can run the test generation directly from here instead of the user clicking through a browser flow. This was a missed-default that wasted a research turn and would have wasted the user's hour.

**How to apply:**
- For any AI provider being shortlisted, do a quick `WebSearch "<provider> MCP server"` and check `claude mcp list` to see if one's already wired.
- If an MCP exists (hosted preferred, local fallback), propose using it as the test path before suggesting manual web-UI clicking.
- The hosted-MCP authentication usually piggybacks on the user's existing account — no extra API key juggling. Lower setup friction than the user assumes.
- Caveat (per `reference_mcp_server_session_restart.md`): newly-added MCPs require a session restart before tools register. Plan the restart into the handoff.
