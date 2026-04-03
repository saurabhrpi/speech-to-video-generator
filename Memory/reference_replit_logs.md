---
name: Replit log format
description: How to read backend logs saved from Replit — each log row spans 4 lines in the exported file
type: reference
---

Backend logs are exported from the Replit console into debug/. Each log row is broken into 4 lines: timestamp, hash, User/System, and the ACTUAL MESSAGE. There is no spacing between rows.

The 4th line of each row contains the useful log content. In the ideal case where every message is 1 line, messages appear at lines 4, 8, 12, 16, etc. But if a message spans multiple lines (length l), the next row's message shifts forward by (l - 1). So positions are not fixed — you must parse row by row, accounting for multi-line messages.
