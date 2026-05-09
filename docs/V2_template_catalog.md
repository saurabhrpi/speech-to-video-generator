# V2 Template Catalog

**Source:** User-provided (Session 59, 2026-05-07).
**Status:** Verbatim capture — categories, names, and counts as supplied. NOT yet assigned to launch subset, pipeline class, model, or asset state.
**Sibling doc:** `V2_motion_transfer_plan.md` — V2 vision, risks, work-track breakdown, clarifying-question answers.

---

## How this catalog is used

This is the **master list of template ideas** for the V2 home-screen carousels. Not all of these will ship at V2 launch; the launch subset is chosen separately (see §2a).

Each template eventually needs:
- **Pipeline class** (which backend pipeline runs it — see §3).
- **Outcome** (1 = character-into-scene, 2 = motion-onto-character, N/A for non-motion templates).
- **Model** (Kling Motion Control / Kling-standard I2V / Hailuo I2V / Nano Banana Edit / etc.).
- **Required user inputs** (selfie, full-body photo, prompt, voice, etc.).
- **Reference asset** (driving video for motion-transfer; scene image for scene-insertion; style ref for transformation; thumbnail for carousel tile).
- **Title + description** for the carousel.
- **Outcome-1 vs Outcome-2 verdict** where applicable.
- **`published_status` flag** for QA gate.

---

## §1. Theme list (verbatim)

### a. Viral Dances
Bombale, Gangsta, Baby Dance, Na Favelinha, Ma Popo, Dance flow, Baby dance, Just Dance, No Batidao

### b. Girl Dances
The Hills, Buttons, River, Telephone, Give it up to me, Pour it up, Woman, Stateside, Lik a G6

### c. TikTok Dances
Pinky up, High School, Soda Pop Baby Dance, Freeze, Dale Pa Ve, Raindrop, Lush Life, Soda Pop Energy, Big Guy, Seteadora, 7/11, Copacabana, Speed, Got 2 Luv U, Luku, Soda Pop Moves, Baby Boo, Git up

### d. Iconic Dances
Rasputin, Boots Stop Working, Beat it, Cotton Eye Joe, Don't Play with me, Twist and Shine

### e. Furry Friend (Dogs/cats dancing)
Soda pop Pet, Pet Dance, Kitty Dance

### f. Trends
Fruit Drama, Drift Master, Teacup Memories, Palm Doll, In the Beat, Street Icon, Eyes on You, Car Flex, Iced out, Live Photos, Tornado Fly, Homeless Prank, Troll News Report, Museum Portrait, Dream Ride, Veo 3.1 ASMR, Giant People, Cage Fighter

### g. Lifestyle Caricatures
Future baby caricature, Couple Caricature, Pet caricature, Boss vibes caricature, Influencer Caricature, Fitness Caricature, Mindset Caricature, Gaming Caricature, Adventure Caricature

### h. News Prank
Caught on camera, Breaking: Chicken Heist, Milk Theft Live, Whiskey Snatcher, Breaking: T-shirt situation

### i. Awards Night
Winning Speech, Arrival Look, Backstage Elegance, Victory Pose

### j. Product Showcase (use case for ads)
Full Pour, Skin at work, Urban mist, Effortless Allure, Served with Intention, Extreme Drop, Hypnose, Brought to life

### k. Winter Olympics
Golden Stillness, Ice Focus, Frozen Grace, Midair Silence, Summit Pride

### l. Birthday Photoshoot
Birthday Walk, Birthday Balloon, Sweet Birthday, Golden Birthday, Birthday Boss, Star Birthday

### m. Viral effects
Rap Star, Underwater, Suspender style, Slow dive

### n. Classy
Old Money, Luxury, Yatch, Date, Elite

### o. Popular
Gas Station, Pixel Life, Witch Transformation, Fairy Dust, Mermaid, Horror Story, Make-up Studio, Adventure Selfie

### p. Text to video (model picker, not templates)
Text to video pro, pixverse 5, Sora 2, Baby interview, Veo 3.1 Fast, Google Veo 3.1, Kling 2.1 Master, Kling 1.6 Master, Kling 1.6 Standard, Hailuo, Seedance, Pixverse

### q. Nano action (user reduced in size, smaller items increased)
Soupy Lake, Berry on top, Cat Chase, Sunny side up

### r. Flying (by user)
Fly on cloud, Flying wings, Eiffel Tower, Flying Pharaoh, Sky Empire, Aloha wings, Cloud Nine, Flying

### s. Animal Transform (animals transforming into users)
Lion King, I of the Tiger, Legendary Leopard

### t. Earthly effects (transforming user appearance)
Blooming Body, Melting metal, Black Angel, Space zoom-in

### u. Monochrome
Under the light, Studio quality, Sitting sensation, White wonder, Black Essence

### v. Nightmare escape (user running away from danger)
It is coming, Alien Predators, Jurassic Run

### w. Metamorphosis (reversing a video which was about a user transforming into their mythical avatars)
Frost Bite, Forest Spirit, Blackwood, Green Vine, Tree of Life

### x. Image to Video
Warrior, Baby runway, Red Carpet

---

