---
name: Keychain reset recovery for code signing
description: After a macOS keychain reset, three things break for iOS code signing; here's the recovery sequence
type: reference
---

After a nuclear Keychain Access reset ("Reset Default Keychains"), iOS code signing breaks in three layers. Fix them in this order:

1. **Private keys for signing certs are wiped.** Certs show "Missing Private Key" in Xcode > Settings > Accounts > Manage Certificates. Fix: click `+` > "Apple Development" to create a new cert (generates new private key at the same time). Old orphan can't be deleted from Xcode (greyed out) because Xcode needs both halves — revoke online at developer.apple.com if cleanliness matters.

2. **Apple WWDR intermediate certificates are wiped.** Build fails with "unable to build chain to self-signed root for signer" + `errSecInternalComponent`. Fix: download all current WWDR CAs from [apple.com/certificateauthority](https://www.apple.com/certificateauthority/) (G3, G4, G5, G6 + Apple Root CA) and double-click each to install in **login** keychain.

3. **Private key ACL is missing codesign partitions.** Build still fails with `errSecInternalComponent` during Embed Pods Frameworks even after WWDR certs are installed. Xcode finds the cert but codesign is denied access to the private key. Fix:
   ```bash
   security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "" ~/Library/Keychains/login.keychain-db
   ```
   (Use Mac login password if `-k ""` fails. `-l "Apple Development: <CN>"` can narrow it further.)

**CRITICAL trap — GUI ≠ partition list:** The "Allow all applications to access this item" toggle visible in Keychain Access → private key → Get Info → Access Control is the **old** ACL. The **partition list** is a newer, separate mechanism that Keychain Access does not expose anywhere in its UI. Even with "Allow all applications" already on, codesign will still fail with `errSecInternalComponent` if the partition list is missing `codesign:`. Only `security set-key-partition-list` can touch it. Don't let the GUI fool you or the user.

**CRITICAL trap — orphan-key dead-end (Session 31):** After a nuclear reset, the keychain can retain dangling references to private keys whose records were deleted. `security set-key-partition-list -s` iterates signing keys and can hit one of these orphans first, output `SecKeychainItemCopyAccess: The specified item is no longer valid. It may have been deleted from the keychain.`, and bail without ever touching the active key. Narrowing with `-l "<exact cert label>"` can work around it, but sometimes even that fails. If you see this error repeatedly, stop fighting — **pivot to EAS Build** (see `reference_eas_build_testflight.md`). Local signing post-nuclear-reset is a known rabbit hole; cut losses at the second or third failure.

**How to apply:** If the user reports any of: "Missing Private Key", "unable to build chain", "errSecInternalComponent" — suspect keychain reset and walk through these three fixes in order. If step 3 hits orphan-key errors, don't keep retrying variants — escape to EAS.

**Verify between fixes:** `security find-identity -v -p codesigning` (should show valid identity), `security verify-cert -c <cert.pem> -p codeSign` (should exit 0).

**Better: don't reset the keychain in the first place.** The root cause that prompted the reset (keychain password out of sync with login password) is better fixed via Keychain Access > right-click "login" > Change Password, entering the OLD password first.
