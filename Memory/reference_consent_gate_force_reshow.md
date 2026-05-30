---
name: reference_consent_gate_force_reshow
description: A one-time consent/onboarding gate won't re-show on reload once its AsyncStorage flag is set; clear the key from the sim manifest to force it
metadata:
  type: reference
---

The onboarding gate (`mobile/components/OnboardingScreen.tsx`, rendered by `_layout.tsx` when `hasDataSharingConsent()` is false) is **one-time**: tapping **Continue** writes `'true'` to `CONSENT_KEY` in AsyncStorage (`mobile/lib/consent.ts`), and the gate is skipped thereafter. **Reloading the JS does NOT re-show it** — the flag is already set. (S86: spent a detour here — "reload should show onboarding" was wrong; the v3 key was already `true` because Continue had been tapped during an earlier reload.)

Bumping `CONSENT_KEY` (e.g. `data_sharing_consent_v2` → `v3`) invalidates old consent so every existing user re-sees onboarding **once** — but as soon as the bumped key is satisfied (Continue tapped, even accidentally while testing), reload won't show it again.

**To force onboarding to re-appear on the simulator** without erasing the whole sim (which also wipes gallery/auth): clear just the consent key from the app's AsyncStorage manifest, then relaunch. RN AsyncStorage (@react-native-async-storage) stores small values inline in `RCTAsyncLocalStorage_V1/manifest.json`. Terminate first so the app doesn't re-flush its in-memory copy over the edit.

```
UDID=592C0D4C-9D02-49D2-B693-F8DFA0D6E835 ; BID=com.saurabh.speechtovideo
MAN=$(find ~/Library/Developer/CoreSimulator/Devices/$UDID -path "*RCTAsyncLocalStorage*/manifest.json" | head -1)
xcrun simctl terminate booted $BID
python3 -c "import json,sys; p=sys.argv[1]; d=json.load(open(p)); [d.pop(k,None) for k in list(d) if 'consent' in k]; json.dump(d,open(p,'w'))" "$MAN"
xcrun simctl launch booted $BID
```

Heavier alternative = `xcrun simctl erase booted` (true fresh install, wipes everything). Related: [[reference_simulator_keychain_persists]], [[reference_simctl_privacy_tcc]].
