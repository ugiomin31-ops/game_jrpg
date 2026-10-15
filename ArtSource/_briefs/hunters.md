# Hunters — brief catalog (data-driven)

Source of truth: `Assets/_Game/Resources/Data/heroes.json` (20 rows: `display_name`, `class`, `rank`, `gender`,
`join_kind`/`join_zone`, `starter_equipment`, `line`, `profile`). The `profile` field is the look spec; every brief
below follows it. Model folder: `Assets/_Game/Resources/Art/Characters/<id>/` (all 20 exist, procedural).
Generated 2026-10-11.

Common frame for every hunter (also in `README.md` §Prompt frame (hunter)): adult Korean hunter, slim adult anime
proportions about 7 heads tall (not chibi), modern Seoul hunter streetwear/tactical, **empty hands**, no weapon or
held props, no cape/crown/medieval armour, full-body front view in a symmetric A-pose, hands clear of the body, feet
apart, plain light-grey background, square, solid attached details, nothing dangling. Rig: Tripo Humanoid (Mixamo).
Size: hero 10–20k tris (h_dohyun came out at 9.4k and was accepted). Clips: see README §Hunter animation blocker.

Status: DONE-STAGED = h_seoa (Tripo rig and Idle/Run exported, staged, waiting for the remaining animations).
EXPORTED = h_dohyun (Tripo FBX in `ArtSource/hunters/h_dohyun/tripo_export/`, not installed). TODO = everything else.

## Identity conflicts
- **h_seoa**: the staged Tripo model came from prompts that ignore the data profile (navy technical jacket, short bob,
  wrist modules; `ArtSource/hunters/h_seoa/candidates/prompts.md`). The data profile says beige trench coat, white knit,
  pleated skirt, round glasses, spellbook on a belt chain. Main decides: accept the staged look and update `profile`,
  or regenerate from the profile (one more generation).
- Held props in profiles conflict with the empty-hands rule. Briefs drop them, or move them to the back or belt as solid
  attached shapes: h_minjun (manhole-cover shield), h_siwoo (rifle-like bow), h_jun (crossbow on the back),
  h_rina (star wand), h_jaehyun (stethoscope is fine, worn).
- Fantasy-leaning items: h_rina "small cape" (magical-girl costume) and h_haneul "floating violet runes". Briefs swap
  the cape for a short ribbon bow at the back and drop the runes (floating parts break image-to-3D).

## Starting party (zone 1, join_kind start) — highest priority

**h_dohyun** · 「강도현」 · warrior · E · M · starter sword_bronze — EXPORTED (install pending).
Line: 「나는 아직 E급이야. 그래도 여기서 도망치진 않아.」
Brief: A Korean man around 20, lean and athletic, short messy black hair, determined look: black hoodie under an olive tactical vest with pouches, dark cargo pants, sneakers, fingerless gloves, long red scarf (tight to the body).

**h_seoa** · 「한서아」 · mage · E · F · starter staff_oak — DONE-STAGED (identity conflict above).
Line: 「수업 빠지면 F인데… 게이트가 먼저야.」
Brief (from profile): A university student mage: beige trench coat over a white knit, pleated skirt, black tights, ankle boots, round glasses, a small spellbook clipped to the belt on a short chain.

**h_jiho** · 「윤지호」 · archer · E · M · starter bow_short — TODO.
Line: 「과녁보다 크네. 안 빗나가.」
Brief: A former national-team archer: navy track jacket with white stripes, snapback cap, arm guard on the left forearm, quiver worn like a sports-bag strap across the back, joggers and trainers.

**h_yuna** · 「백유나」 · cleric · E · F · starter mace_wood — TODO.
Line: 「다친 사람 있으면 저부터 불러 주세요!」
Brief: A nursing student: white cardigan over a light-blue scrub top, red-cross armband, white sneakers, hair in a low ponytail, first-aid pouch on the hip.

## Boss-reward hunters (join after zone N's boss), in zone order

**h_minjun** · 「최민준」 · warrior · D · M · zone 1 — TODO.
Line: 「시민 대피 끝! 이제 내가 막는다.」
Brief: A former firefighter tank: orange-and-navy turnout coat with reflective stripes, yellow brimmed helmet-cap, heavy gloves, boots. The manhole-cover shield is left out (empty hands); it could be a separate prop later.

**h_sora** · 「이소라」 · archer · D · F · zone 2 · job ranger — TODO.
Line: 「…말 걸지 마. 표적이 도망가.」
Brief: A quiet assassin type: short black bomber jacket with violet trim, fitted dark pants, thigh straps with sheathed knives (attached), violet accents, cool expression.

