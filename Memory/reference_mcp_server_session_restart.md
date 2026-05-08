---
name: MCP server tools require session restart
description: After `claude mcp add` registers a new MCP server, its tools are NOT loaded into the current Claude Code session — need to /exit and re-launch before tools become callable
type: reference
---

After running `claude mcp add --transport stdio <name> -- <command>`, the server registers in `~/.claude.json` and `claude mcp list` will show it Connected, but its tools are NOT available in the current session. `ToolSearch` will return no matches for the server's tool names. Claude Code only loads MCP tool schemas at session startup.

**Workflow for installing a new MCP server mid-session:**
1. Run `claude mcp add ...` — confirms registration
2. Run `claude mcp list` — confirms server reports Connected
3. Tell user to `/exit` and re-launch Claude Code
4. In the next session, the server's tools become available via ToolSearch / direct call

**Why this matters:** A single session with a freshly installed MCP server will silently fail to use it. Don't try to call MCP tools from the same session that installed them — flag the restart requirement immediately, then wrap up cleanly.
