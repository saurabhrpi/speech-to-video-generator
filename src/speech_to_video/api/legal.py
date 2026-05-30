"""Static legal pages (Privacy Policy, Terms of Use) served at /privacy and /terms.

Plain HTML strings keep this self-contained — no template engine, no static
files, no separate hosting. Edit the strings directly to update the docs;
git history is the change log. Bump EFFECTIVE_DATE on any substantive change.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

EFFECTIVE_DATE = "May 30, 2026"
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

<p>This Privacy Policy explains how <strong>AIVO</strong> ("we", "us", "our", "the App") handles your information. The App is operated by <strong>Saurabh Sharma</strong>, an individual sole proprietor ("the Operator"). By using the App you agree to the practices described here.</p>

<p>The App is intended only for users <strong>18 years of age or older</strong> and is not offered in the European Union or European Economic Area.</p>

<h2>Quick summary</h2>
<ul>
  <li>We create short AI-generated videos from a photo you choose or a text/voice prompt.</li>
  <li>Your photo and/or prompt is sent to third-party AI providers to generate the video.</li>
  <li><strong>Photos you upload are deleted from our servers within 24 hours.</strong> We do not use them to train AI models, and we never sell your information.</li>
  <li>We do not run third-party analytics, advertising, or tracking SDKs.</li>
</ul>

<h2>Information we collect</h2>

<p><strong>Account information.</strong> When you first open the App, we create an anonymous account through Firebase Authentication (a Google service), which assigns a random identifier not linked to any personal information. If you choose <strong>Sign in with Apple</strong>, we receive an Apple-relayed identifier and — only if you allow it — your name and email. You may use Apple's private email relay (an <code>@privaterelay.appleid.com</code> address) instead of your real email.</p>

<p><strong>Photos you upload.</strong> Some templates ask you to provide a photo of yourself (a "selfie"). When you generate a video:</p>
<ul>
  <li>Your photo is uploaded to our object storage (<strong>Cloudflare R2</strong>) under a randomized key tied to your account.</li>
  <li>It is processed by <strong>Google's AI image model</strong> ("Nano Banana Pro" / Gemini) to adapt your likeness, and the result is sent to <strong>Kling AI</strong> (Kuaishou Technology) to generate the final video.</li>
  <li><strong>Your uploaded photo is deleted from our servers within 24 hours</strong> — both by deleting it after your video is generated and by an automatic 1-day storage-expiry rule.</li>
</ul>

<p><strong>Prompts and voice input.</strong> If you use the speech/text-to-video feature, your typed prompt and/or recorded audio is sent to AI providers to generate your video. Audio is transcribed to text by <strong>OpenAI</strong> (Whisper) and is not retained by us after transcription; your prompt is sent to <strong>MiniMax</strong> (Hailuo) to generate the clip.</p>

<p><strong>Generated videos.</strong> We store links to your generated videos under your account so you can access them in the App's gallery.</p>

<p><strong>Purchase information.</strong> When you buy credits, <strong>Apple</strong> processes the payment and our purchase provider <strong>RevenueCat</strong> confirms it to our servers. We receive a transaction identifier and your credit status — never your payment-card number.</p>

<p><strong>Diagnostic data.</strong> We record technical events about each generation (timing, success or failure, the provider's task identifier) to monitor and improve reliability. This is stored in our database and is never used for advertising.</p>

<p><strong>What we do NOT collect.</strong> We do not run third-party analytics, advertising SDKs, or remote crash reporters, and we do not use App Tracking Transparency. We do not collect your location or contacts, and we do not browse your photo library — you choose a single photo via iOS's standard picker, and only that photo is uploaded.</p>

<h2>How we use information</h2>
<ul>
  <li>Create and deliver the AI videos you request</li>
  <li>Maintain your account and gallery of generated videos</li>
  <li>Process purchases and manage your credit balance</li>
  <li>Monitor reliability, diagnose failures, and prevent fraud or abuse</li>
  <li>Respond to support requests and comply with legal obligations</li>
</ul>
<p>We do not sell, rent, or share your information for advertising.</p>

<h2>Third-party services</h2>
<p>We share limited information with the following processors, each of which handles it under its own privacy policy:</p>
<ul>
  <li><strong>Google LLC</strong> (United States) — Firebase authentication and database; Google AI image generation ("Nano Banana Pro" / Gemini)</li>
  <li><strong>Kling AI</strong> / Kuaishou Technology (<strong>China</strong>) — motion/dance video generation</li>
  <li><strong>MiniMax</strong> / Hailuo (<strong>China</strong>) — text/voice-to-video generation</li>
  <li><strong>OpenAI</strong> (United States) — audio transcription (Whisper)</li>
  <li><strong>Cloudflare, Inc.</strong> (United States) — object storage (R2)</li>
  <li><strong>RevenueCat, Inc.</strong> (United States) — purchase verification</li>
  <li><strong>Apple Inc.</strong> (United States) — Sign in with Apple and App Store payments</li>
  <li><strong>Replit, Inc.</strong> (United States) — backend hosting</li>
</ul>

<h2>International data transfers</h2>
<p>We are based in the United States. As shown above, some processors — in particular <strong>Kling AI and MiniMax are located in China</strong> — receive the information needed to generate your video. By using the App you understand and agree that your information will be processed outside your country of residence, including in China, solely to provide the service you request.</p>

<h2>Data retention and deletion</h2>
<ul>
  <li><strong>Uploaded photos:</strong> deleted from our servers within 24 hours of upload.</li>
  <li><strong>Voice audio:</strong> not retained after transcription.</li>
  <li><strong>Account, gallery, and purchase records:</strong> kept while your account is active.</li>
</ul>
<p>You can permanently delete your account from inside the App at <em>Settings → Danger Zone → Delete Account</em>. Deletion removes your authentication record, credit balance, any stored photos, and all generated-video links and metadata associated with your account. This action is irreversible. You may also email us to request deletion. We do not use your photos, prompts, or videos to train AI models.</p>

<h2>Your rights — California residents (CCPA/CPRA)</h2>
<p>If you are a California resident, you have the right to know, access, and delete your personal information, and to opt out of its "sale" or "sharing" — note that <strong>we do not sell or share your personal information</strong> for cross-context behavioral advertising. We will not discriminate against you for exercising these rights. To make a request, email <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>; we will verify it using your account information.</p>

<h2>Security</h2>
<p>We use reasonable measures to protect your information, including encrypted connections, access-scoped storage credentials, and short retention windows for sensitive inputs such as photos. No method of transmission or storage is completely secure, and we cannot guarantee absolute security.</p>

<h2>Children</h2>
<p>The App is for adults <strong>18 and older</strong>. We do not knowingly collect information from anyone under 18. If you believe a minor has provided us information, please contact us and we will delete it.</p>

<h2>Changes to this policy</h2>
<p>We may revise this policy from time to time. The effective date at the top reflects the most recent revision. Continued use of the App after changes constitutes acceptance of the revised policy.</p>

<h2>Contact</h2>
<p>Questions about this policy: <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></p>
"""


