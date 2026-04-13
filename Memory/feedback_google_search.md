---
name: Google search when uncertain
description: Use web search proactively when unsure, AND always provide web evidence before proposing root cause fixes
type: feedback
---

When in doubt about which direction to think, what to answer, or what approach to take — do a Google search rather than guessing or hedging.

**For root cause investigations specifically:** Before proposing a fix or making code changes, search the web for evidence that the suspected root cause is real. Present the evidence to the user first. Don't jump to code changes based on theories — theories must be grounded in documented issues, known patterns, or reproducible evidence.

**Why:** User called this out during a crash investigation. I proposed two wrong root causes (SecureStore unhandled promises, Pressable+FlatList) and started making code changes without evidence. Web search quickly disproved both and revealed the real cause (react-native-reanimated dev reload crash — a well-documented issue). Would have saved time and trust by searching first.

**How to apply:** Proactively use WebSearch whenever uncertain about technical approaches, model capabilities, API behavior, best practices, or any factual question. For bug/crash investigations, ALWAYS search for evidence before proposing a root cause or making a fix. Don't treat searching as a last resort — treat it as a first instinct when confidence is low.
