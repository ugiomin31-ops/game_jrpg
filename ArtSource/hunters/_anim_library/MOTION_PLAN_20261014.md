# Motion audit and Tripo plan (2026-10-14)

Read-only analysis at commit 7fede68. No assets or code were changed. Budget: about 590 Tripo credits on account 3.
Known costs: free presets (on a Humanoid/Mixamo rig), text-to-motion 20 per clip (whole seconds), Auto Rig 20, generate 55 + Smart Mesh retopo 35.

**Plan in one line:** 20 text-to-motion clips (400) + 2 generated objects (180) = 580 credits. Everything else is free presets or code.

---

## 1. Audit

### 1.1 How a model gets its clips

From `ArtLibrary.SpawnCharacter`:

- **Model with its own `Idle` take** (all Tripo monsters and bosses, villager_a): uses only its own takes. The Unity rig is Generic, so clips are bound to that model's bone paths and do not transfer between models.
- **Unity Humanoid model with no takes** (all 5 hunters, the elder, innkeeper, smith, guild_clerk and shopkeeper NPCs): gets the shared library `Art/HumanoidAnimations/` (Idle, Run, Walk, Attack, Cast, Hit, Die, Victory, Guard, Revive, Talk). That is overlaid with `Art/HumanoidAnimationsByClass/<ClassOf(id)>/`.
  - `ClassOf(heroId)` returns the hero's class. For an NPC it returns the NPC id, so a folder `HumanoidAnimationsByClass/<npcId>/` would already work as a per-NPC override.
  - There is **no per-hero layer**. Two heroes of the same class (h_dohyun and h_minjun are both warriors) can never move differently.
- **Contact / release point:** `ArtLibrary.ClassContact` for class takes (warrior Attack .396, cleric Attack .14, mage Skill .50, archer Attack .51). Otherwise `BattleView.DefaultContact`: Attack .40, Cast .60, Skill .50, Ultimate 44/66. `ClassEnd` cuts held tails (warrior Attack .68, archer .85).

Which clip a battle action plays (`BattleView.cs` around lines 640–690):

| Situation | Clip played |
|---|---|
| Presentation `actor_action == cast`, or an item | `Cast` |
| Non-cast Skill with a `Skill` clip | `Skill` |
| Anything else | `Attack` |
| Mage basic attack with no class Attack | `Cast` |
| Ultimate | `Ultimate` if the model has it; otherwise the `Cast` wind-up, then the normal strike |
| Boss entrance | `Roar`, else `Attack` |
| Boss phase change | `Cast` |
| Party victory | `Victory` |
| Party rest pose | `BattleIdle` (if present) |

Skill mix per hero (learnset × presentation actor_action):

| Hero | attack-type | cast-type | shoot-type |
|---|---|---|---|
| h_dohyun | 19 | 6 | – |
| h_minjun | 19 | 6 | – |
| h_seoa | – | 24 | – |
| h_yuna | – | 24 | – |
| h_jiho | – | 2 | 20 |

So h_seoa and h_yuna play `Cast` for almost everything, and both warriors play `Attack` for almost everything.

### 1.2 Hunters (all Humanoid, no own takes)

Library source rigs:
- Shared library: account-1 female hunter rig `0b4952e7`.
- Class takes: account-2 shopkeeper rig `bc94a7b1`.
- Neither rig is reachable now.

