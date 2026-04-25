"""Static legal pages (Privacy Policy, Terms of Use) served at /privacy and /terms.

Plain HTML strings keep this self-contained — no template engine, no static
files, no separate hosting. Edit the strings directly to update the docs;
git history is the change log. Bump EFFECTIVE_DATE on any substantive change.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

EFFECTIVE_DATE = "April 25, 2026"
SUPPORT_EMAIL = "support@speech-2-video.ai"
GOVERNING_LAW_JURISDICTION = "the State of Tennessee, United States"
GOVERNING_LAW_VENUE = "Davidson County, Tennessee"

_BASE_STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 20px 64px;
  line-height: 1.6;
  color: #1c1c1e;
  background: #ffffff;
  -webkit-text-size-adjust: 100%;
}
@media (prefers-color-scheme: dark) {
  body { color: #f2f2f7; background: #000000; }
  a { color: #0a84ff; }
  .meta { color: #8e8e93; }
}
h1 { font-size: 1.8rem; margin: 0 0 4px; }
h2 { font-size: 1.2rem; margin-top: 2rem; }
.meta { color: #6c6c70; font-size: 0.9rem; margin: 0 0 24px; }
ul { padding-left: 20px; }
li { margin: 4px 0; }
.legal-block { font-size: 0.92rem; }
"""