**h_taeyang** · 「오태양」 · mage · C · M · zone 3 · job elementalist — TODO.
Line: 「공장 불 끄던 놈이 불을 쓰게 될 줄이야.」
Brief: A factory engineer turned fire mage: orange coveralls with the sleeves tied at the waist, black tank top, welding goggles pushed up on the forehead, tool belt, heat-proof gloves.

**h_eunbi** · 「정은비」 · cleric · C · F · zone 4 · job exorcist — TODO.
Line: 「귀신보다 무서운 건 야근이에요.」
Brief: A Korean shaman exorcist: white jeogori-style short jacket with a red goreum ribbon, dark hanbok-like long skirt, talismans on a cord across the chest (no lettering), bell bracelet, long straight black hair.

**h_gunwoo** · 「서건우」 · warrior · C · M · zone 5 · job berserker — TODO.
Line: 「맞으면서 배우는 거지. 덤벼!」
Brief: An MMA-fighter berserker: sleeveless black compression top, red fight shorts over leggings, hand wraps and bandaged forearms, buzz cut, chain necklace.

**h_hana** · 「김하나」 · mage · B · F · zone 6 · job elementalist — TODO.
Line: 「팬 여러분, 오늘도 얼려 드릴게요!」
Brief: An idol hunter ice mage: white and ice-blue stage jacket with silver trim, short pleated skirt with leggings, star hairpin, knee boots, headset mic.

**h_siwoo** · 「류시우」 · archer · B · M · zone 7 · job sniper — TODO.
Line: 「교실에서 보는 것보다 과녁이 크네요.」
Brief: A genius high-school sniper: navy school blazer with an emblem patch (no text), loosened tie, white shirt, grey slacks, headphones round the neck. The rifle-like bow is left out.

**h_mirae** · 「송미래」 · cleric · B · F · zone 8 · job inquisitor — TODO.
Line: 「죄는 미워하되, 몬스터는 더 미워하세요.」
Brief: An inquisitor: long white military-style coat with gold buttons and a cross emblem, black gloves, peaked cap, knee boots, golden-blonde braid.

**h_jaehyun** · 「남재현」 · cleric · A · M · zone 9 · job priest — TODO.
Line: 「환자는 제가 맡죠. 여러분은 싸우기만 하세요.」
Brief: A doctor healer: white doctor's coat over teal scrubs, stethoscope round the neck, ID badge clipped on, rimless glasses, neat short hair.

**h_dana** · 「문다나」 · warrior · A · F · zone 10 · job knight — TODO.
Line: 「한 걸음도 물러서지 않는다. 그게 해병이다.」
Brief: An ex-marine guardian: digital-camo jacket with rolled sleeves, tactical plate carrier, knee pads, combat boots, short ponytail, red beret.

**h_iseul** · 「차이슬」 · archer · A · F · zone 11 · job sniper — TODO.
Line: 「길드 거리는 내 앞마당이야. 따라와.」
Brief: A guild scout captain: green field poncho cut short over a utility vest, cargo pants, binoculars on the chest, bandana, fingerless gloves.

**h_haneul** · 「강하늘」 · mage · S · M · zone 12 · job warlock — TODO.
Line: 「S급이라고 다 친절한 건 아냐. 난 예외지만.」
Brief: An S-rank dark mage: long black coat with violet lining and a high collar (coat tails short enough not to fuse with the legs), black gloves, silver hair, dress shoes. No floating runes.

## Scout hunters (join_kind scout)

**h_bora** · 「표보라」 · warrior · C · F · scout zone 3 · job berserker — TODO.
Line: 「의뢰비만 확실하면, 끝까지 지켜 드리죠.」
Brief: A bodyguard warrior: black suit with the jacket open, red tie, sunglasses pushed up on the head, earpiece, leather gloves, bob-cut wine-red hair.

**h_youngsu** · 「장영수」 · cleric · C · M · scout zone 6 · job exorcist — TODO.
Line: 「나무아미타불… 그리고 한 대 더.」
Brief: A temple-monk exorcist: grey monk robe with a brown kasa sash, prayer beads, straw sandals over socks, shaved head, a wooden moktak hanging from the belt.

**h_rina** · 「유리나」 · mage · B · F · scout zone 8 · job elementalist — TODO.
Line: 「사랑과 마력으로, 게이트를 닫겠어요!」
Brief: A magical-girl mage: pink-and-white frilled jacket with a big ribbon, twin tails with ribbons, striped stockings, a short ribbon bow at the back instead of a cape. No wand.

**h_jun** · 「진준」 · archer · A · M · scout zone 10 · job ranger — TODO.
Line: 「배송 완료. 표적도 완료.」
Brief: A courier-rider assassin: black hooded windbreaker with neon-yellow stripes, motorcycle gloves, helmet clipped to the belt, delivery bag across the back. The crossbow is left out.