| Slot | h_dohyun (warrior, sword) | h_minjun (warrior, sword, D-rank rescue tank) | h_seoa (mage, staff) | h_jiho (archer, bow) | h_yuna (cleric, mace) |
|---|---|---|---|---|---|
| Idle (town, dungeon) | shared `idle` preset | same | same | same | same |
| BattleIdle | warrior `BattleIdle`: boxer guard, both fists at the face, loop seam 0.052 | **same file** | mage `BattleIdle` = `standing_relax` (casual, 17.6 s) | archer `BattleIdle` = same `standing_relax` | cleric `BattleIdle` = same `standing_relax` |
| Run / Walk | shared `run` / `walk` | same | same | same | same |
| Attack | warrior `Attack` = **`chop` preset** (two empty fists slam down, no sword arc), contact .396 | **same** | mage has none → plays shared `Cast` | archer `Attack` = bow-draw text-to-motion (good), .51 | cleric `Attack` = cane sweep, **contact .14** (hit lands almost at once, then a long hold) |
| Skill (physical skills) | none → `Attack` (chop) for all 19 attack skills | same | mage `Skill.fbx` installed but **never played** (all mage skills are cast) | none → `Attack` for all 20 shoot skills, incl. sig double shot | none |
| Cast | shared `cast_a_spell` cut (palm thrust, .605) | same, **including his signature taunt** | same | same | same, **including heals and sig 응급 처치** |
| Signature | 이연참 "two invisible-fast cuts" → one chop | 구조대의 함성 (taunt) → palm thrust | 정전기 폭발 → palm thrust | 국대 더블 샷 (two arrows) → one draw | 응급 처치 (heal) → aggressive palm thrust at the ally |
| Ultimate | no `Ultimate` clip anywhere → `Cast` wind-up + chop | same | `Cast` | `Cast` + draw | `Cast` |
| Guard / Revive / Hit / Die | shared Guard (text), Revive (prone stand-up), `hit_to_body_01`, `defeat_02` | same | same | same | same |
| Victory | shared `cheer` | same | same | same | same |

### 1.3 Humanoid-rigged monsters and bosses (own takes, Generic in Unity)

| Model | Takes (source preset → slot) | Lengths (s) |
|---|---|---|
| sprout, mushroom, pixie (account 3) | idle → Idle; walk (in place) → Run; **chop** → Attack; **cheer 20–79 copy** → Cast; hit_to_body_01 → Hit; defeat_02 → Die; cheer → Victory | Idle 15.33, Run 2.33, Attack 2.46, Cast 2.46, Hit 1.29, Die 8.46, Victory 12.08 |
| forest_guardian (account 3, boss) | same, but Die = `fall` | same; Die 3.00 |
| sewer_rat, horned_rabbit (account 2) | idle, run, **slash** (human sword slash) → Attack, **cast_a_spell** → Cast, hit_to_body_01, defeat_02 | Attack 2.46, Cast 2.21, Die 8.46 |
| scrap_colossus, abyss_herald (account 1) | idle, run, box_01 → Attack, cast_a_spell → Cast, hit, defeat, cheer | Attack 2.21, Cast 5.38 |
| festival_pumpkin_king (account 1) | idle, run, slash, cast_a_spell, hit, defeat, cheer | Attack 2.46, Cast 2.21 |
| subway_bat_lord, goblin, mandragora, scrap_bot | older Blender takes (short, model-specific) | – |

Roar: no humanoid monster has one, so boss entrances play `Attack` (chop). forest_guardian's intro is a chop.

### 1.4 NPCs (elder, innkeeper, smith, guild_clerk, shopkeeper)

All use shared `idle`, `walk` and `Talk` (one 5 s conversation take). villager_a has its own older takes.

### 1.5 Why everything looks the same or awkward

1. **One idle for the whole world.** Every hunter, every humanoid NPC and every Tripo monster plays the same 15.3 s `idle` preset.
   - `Play("Idle")` always starts at time 0, so units spawned together breathe in lockstep: four heroes, three NPCs, a row of monsters.
   - Code fix (no credits): start looping Idle and BattleIdle at a random normalized time per unit.
2. **The chop is everyone's attack.**
   - Both warriors' Attack, and all 38 of their physical skills, use the `chop` preset: two empty fists slam down. The sword in the right hand never draws an arc.
   - sprout, mushroom, pixie and forest_guardian use the **same chop**. A stump, a mushroom, a fairy and a tree giant all attack identically, and identically to the warriors.
