---
name: Simulator clipboard paste workaround
description: iOS simulator pasteboard sync is broken; use pbpaste | xcrun simctl pbcopy booted to push Mac clipboard into simulator
type: reference
---

Automatic pasteboard sync between Mac and iOS simulator is broken. To paste into a TextInput in the simulator:

1. Copy text on Mac (Cmd+C)
2. Run: `pbpaste | xcrun simctl pbcopy booted`
3. Long-press in the TextInput in the simulator and use the iOS paste popup
