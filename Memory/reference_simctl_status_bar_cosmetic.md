---
name: simctl status_bar is cosmetic, not real network control
description: xcrun simctl status_bar override only changes displayed icons; to actually cut sim network traffic, toggle host Mac WiFi with networksetup
type: reference
---

`xcrun simctl status_bar booted override --wifiMode failed --cellularMode notSupported` only changes the DISPLAYED status-bar icons on the simulator. It does NOT actually cut network traffic — the sim still uses the host Mac's network stack underneath and reaches the internet.

**To actually simulate offline on the iOS Simulator:**
```
networksetup -setairportpower en0 off    # WiFi off at the host
networksetup -setairportpower en0 on     # back on
```

Confirm `en0` is your WiFi interface via `networksetup -listallhardwareports`.

Alternative: macOS Network Link Conditioner with the 100% packet loss profile (pref pane, separate install with Xcode Additional Tools).

Watch out for ethernet — if the Mac is plugged in and WiFi is off, the sim still has internet. Disconnect ethernet or use NLC to cut both.