3. **One palm thrust casts every spell.** The shared `Cast` serves 24 mage spells, 24 cleric spells (mostly heals), both warriors' buffs and taunts, every ultimate wind-up, and the mage basic attack.
   - A heal on an ally looks like an attack on them.
   - h_minjun's signature taunt is a palm push, not a shout.
4. **Monster Cast is a cheer.** Cast = a 60-frame copy of `cheer`.
   - Every monster spell, every boss phase change and the guardian's root-bind / photosynthesis is a two-arms-up victory cheer.
   - Its .60 release point lands on an arbitrary cheer frame.
5. **Signatures don't match their text.** "Two lightning cuts" = one chop. "Double shot" = one draw. "Emergency first aid" = an offensive palm thrust. "Rescue squad war cry" = a palm push.
6. **Missing slots:** no `Ultimate` (every ultimate is the Cast wind-up), no `Roar` (boss intro is a chop), no `Skill` for warrior and archer, and the mage `Skill` take is unreachable.
7. **Timing mismatches:**
   - cleric Attack contact is 14% (strike at frame 5, then 86% of hold).
   - Monster Die is 8.46 s (`defeat_02`, 204 frames); the dissolve cuts it early.
   - The warrior `BattleIdle` loop seam is 0.052, a visible hitch every 1.5 s.
8. **Foot sliding.** Monster Run is `walk` with the root travel removed. Enemies dash 10–16 m/s in 0.22–0.36 s and the Run rate is only matched for heroes. Measured on rat and rabbit, the planted vertices move at the root speed (ratio 1.02): the feet glide.
9. **Stiff idles.** The hero rest pose is a boxer guard (warrior) or a casual standing loop (archer, mage, cleric). Nobody holds a weapon ready. Victory is the same cheer for all four, all in sync.

---

## 2. Free fixes first (no credits)

**Code (small, recommended before or alongside the clip install):**

- **Random start phase** for looping Idle, BattleIdle and Walk. This alone breaks the lockstep.
- **Per-hero clip layer.** `ArtLibrary.MergeClassClips` gets a third layer, `Art/HumanoidAnimationsByHero/<heroId>/`, merged on top of class and shared. `ClassContact` / `ClassEnd` keys become `<heroId>/<clip>` first, then `<class>/<clip>`.
  - Needed so h_dohyun and h_minjun can differ.
  - mage, cleric and archer each have one hero today, so those class folders already act as per-hero.
- **Enemy Run rate:** `SetRunRate` for enemies too, clamped .6–3. The glide is still unavoidable at dash speed, but the legs cycle.

**Free Tripo presets.** Confirm exact names with the preset recon worker; these were all seen before.

| Slot | Target | Preset | Why |
|---|---|---|---|
| Victory variants | h_jiho `agree`, h_yuna `wave_goodbye_01`, h_seoa `greet_01`, h_dohyun and h_minjun keep `cheer` | free, on rig 5de41bd4 | Four distinct victory beats instead of one synced cheer |
| NPC Idle variants | innkeeper / shopkeeper `standing_relax`; elder keeps `idle` | free | NPCs stop breathing in sync (folder `HumanoidAnimationsByClass/<npcId>/Idle.fbx`, no code) |
| Monster Die | sprout, mushroom, pixie: `fall` (3 s) instead of `defeat_02` (8.46 s) | free, on each monster's own rig | Death reads before the dissolve |
| Monster Run | sprout, mushroom, pixie, guardian: `run` instead of in-place `walk` | free | A real run cycle for the dash |
| Shared Walk / Hit | keep | – | Already fine |

---

## 3. Paid clips: top 20 in priority order (text-to-motion, 20 credits each = 400)

Sources:
- **H** = the account-3 hunter base rig `5de41bd4` (see section 4).
- **M** = that monster's own account-3 rig (Generic in Unity, so its clips must be made on its own rig).

All prompts are written to be typed verbatim. Length is whole seconds. "Contact" is the design target; after trimming, measure it in Blender by peak hand speed, as the earlier installs did, and enter it in `ClassContact` (hunters). Monsters use the runtime defaults, so trim them to land on .40 (Attack), .60 (Cast) or .50 (Skill).