_TERMS_BODY = f"""
<h1>Terms of Use</h1>
<p class="meta">Effective date: {EFFECTIVE_DATE}</p>

<p>These Terms of Use ("Terms") are a binding agreement between you and <strong>Saurabh Sharma</strong>, an individual sole proprietor ("we", "us", "the Operator"), governing your use of the <strong>AIVO</strong> iOS application ("the App"). By installing or using the App, you agree to these Terms and to our <a href="/privacy">Privacy Policy</a>.</p>

<h2>1. Eligibility</h2>
<p>You must be <strong>at least 18 years old</strong> to use the App, and you represent that you are. The App is not available in the European Union or European Economic Area.</p>

<h2>2. License</h2>
<p>We grant you a personal, non-exclusive, non-transferable, revocable license to use the App on Apple devices you own or control, subject to Apple's standard End User License Agreement and these Terms.</p>

<h2>3. AI-generated content</h2>
<p>The App produces videos using third-party AI models. You acknowledge that:</p>
<ul>
  <li>AI output is non-deterministic and may not match your input</li>
  <li>AI may produce unexpected, inaccurate, or unintended results</li>
  <li>We make no warranty as to the quality, fitness, or accuracy of generated videos</li>
  <li>You are responsible for reviewing generated content before sharing it, and must not present it in a way that deceives others or violates the law</li>
</ul>

<h2>4. Your content and the rights you grant</h2>
<p>You are solely responsible for any photo, image, audio, or text you provide ("Your Content"). You represent that you own or have all necessary rights to Your Content and the consent of any identifiable person in it. <strong>Do not upload images of other people without their explicit permission, and never upload images of minors.</strong> You grant us a limited, worldwide, royalty-free license to host, process, and transmit Your Content to the AI providers <strong>solely to provide the App's features to you</strong>. We do not use Your Content to train AI models, and we do not sell it.</p>

<h2>5. Acceptable use</h2>
<p>You may not use the App to generate or distribute content that:</p>
<ul>
  <li>Depicts a real, identifiable person without their consent, or impersonates someone deceptively or harmfully (including deepfakes used to harm or impersonate)</li>
  <li>Is sexual or pornographic, or sexualizes any person</li>
  <li>Involves a minor in any way</li>
  <li>Is illegal, defamatory, harassing, hateful, violent, or infringes the intellectual-property, privacy, or publicity rights of others</li>
  <li>Violates the policies of the underlying AI providers (Google, OpenAI, MiniMax, Kling AI)</li>
</ul>
<p>We may remove content and suspend or terminate access for any violation of this section.</p>

<h2>6. Credits and purchases</h2>
<ul>
  <li>Credits are consumable in-app purchases processed by Apple. We grant credits after Apple confirms the transaction. New users may receive a limited number of free starter credits.</li>
  <li>Credits have no cash value, are non-transferable, and exist only for use within the App.</li>
  <li>Credits are deducted when a generation is successfully created; if a generation fails on our side, we aim not to charge you for it.</li>
  <li>Refunds are handled by Apple under their standard App Store refund policy; we cannot directly refund purchases. Nothing here limits rights you have under applicable law.</li>
</ul>

<h2>7. Account</h2>
<p>You may use the App anonymously or Sign in with Apple. You may delete your account at any time from <em>Settings → Danger Zone → Delete Account</em>; deletion is irreversible (see our <a href="/privacy">Privacy Policy</a>).</p>

<h2>8. Disclaimer</h2>
<p class="legal-block">THE APP IS PROVIDED "AS IS" AND "AS AVAILABLE", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. WE DO NOT WARRANT THAT THE APP WILL BE UNINTERRUPTED, ERROR-FREE, OR THAT ANY GENERATION WILL SUCCEED.</p>

<h2>9. Limitation of liability</h2>
<p class="legal-block">TO THE MAXIMUM EXTENT PERMITTED BY LAW, WE WILL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF DATA, PROFITS, OR GOODWILL, ARISING FROM OR RELATED TO YOUR USE OF THE APP. OUR TOTAL LIABILITY FOR ANY CLAIM WILL NOT EXCEED THE GREATER OF (A) THE AMOUNT YOU PAID US IN THE THREE (3) MONTHS BEFORE THE CLAIM, OR (B) US $50.</p>

<h2>10. Indemnification</h2>
<p>You agree to indemnify and hold harmless the Operator from any claims, damages, liabilities, and expenses (including reasonable legal fees) arising out of Your Content, your use of the App, or your violation of these Terms or any law or third-party right.</p>

<h2>11. Termination</h2>
<p>We may suspend or terminate your access to the App at any time for violation of these Terms or for any reason. Upon termination, your right to use the App ceases immediately.</p>

<h2>12. Governing law</h2>
<p>These Terms are governed by the laws of {GOVERNING_LAW_JURISDICTION}, without regard to conflict-of-law principles. Any dispute will be resolved in the state or federal courts located in {GOVERNING_LAW_VENUE}, and you consent to the personal jurisdiction of those courts. Nothing here affects mandatory consumer-protection rights you may have where you reside.</p>

<h2>13. Apple's EULA</h2>
<p>To the extent these Terms conflict with Apple's standard End User License Agreement (the "Apple EULA"), the Apple EULA controls.</p>

<h2>14. Changes</h2>
<p>We may revise these Terms from time to time. Continued use of the App after changes constitutes acceptance of the revised Terms.</p>

<h2>15. Contact</h2>
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
<p>One video = 25 credits. New users get 25 free credits — enough for one free video. When you want more, buy a credit pack from the in-app paywall: $5.99 for 50 credits (2 videos), $15.99 for 150 credits (6 videos), or $24.99 for 250 credits (10 videos). Credits never expire.</p>

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