## §2. Counts at a glance

| Category | Count | Tentative pipeline class (S59 working hypothesis — NOT locked) |
|---|---|---|
| a. Viral Dances | 9 | Motion-transfer (Kling Motion Control, Outcome 2) |
| b. Girl Dances | 9 | Motion-transfer (Kling Motion Control, Outcome 2) |
| c. TikTok Dances | 18 | Motion-transfer (Kling Motion Control, Outcome 2) |
| d. Iconic Dances | 6 | Motion-transfer (Kling Motion Control, Outcome 2) |
| e. Furry Friend | 3 | Motion-transfer applied to pet photo — needs spike to confirm Kling handles non-human |
| f. Trends | 18 | Mostly scene-insertion (Outcome 1) — needs per-template review |
| g. Lifestyle Caricatures | 9 | I2I-only (Nano Banana Edit) — may not need video at all |
| h. News Prank | 5 | Scene-insertion (Outcome 1) |
| i. Awards Night | 4 | Scene-insertion (Outcome 1) |
| j. Product Showcase | 8 | Different user (B2B/advertisers); deferred — different product surface |
| k. Winter Olympics | 5 | Scene-insertion (Outcome 1) |
| l. Birthday Photoshoot | 6 | Scene-insertion (Outcome 1) |
| m. Viral effects | 4 | Style transformation (I2I → I2V) |
| n. Classy | 5 | Scene-insertion (Outcome 1) |
| o. Popular | 8 | Mixed — scene-insertion + transformation; per-template review |
| p. Text to video | 12 | NOT templates — model picker for the existing S2V flow; treat as feature, not carousel row |
| q. Nano action | 4 | Style transformation (I2I → I2V) |
| r. Flying | 8 | Scene-insertion (Outcome 1) |
| s. Animal Transform | 3 | Style transformation (I2I → I2V) |
| t. Earthly effects | 4 | Style transformation (I2I → I2V) |
| u. Monochrome | 5 | Style transformation (I2I → I2V) |
| v. Nightmare escape | 3 | Scene-insertion (Outcome 1) |
| w. Metamorphosis | 5 | I2V on pre-generated transformation image, played reversed |
| x. Image to Video | 3 | Generic I2V |
| **Total templates** | **~150** (excludes (j) B2B and (p) model-picker if both deferred) | |

Pipeline-class column above is a working hypothesis from a quick read of names — every cell needs verification before it's load-bearing.

---

## §2a. V2 launch subset (S59 — locked)

**Choice:** "Dances + Scenes (~25)" — 2 pipelines (motion-transfer + scene-insertion), 5 categories, ~25 templates. Proves both the wedge and the home-screen carousel UX across pipeline types.

| Category | Pipeline | Take |
|---|---|---|
| (a) Viral Dances | Motion-transfer (Outcome 2, Kling Motion Control) | All 9 |
| (f) Trends | Scene-insertion (Outcome 1, Nano Banana Edit → I2V) | 5 of 18 (specific picks TBD) |
| (l) Birthday Photoshoot | Scene-insertion | 4 of 6 (specific picks TBD) |
| (i) Awards Night + (k) Winter Olympics | Scene-insertion | 4 combined (2+2, specific picks TBD) |
| (r) Flying | Scene-insertion | 3 of 8 (specific picks TBD) |
| **Total** | **2 pipelines** | **~25** |

Other categories (b, c, d, e, g, h, m, n, o, q, s, t, u, v, w, x) shift to V2.1+ release. (j, p) deferred per §3a.

Specific template picks within each pool: still open — see §3 for the per-template work that gates this.

---

## §3. Open per-template work (deferred)

For each launch-subset template, before backend code can be written:

1. Confirm pipeline class.
2. Source / commission / generate the reference asset.
3. Test on Kling (or appropriate model) with at least 3 selfie variants to gauge variance.
4. Decide Outcome 1 vs 2 (where applicable).
5. Write title + description.
6. Set `published_status: draft` until QA passes.

This per-template work is the long pole for V2 launch.

---

## §3a. Explicitly deferred categories (S59 user direction)

The following two categories are **deferred to the end of V2 implementation** — not part of launch-subset analysis, not part of pipeline architecture decisions for V2 launch. Revisit once the rest of V2 is shipping.

- **(j) Product Showcase** — different user (advertisers / B2B); revisit late, may not belong in the consumer V2 product at all.
- **(p) Text to video** — list of *model names* (Sora 2, Veo 3.1, Kling Master, Hailuo, etc.), not templates. Treat as a model-picker feature for the existing S2V flow if revived; not a carousel row. Decision deferred.

---

## §4. Naming caveat

Many template names here reference real, named TikTok / IG trends ("Soda Pop", "Pinky Up", "Bombale"). The dance trend names themselves are generally not trademarked, but song titles in the names sometimes are (e.g., "Beat it", "7/11"). Pre-launch legal pass should review whether to rename or keep. Discovery-only model (Q1 = a) does NOT cover the naming question.

---

## §5. Source / change log

- **2026-05-07 (S59):** Initial capture from user message. List as supplied; pipeline-class column is S59 working hypothesis.
