---
name: linkWithCredential doesn't fire onAuthStateChanged
description: Firebase's onAuthStateChanged only fires on sign-in/sign-out (UID null↔user), NOT on linkWithCredential — anon→Apple link path needs explicit state update
type: reference
---

## The gotcha

`auth().onAuthStateChanged()` fires when a user transitions between "signed in" and "signed out" — i.e. when the UID goes from null to a value or vice versa. It does **NOT** fire when the same UID mutates (profile update, linkWithCredential, unlink, etc.). Firebase treats those as user *mutations*, not auth state transitions.

This bites the anonymous → Apple Sign In upgrade path. When `currentUser.linkWithCredential(appleCred)` succeeds on an anonymous user, the UID stays the same (that's the whole point — preserves gallery, usage counts, clips). Firebase upgrades the user in place with `provider = apple.com` and an email, but `onAuthStateChanged` is silent.

Symptom in this codebase (before the fix): user completes Apple Sign In, Firebase Console shows the UID upgraded, but mobile UI stays stuck showing "Sign in required" because `loginRequired: false` was only cleared in the `onAuthStateChanged` callback, which never fired.

## Three ways to handle it

1. **Explicit post-action update (what we did).** After `await signInWithApple()`, manually pull `auth().currentUser`, apply it to the store, clear `loginRequired`, refresh usage. See `mobile/store/auth-store.ts::signInWithApple`.
2. **Use `onIdTokenChanged` instead.** Fires on link AND on sign-in/sign-out. Also fires every ~1 hour on token refresh — any side effects in the callback (like `refreshUsage()`) will run hourly.
3. **Use `onUserChanged`.** Fires on all user mutations including link. Supported by @react-native-firebase. Less commonly used; semantically cleanest if you want one listener to cover everything.

We kept `onAuthStateChanged` + added the explicit update — listener still earns its keep for cold start / sign-out / external session invalidation, and the redundant `set()` in the link path is a no-op.

## How to apply

- Any RN Firebase codebase using `linkWithCredential` needs explicit state sync after the call, unless it's on `onIdTokenChanged` or `onUserChanged`.
- If the listener is `onAuthStateChanged`, have the link caller return the upgraded `FirebaseUser` and push it into state directly.
- Flag this pattern whenever reviewing anon→provider migration flows — the bug is invisible on the Firebase side (UID upgrades correctly) and only surfaces as a silent UI hang.