def _shell(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Speech to Video</title>
  <style>{_BASE_STYLE}</style>
</head>
<body>
{body_html}
</body>
</html>
"""


_PRIVACY_BODY = f"""
<h1>Privacy Policy</h1>
<p class="meta">Effective date: {EFFECTIVE_DATE}</p>

<p>This Privacy Policy explains how <strong>Speech to Video</strong> ("we", "us", "the App") handles information when you use our iOS application.</p>

<h2>Information we collect</h2>

<p><strong>Account information.</strong> When you first open the App, we generate a random anonymous identifier (Firebase UID) so we can associate your activity with one device. This identifier is not linked to any personal information.</p>

<p>If you choose to <strong>Sign in with Apple</strong>, we receive your name (only if you choose to share it) and an email address. You may use Apple's private email relay (an <code>@privaterelay.appleid.com</code> address) instead of sharing your real email — we receive whichever you choose.</p>

<p><strong>Generated content.</strong></p>
<ul>
  <li><strong>Prompts and audio.</strong> Text prompts you type, and audio you record for transcription, are sent to third-party AI providers (OpenAI for transcription, MiniMax for video generation). We do not retain audio files after transcription.</li>
  <li><strong>Generated videos.</strong> URLs to your generated videos are stored on our servers under your account identifier so you can access them from the App's gallery. The video files themselves are hosted by the AI providers.</li>
</ul>

<p><strong>Purchase information.</strong> When you buy a credit pack, our payment processor RevenueCat receives the transaction identifier from Apple and confirms the purchase to our servers. We store the transaction identifier to grant your credits and prevent duplicate fulfillment. We do not see your payment method or any other Apple-specific payment details.</p>

<p><strong>Information we do NOT collect.</strong></p>
<ul>
  <li>We do not run third-party analytics, advertising SDKs, or remote crash reporters.</li>
  <li>We do not collect device identifiers, location, contacts, photo library, or any microphone data beyond the audio you actively record for transcription.</li>
</ul>

<h2>How we use information</h2>
<p>We use the information described above to:</p>
<ul>
  <li>Operate the App's video generation feature</li>
  <li>Maintain your gallery of generated videos</li>
  <li>Process credit purchases and prevent duplicate fulfillment</li>
  <li>Authenticate you and recover your account if you reinstall the App on the same Apple ID</li>
</ul>
<p>We do not sell, rent, or share your information for advertising.</p>

<h2>Third-party services</h2>
<p>The App relies on the following services. Their handling of information is governed by their own privacy policies:</p>
<ul>
  <li><strong>Apple</strong> — Sign in with Apple, in-app purchases</li>
  <li><strong>Google Firebase</strong> — authentication, document database for credit balance</li>
  <li><strong>RevenueCat</strong> — purchase verification</li>
  <li><strong>OpenAI</strong> — audio transcription (Whisper)</li>
  <li><strong>MiniMax (Hailuo)</strong> — text-to-video generation</li>
  <li><strong>Replit</strong> — backend hosting</li>
</ul>

<h2>Data retention and deletion</h2>
<p>You can permanently delete your account from inside the App: <em>Settings → Danger Zone → Delete Account</em>. Deletion removes your authentication record, your credit balance, and all generated video URLs and metadata associated with your account. This action is irreversible.</p>
<p>Generated video files hosted by AI providers are retained per those providers' own policies; we cannot recall them on your behalf.</p>

<h2>Children</h2>
<p>The App is not directed to children under 13 and we do not knowingly collect information from children under 13. If you believe a child has provided us with information, please contact us and we will delete it.</p>

<h2>Changes to this policy</h2>
<p>We may revise this policy from time to time. The effective date at the top reflects the most recent revision. Continued use of the App after changes constitutes acceptance of the revised policy.</p>

<h2>Contact</h2>
<p>Questions about this policy: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
"""


_TERMS_BODY = f"""
<h1>Terms of Use</h1>
<p class="meta">Effective date: {EFFECTIVE_DATE}</p>

<p>These Terms of Use ("Terms") govern your use of the <strong>Speech to Video</strong> iOS application ("the App"). By installing or using the App, you agree to these Terms.</p>

<h2>1. License</h2>
<p>We grant you a personal, non-exclusive, non-transferable, revocable license to use the App on Apple devices you own or control, subject to Apple's standard End User License Agreement and these Terms.</p>

<h2>2. AI-generated content</h2>
<p>The App produces videos using third-party AI models. You acknowledge that:</p>
<ul>
  <li>AI output is non-deterministic and may not always match your prompt</li>
  <li>AI may produce unexpected, inaccurate, or unintended results</li>
  <li>We make no warranty as to the quality, fitness, or accuracy of generated videos</li>
  <li>You are responsible for reviewing generated content before sharing or distributing it</li>
</ul>

<h2>3. Acceptable use</h2>
<p>You may not use the App to generate or distribute content that:</p>
<ul>
  <li>Is illegal, defamatory, harassing, or infringes the rights of others</li>
  <li>Sexualizes or harms minors in any way</li>
  <li>Promotes violence, self-harm, or hatred toward any group</li>
  <li>Impersonates a real person without their consent</li>
  <li>Violates the policies of the underlying AI providers (OpenAI, MiniMax)</li>
</ul>
<p>We reserve the right to revoke your access if we determine you have violated this section.</p>

<h2>4. Credits and purchases</h2>
<ul>
  <li>Credit packs are consumable in-app purchases processed by Apple. We grant credits to your account after Apple confirms the transaction.</li>
  <li>Credits do not expire but have no cash value and are non-transferable.</li>
  <li>Refunds are handled by Apple under their standard App Store refund policy; we cannot directly refund purchases.</li>
  <li>Free starter credits granted on first launch are intended for first-time anonymous users and are not replenished after account deletion.</li>
</ul>

<h2>5. Account</h2>
<p>You may use the App anonymously or Sign in with Apple. You may delete your account at any time from Settings; deletion is irreversible (see our <a href="/privacy">Privacy Policy</a>).</p>

<h2>6. Disclaimer</h2>
<p class="legal-block">THE APP IS PROVIDED "AS IS" AND "AS AVAILABLE", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.</p>

<h2>7. Limitation of liability</h2>
<p class="legal-block">TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE WILL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING FROM OR RELATED TO YOUR USE OF THE APP, EVEN IF WE HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. OUR TOTAL LIABILITY WILL NOT EXCEED THE AMOUNT YOU HAVE PAID TO US IN THE PAST 12 MONTHS.</p>

<h2>8. Termination</h2>
<p>We may suspend or terminate your access to the App at any time for violation of these Terms or for any reason. Upon termination, your right to use the App ceases immediately.</p>

<h2>9. Governing law</h2>
<p>These Terms are governed by the laws of {GOVERNING_LAW_JURISDICTION}, without regard to conflict-of-law principles. Any dispute will be resolved in the state or federal courts located in {GOVERNING_LAW_VENUE}, and you consent to the personal jurisdiction of those courts.</p>

<h2>10. Apple's EULA</h2>
<p>To the extent these Terms conflict with Apple's standard End User License Agreement (the "Apple EULA"), the Apple EULA controls.</p>

<h2>11. Changes</h2>
<p>We may revise these Terms from time to time. Continued use of the App after changes constitutes acceptance of the revised Terms.</p>

<h2>12. Contact</h2>
<p>Questions: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
"""


_SUPPORT_BODY = f"""
<h1>Support</h1>
<p class="meta">For help with AI Speech to Video</p>

<h2>Contact us</h2>
<p>For all questions — bug reports, feature requests, account help, refund inquiries, or anything else — email us at: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
<p>We typically respond within 1–2 business days.</p>

<h2>Common questions</h2>

<h3>How do credits work?</h3>
<p>One video = 10 credits. New users get 10 free credits — enough for one free video. When you want more, buy a credit pack from the in-app paywall: $4.99 for 50 credits (5 videos), $9.99 for 120 credits (12 videos), or $19.99 for 250 credits (25 videos). Credits never expire.</p>

<h3>Where are my generated videos stored?</h3>
<p>Each generated video is saved in your in-app Gallery. From there you can save it to your Camera Roll, share via the iOS share sheet, or delete it.</p>

<h3>Refunds</h3>
<p>Credit pack refunds are handled directly by Apple under their standard App Store refund policy. Request one at <a href="https://reportaproblem.apple.com">reportaproblem.apple.com</a>. We are unable to process refunds directly.</p>

<h3>How do I delete my account?</h3>
<p>In the app, tap the gear icon → Settings → Danger Zone → Delete Account. This permanently removes your account, credits, and generated videos.</p>

<h3>Keep my videos across devices</h3>
<p>If you're signed in anonymously and want your gallery and credits to persist across devices, tap the gear icon → Settings → Sign in with Apple. Your existing data carries over.</p>

<h3>The video didn't match my prompt</h3>
<p>AI video generation is non-deterministic — output can vary. Try rewording your prompt with more specific visual details (subject, action, environment, mood). For example, "a corgi in a tuxedo, slow motion, golden hour lighting" works better than "a fancy dog."</p>

<h2>Privacy &amp; terms</h2>
<p>For full details on how we handle your information, see our <a href="/privacy">Privacy Policy</a> and <a href="/terms">Terms of Use</a>.</p>
"""


@router.get("/privacy", response_class=HTMLResponse)
def privacy_policy() -> HTMLResponse:
    return HTMLResponse(_shell("Privacy Policy", _PRIVACY_BODY))


@router.get("/terms", response_class=HTMLResponse)
def terms_of_use() -> HTMLResponse:
    return HTMLResponse(_shell("Terms of Use", _TERMS_BODY))


@router.get("/support", response_class=HTMLResponse)
def support_page() -> HTMLResponse:
    return HTMLResponse(_shell("Support", _SUPPORT_BODY))
