---
name: iOS simulator crash reports
description: How to find and parse iOS simulator crash reports from ~/Library/Logs/DiagnosticReports
type: reference
---

Crash reports are `.ips` files at:
```
~/Library/Logs/DiagnosticReports/
```

Find recent ones:
```bash
find ~/Library/Logs/DiagnosticReports -name "*.ips" -newer <reference-file>
```

Parse with Python:
```python
import json
with open('crash.ips') as f:
    lines = f.readlines()
crash = json.loads(''.join(lines[1:]))  # Line 1 = header JSON, rest = crash JSON
print(crash['termination'])  # Why it was killed
for t in crash['threads']:
    if t.get('triggered'):   # Crashed thread
        for frame in t['frames'][:15]:
            print(frame.get('symbol', hex(frame.get('imageOffset', 0))))
```

Key fields in the termination dict:
- `namespace: TCC` — privacy permission crash (tells you exactly which Info.plist key is missing)
- `namespace: SIGNAL` — native signal (SIGABRT, SIGSEGV, etc.)
- `details` — human-readable explanation of why the app was killed
