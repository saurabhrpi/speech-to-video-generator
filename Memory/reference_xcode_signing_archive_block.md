---
name: New Apple Dev accounts need a registered device to archive
description: Brand-new Individual Apple Developer accounts cannot archive in Xcode until at least one device is registered, even for TestFlight distribution
type: reference
---

A brand-new Individual Apple Developer account in Xcode cannot produce ANY provisioning profile — not development, not distribution — until at least one device is registered to the team. The error "Communication with Apple failed. Your team has no devices from which to generate a provisioning profile" blocks Product > Archive entirely.

**Common misconception (and mistake made in Session 31):** Assuming signing warnings about development profiles don't affect archive/TestFlight because TestFlight uses a Distribution profile. Wrong — Xcode's automatic signing flow requires the team to have at least one registered device before it will create any profile type.

**How to apply:** When helping a user set up TestFlight with a new paid Apple Developer account, require device registration FIRST (USB connection and "Use for Development", or manual UDID entry at developer.apple.com/account/resources/devices). Only then attempt archive. Alternatively, use EAS Build to bypass local signing entirely — it handles certificates/profiles in the cloud without needing a registered device.

**Evidence source:** Apple Developer Forums thread 797981 "Fail to archive XCode"; thread 750114 "publishing app - Communication with Apple failed".