| # | Target | Slot | Src | s | Prompt | Fixes | Install (path → contact) |
|---|---|---|---|---|---|---|---|
| 1 | h_dohyun | Attack | H | 2 | "Fighting stance with a sword in the right hand. A fast diagonal slash from the right shoulder down to the left hip, the blade arm fully extended at the end, then snap back to the stance. Feet planted, slight forward lean." | Replaces the two-fist chop with a real sword stroke | `ByHero/h_dohyun/Attack.fbx` → .40 |
| 2 | h_dohyun | Skill | H | 3 | "Sword fighter, sword in the right hand. Two lightning-fast slashes in a row: first a horizontal cut from right to left, then immediately a rising diagonal cut from left to right, ending in a low finishing pose with the sword arm extended. Feet planted, then return to the stance." | Signature 이연참 and all 19 physical skills | `ByHero/h_dohyun/Skill.fbx` → .40 (first cut; twin_slash VFX covers the second) |
| 3 | h_minjun | Cast | H | 2 | "Plant both feet wide, pound the chest twice with the right fist, then throw both arms wide open and shout with the chin up, hold the pose briefly, then return to a guarding stance." | Taunt / war-cry signature and his 6 buff skills | `ByHero/h_minjun/Cast.fbx` → .55 (arms open) |
| 4 | h_minjun | Attack | H | 2 | "Heavy defender. Step in with a hard left shoulder check, then a short horizontal sword swipe with the right hand at waist height, then step back into a guarding stance. Strong, grounded, feet stay close." | Distinct from h_dohyun: a tank's shove-and-cut | `ByHero/h_minjun/Attack.fbx` → .45 (swipe) |
| 5 | shared | Ultimate | H | 3 | "Crouch and gather power with both fists clenched at the hips, body trembling, then explode upward into a jump with both arms raised, and slam both arms down hard as you land in a low crouch, then rise." | Every ultimate currently uses the Cast wind-up | `HumanoidAnimations/Ultimate.fbx`, trimmed to 66 frames so the power-up ends near frame 28 and the slam is near frame 44 (`UltimateResume` 28/66, contact 44/66) |
| 6 | h_yuna | Cast | H | 2 | "Gentle healer. Bring both hands together at the chest, then lift and open both palms upward and outward toward a friend in front, hold the open pose softly, then lower the hands. Feet planted, kind posture." | Heals stop looking like an attack (24 cast skills plus signature 응급 처치) | `HumanoidAnimationsByClass/cleric/Cast.fbx` → .55 |
| 7 | h_seoa | Cast | H | 2 | "Young mage holding a staff upright in the left hand. Draw a quick circle in the air with the right hand, then snap the right palm forward at chest height to release, short hold, then relax. Feet planted." | A mage-specific cast that differs from the cleric's | `HumanoidAnimationsByClass/mage/Cast.fbx` → .60 |
| 8 | h_jiho | Skill | H | 3 | "Stand sideways to the target. Extend the left arm straight forward at shoulder height. Pull the right hand back to the right cheek and snap it open, then immediately do it a second time, faster. Lower both arms. Feet stay planted." | 국대 더블 샷 and 20 shoot skills. Phrasing copies the one archer prompt Tripo got right | `HumanoidAnimationsByClass/archer/Skill.fbx` → .35 (first release) |
| 9 | forest_guardian | Roar | M | 3 | "Huge hunched tree giant. Rear up tall, throw both long arms wide open, chest out, head thrown back in a roar, hold, then sink back into a hunched heavy stance." | Boss entrance (currently a chop) | take `Roar` in `forest_guardian.fbx` |
| 10 | forest_guardian | Attack | M | 2 | "Huge hunched giant. Swing the right arm in a wide heavy horizontal backhand sweep from right to left at waist height, body twisting with it, then recover slowly. Feet planted." | Distinct boss melee | take `Attack` → .40 |
| 11 | forest_guardian | Cast | M | 3 | "Huge giant raises both arms high above the head with palms up, holds for a moment, then slams both hands down to the ground in front, staying low, then rises." | Root bind, photosynthesis and phase change (currently the cheer) | take `Cast` → .60 (slam) |
| 12 | sprout | Attack | M | 2 | "Small stubby creature. Crouch, hop forward and headbutt with the whole body, then hop back to the start. Arms stay short and close." | Stump headbutt instead of the chop | take `Attack` → .40 |
| 13 | mushroom | Attack | M | 2 | "Short creature with a heavy head. Bend sharply forward from the waist and swing the head down like a hammer, then straighten up. Feet planted." | Cap bash instead of the chop | take `Attack` → .40 |
| 14 | pixie | Attack | M | 2 | "Small light fairy. Skip forward on tiptoe and push with both palms, then skip back lightly. Playful, quick." | Fairy push instead of the chop | take `Attack` → .40 |
| 15 | mushroom | Cast | M | 2 | "Crouch low, shake the whole body quickly side to side, then spring up with both arms flung outward as if releasing a cloud, then settle." | Spore puff instead of the cheer | take `Cast` → .60 |
| 16 | pixie | Cast | M | 3 | "Small fairy turns once on tiptoe, raises both hands overhead, then sweeps them down and outward as if sprinkling light, then settles." | Heal and holy light instead of the cheer | take `Cast` → .60 |
| 17 | sprout | Cast | M | 2 | "Small stubby creature squats and stomps one foot hard on the ground twice, arms pointing down, then straightens." | Root bind instead of the cheer | take `Cast` → .60 (second stomp) |
| 18 | h_dohyun | BattleIdle | H | 3 | "Sword fighter ready stance: left foot forward, sword held low and forward in the right hand, knees bent, light bounce on the balls of the feet, ends exactly in the starting pose so it loops." | A real weapon-ready rest pose (and the loop hitch goes) | `ByHero/h_dohyun/BattleIdle.fbx` (loop) |
| 19 | h_yuna | BattleIdle | H | 3 | "Nervous young healer holding a short mace close to the chest with both hands, weight shifting from foot to foot, glancing around, ends in the starting pose so it loops." | Gives the cleric her own personality instead of the casual stand | `HumanoidAnimationsByClass/cleric/BattleIdle.fbx` (loop) |
| 20 | h_yuna | Attack | H | 2 | "Holding a short mace in the right hand, raise it over the right shoulder and bring it down in a quick one-handed strike in front, then return to a ready stance. Feet planted." | Fixes the 14% cane-sweep contact | `HumanoidAnimationsByClass/cleric/Attack.fbx` → .40 |

**Next tier** (not funded at 590; costs include an Auto Rig of 20 where the rig is not on account 3):

| Next-tier item | Cost |
|---|---|
| h_seoa basic Attack (staff jab) | 20 |
| h_jiho BattleIdle | 20 |
| h_minjun BattleIdle (shield-bearer stance) | 20 |
| forest_guardian Skill (vine whip) | 20 |
| sewer_rat Attack (lunge bite) and horned_rabbit Attack (horn charge) | rig 20 each + 20 per clip |
| scrap_colossus / abyss_herald / festival_pumpkin_king Roar | rig 20 each + 20 per clip |

**Generation rules for the browser worker:**
- One generation per clip; no re-rolls.
- If a take reads wrong in the Tripo preview, record it and move on (it can be swapped for a next-tier clip).
- Export FBX, Blender preset, skeleton on, stay-in-place **off**.
- Hunter clips go into one bundle from rig 5de41bd4. Each monster's clips are exported from its own task with its existing free takes, so the takes can be merged into the installed FBX with the INSTALL-B6-2 builder.

**Install pipeline (unchanged from INSTALL.md):**
- Blender gate: 0 unweighted vertices, and a posed bone moves the mesh.
- Rest-pose-patched armature-only export, one action per file, manual trim, no leaf bones.
- Measure the hip-speed / hand-speed peak for the contact value.
- Loop seam check for BattleIdle (target < 0.02).
- Recentre any hips XY drift.
- Monsters: merge as `Rig|<Slot>` takes into `Art/Enemies/<id>/<id>.fbx`, keep the existing takes, and re-check floor offsets.

---

## 4. Best motion source on account 3

**Use task `5de41bd4-321d-4ff4-9487-7d4feaca58fb`.** It is the tactical-outfit hunter base body (`tripo_export_class2/rig_base`) that was uploaded and auto-rigged Humanoid/Mixamo on account 3 for the Blessing Gesture.

- **No extra credits:** it is already rigged, so no upload or Auto Rig (20) is needed.
- **Right proportions:** it has adult human proportions, unlike sprout, mushroom, pixie and forest_guardian, whose stumpy or giant bodies would bake odd reach and stance into a retargeted clip.
- **Proven:** it is the same body as the class clips already installed, and it passed the Blender skin check (0% unweighted).
- **Caveat:** its skeleton rests facing -X, while the class rig faces -Y. Unity Humanoid retargeting should absorb this, but verify on the first clip before the batch: install one take, then check facing in Unity.

**Fallback:** upload a local hunter FBX and Auto Rig it (20). Prefer h_dohyun (male, sword) if 5de41bd4 fails the facing check.

**The four monster rigs** (ab222847, 89c1a712, c8d69352, 880cb170) are only the source for their own monster clips.

---

## 5. Skill objects / props: 2 recommended (90 each = 180), 1 optional

### 1. Emergency first-aid kit (skill object for h_yuna's sig 응급 처치 and heals)
- **Why:** the heal is only quads (circle, plus signs, leaves). The heal effect gets a mesh layer that pops open over the ally.
- **Brief:** a compact modern hunter-association first-aid case, hard-shell, about 40 × 28 × 12 cm, matte white with a red cross and a small cyan Korean "응급" label plate.
  - Rubberised dark grey corner bumpers and a carry handle.
  - Lid slightly open, showing bandage rolls and an injector pen.
  - Clean stylised game-asset look, soft hand-painted shading, 3/4 front view.
  - Single object on a plain light-grey background, no text other than the label, no fantasy elements.
- **Target:** ~1.5k triangles, 1k texture.

### 2. Gate access keycard (dungeon `key_item` prop, used by every locked subway door)
- **Why:** the current key is an old procedural Blender fantasy key in a modern subway.
- **Brief:** a thick hunter-association gate access keycard on a short lanyard clip: a rounded rectangle about 9 × 6 cm, dark navy with a glowing cyan magnetic stripe and a chip.
  - A small coral warning band across one corner; the edge glows slightly.
  - Shown standing upright at a slight angle, stylised game-asset look.
  - Single object, plain light-grey background, no readable text, no fantasy motifs.
- **Target:** ~800 triangles, 1k texture. It spawns at 0.8 m against a wall, so it must read at distance: the glow edge matters more than detail.

### 3. Optional: rescue-squad riot shield (h_minjun taunt / guard; replaces the generic barrier panel for him)
- **Brief:** a modern Korean rescue-team tactical shield, about 50 × 90 cm, scuffed matte black polymer with a reflective orange band, a small viewing window, and grab handles on the back.
  - Stylised, front 3/4 view, plain background, no text, no emblem.
  - Costs 90 more; funding it means dropping clips #18–19.

---

## 6. Budget

| Item | Credits |
|---|---|
| 20 text-to-motion clips | 400 |
| First-aid kit (generate 55 + retopo 35) | 90 |
| Gate keycard (generate 55 + retopo 35) | 90 |
| Free presets (Victory variants, NPC idles, monster Die / Run) | 0 |
| **Total** | **580 of ~590** (10 spare for a server-error retry; Tripo's own retries are free) |
