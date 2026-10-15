# Weapons — brief catalog (data-driven)

Source of truth: `Assets/_Game/Resources/Data/equipment.json` (slot = weapon), model resolution `ArtVariants.GearModel`
(`Assets/_Game/Scripts/Logic/Data/ArtVariants.cs:30`: `model` field, else the row id). Generated 2026-10-11.

- 48 weapon rows → **48 distinct models**. No weapon row sets `model` or `tint`, so no weapon model is shared and
  there are no shared-row conflicts. (The 39 rows that do share models are all armour/accessories, which have no 3D
  model in this pass.)
- The id prefix is legacy and only partly matches the object. It still matters at runtime: `GearDisplay.Family()` takes
  the id prefix and `WeaponScale` boosts held size by it (`Assets/_Game/Scripts/Runtime/Art/GearDisplay.cs:16-23`:
  staff ×1.1, bow ×1.2, sword/mace ×1.35). Model the **object** below at real-world size; the prefix only decides the
  runtime boost (see "Scale conflicts").
- Status keys: QUEUED = corrected request already queued today, do not redo. TODO = brief ready.
- Shared prompt rules for every weapon: see `README.md` §Prompt frame (weapon). Briefs below describe only the object.

## Identity notes (id ≠ object)
| id | Shown in game as | Real object |
|---|---|---|
| sword_bronze | 「쇠파이프」 | steel pipe (blunt) |
| sword_iron | 「삼단봉」 | telescoping baton |
| sword_knight | 「강철 사냥 단검」 | hunting dagger |
| sword_flamberge | 「웨이브 블레이드」 | wavy-edged sword |
| mace_wood | 「구급 지팡이」 | wooden walking staff (medic) |
| mace_judgment | 「심판의 전쇠」 | war hammer, blunt face + spike |
| mace_requiem | 「진혼의 쇠추 망치」 | hammer with a hanging iron weight |
| mace_verdict | 「판결의 망치」 | giant iron-banded gavel |
| mace_saint / mace_grace / mace_dawn / mace_seraph | 「…홀」 | sceptre-rods |
| staff_oak, staff_crystal, staff_sage, staff_ruby, staff_bone, staff_coral, staff_void, staff_starlight | 「…완드」 | one-hand wands |
| staff_hex, staff_prism, staff_abyss_eye, staff_arcanum | 「…지팡이」/「심연의 눈」 | full-length staffs |

## Scale conflicts (flag, no split needed)
- 8 `staff_*` rows are **wands** but get the staff boost ×1.1 (smallest). A 35–45 cm wand will read tiny in hand.
  Model them as long wands/rods (~60–70 cm). Otherwise main has to decide on a per-model scale override (code change).
- `mace_wood` 「구급 지팡이」 is a full staff but gets the one-hander boost ×1.35. Keep it ~120 cm max, or override.
- `sword_knight` 「강철 사냥 단검」 is a dagger (×1.35 helps). Fine.

## Direction conflicts (tier 5–8 descriptions contain fantasy motifs)
The modern-hunter rule says no crowns, capes or medieval decoration. These rows describe them; briefs keep each row's
identity but restyle it as gate tech: sword_conqueror 「왕관 가드」 (crown guard → angular spiked guard),
sword_holy_avenger / bow_heavens / mace_seraph (angel wings → stylised blade-fins, no feathers), mace_seraph (halo →
twin emitter rings), mace_grace (lily), sword_aegis (shield guard). Main decides whether to keep this restyle.

---

## Sword family (warrior) — 12 models

**sword_bronze** · QUEUED — sword_bronze 「쇠파이프」 t1, warrior.
Brief: A plain steel water pipe picked up off the street, gaffer tape wound round the grip end, one end slightly bent. (Request queued, do not redo.)

**sword_iron** · QUEUED — sword_iron 「삼단봉」 t2, warrior. The Tripo mesh installed today (`Art/Weapons/sword_iron.tripo`) is a cleaver, the wrong object; the redo is queued.
Brief: An extended three-section telescoping steel baton with a black rubber grip and wrist-strap loop. (Queued.)

**sword_knight** · TODO — sword_knight 「강철 사냥 단검」 t3 r1, warrior.
Brief: A short steel hunting dagger with a clip point, black polymer grip and small finger guard, the kind hunter-shop field gear comes with. One-hand size, chunky toon proportions.

**sword_flamberge** · TODO — sword_flamberge 「웨이브 블레이드」 t4 r2, warrior.
Brief: A straight one-hand sword whose edge ripples in regular waves, brushed steel with a dark wrapped grip and a squared guard. Modern hunter-shop finish, no ornament.

**sword_aegis** · TODO — sword_aegis 「수호의 검 이지스」 t5 r2, warrior (job knight).
Brief: A broad straight sword whose guard is a small rounded riot-shield plate, steel blade with a blue gate-energy line down the fuller. Heavy, defensive silhouette.

**sword_ravager** · TODO — sword_ravager 「파괴의 대검」 t5 r2, warrior (job berserker).
Brief: An oversized cleaver-like greatsword with a saw-toothed spine, dark steel with red hazard accents and a long two-hand grip. Brutal but clean chunky shapes.

**sword_runic** · TODO — sword_runic 「마석 각인 블레이드」 t5 r2, warrior.
Brief: A long straight blade with cyan glowing engraved lines of gate-stone dust along the flat (patterns, not letters), steel guard, dark grip. The engraving should glow softly.

**sword_tidal** · TODO — sword_tidal 「심해 곡도」 t6 r2, warrior.
Brief: A one-edged curved sabre with a wave pattern glowing teal along the back of the blade, sea-blue grip and a guard shaped like a breaking wave.

**sword_void** · TODO — sword_void 「공허 절단검」 t7 r2, warrior.
Brief: A black blade forged from an abyss core, cracked down the middle so violet light leaks through the fissure; angular black guard.

**sword_conqueror** · TODO — sword_conqueror 「정복왕의 대검」 t8 r3, warrior (job warlord). Direction conflict: data says crown guard.
Brief: A black-and-gold two-hand greatsword with a tall angular spiked guard (a stylised crest of points, not a literal crown) and a dim gold edge glow.

**sword_dawn** · TODO — sword_dawn 「새벽검」 t8 r3, warrior.
Brief: The top Dawn Guild sword: a white-steel straight blade with a rising-sun emblem in gold on the guard and a warm first-light glow along the edge. Clean and heroic, no wings.

**sword_holy_avenger** · TODO — sword_holy_avenger 「성검 홀리 어벤저」 t8 r3, warrior (job paladin). Direction conflict: data says angel-wing guard.
Brief: A bright silver longsword whose guard sweeps up into two stylised blade-fins (wing-like, no feathers), gold core gem, soft holy-white glow.

## Staff family (mage) — 12 models

**staff_oak** · QUEUED — staff_oak 「연습용 마력 완드」 t1, mage.
Brief: A wooden practice wand issued by the hunter academy, simple turned wood with a small clear focus stone. (Queued.)

**staff_crystal** · TODO — staff_crystal 「마석 완드」 t2 r0, mage.
Brief: A long wand of brushed aluminium with a clear faceted gate-stone crystal clamped at the tip in a three-prong holder, rubber grip.

**staff_sage** · TODO — staff_sage 「전술 마력 완드」 t3 r1, mage.
Brief: A tactical casting wand: matte black polymer shaft with a picatinny-rail-style grip section, a blue stone in a protective cage at the tip.

**staff_ruby** · TODO — staff_ruby 「홍염 마력 완드」 t4 r2, mage.
Brief: A slim dark wand with a large red faceted ruby at the tip held by flame-shaped metal prongs, faint red glow.

**staff_bone** · TODO — staff_bone 「뼈 장식 완드」 t5 r2, mage.
Brief: A pale bone-white wand topped by a small horned skull ornament holding a green flame, wrapped dark grip. Keep the skull small, cute-spooky.

**staff_hex** · TODO — staff_hex 「저주의 지팡이」 t5 r2, mage (job warlock).
Brief: A full-length twisted black staff whose head cradles a single violet cursed eye, with thorny loops round it.

**staff_prism** · TODO — staff_prism 「프리즘 지팡이」 t5 r2, mage (job elementalist).
Brief: A full-length silver staff whose head is a clear prism ringed by four small element crystals (red, blue, green, yellow).

**staff_coral** · TODO — staff_coral 「산호 마력 완드」 t6 r2, mage.
Brief: A wand grown from branching pink-orange coral with a sea-glass orb in the fork, sand-worn grip.

**staff_void** · TODO — staff_void 「공허 마력 완드」 t7 r2, mage.
Brief: A black wand with two open metal rings at the tip and a violet void orb floating between them (attach the orb with a thin solid bridge so it stays one mesh).

**staff_abyss_eye** · TODO — staff_abyss_eye 「심연의 눈」 t8 r3, mage (job abyssal).
Brief: A full-length dark staff whose head is a large glowing eye wrapped by chunky tentacles, violet and black.

**staff_arcanum** · TODO — staff_arcanum 「대마도의 지팡이 아르카눔」 t8 r3, mage (job archmage).
Brief: A tall white-and-gold staff topped by a blue orb inside three interlocking orbit rings (rings joined to each other and the shaft).

**staff_starlight** · TODO — staff_starlight 「성광 마력 완드」 t8 r3, mage.
Brief: A top-grade long wand of pale starlight metal with a star-shaped focus and four tiny element stones set round it.

## Bow family (archer) — 12 models

**bow_short** · QUEUED — bow_short 「양궁용 리커브 보우」 t1, archer.
Brief: A beginner sport recurve bow. (Queued.)

**bow_hunter** · TODO — bow_hunter 「사냥꾼 컴파운드 보우」 t2 r0, archer.
Brief: A compact hunting compound bow with cams at both limb tips, olive-drab riser and black limbs, string attached.

**bow_composite** · TODO — bow_composite 「합성 컴파운드 보우」 t3 r1, archer.
Brief: A compound bow with laminated two-tone limbs (carbon black and steel grey), machined riser, stabiliser stub.

**bow_gale** · TODO — bow_gale 「질풍 리커브 보우」 t4 r2, archer.
Brief: A light recurve bow with swept-back aerodynamic limbs in white and mint, wind-stripe decals (no text).

**bow_longshot** · TODO — bow_longshot 「장거리 저격궁」 t5 r2, archer (job sniper).
Brief: A long tactical bow with a telescopic scope mounted on the riser, matte black and grey, very readable long silhouette.

**bow_thornvine** · TODO — bow_thornvine 「가시덩굴 활」 t5 r2, archer (job ranger).
Brief: A bow grown from a living green vine with short thorns and two small leaves at the grip, string of twisted fibre.

**bow_wraith** · TODO — bow_wraith 「사슬 장식 보우」 t5 r2, archer.
Brief: A pale bone-coloured bow bound with short chunky chain wraps, faint blue spirit glow at the limb tips.

**bow_tide** · TODO — bow_tide 「심해 보우」 t6 r2, archer.
Brief: A bow whose limbs spread like translucent fish fins in teal and deep blue, pearl-white grip.

**bow_void** · TODO — bow_void 「공허 보우」 t7 r2, archer.
Brief: A black thorned bow with violet pulse lines running along the limbs.

**bow_heavens** · TODO — bow_heavens 「천공의 활」 t8 r3, archer (job divine_archer). Direction conflict: data says wing limbs.
Brief: A white-and-gold bow whose limbs are stylised layered blade-fins (wing-like, no feathers), soft golden light at the riser.

**bow_nightfall** · TODO — bow_nightfall 「황혼의 활」 t8 r3, archer (job shadow_stalker).
Brief: A black recurve bow with short blades at both limb tips and dusk-purple edge glow.

**bow_star** · TODO — bow_star 「유성 보우」 t8 r3, archer.
Brief: A gate-stone bow with a glowing meteor crystal set in the riser and silver limbs streaked like a falling star.

## Mace family (cleric) — 12 models

**mace_wood** · QUEUED — mace_wood 「구급 지팡이」 t1, cleric.
Brief: A modest wooden walking staff for a rookie medic, with a small first-aid pouch tied near the top. (Queued.)

**mace_silver** · TODO — mace_silver 「의료용 메이스」 t2 r0, cleric.
Brief: A short rescue mace: white aluminium shaft, rounded silver head with a red-cross plate on each face (cross symbol only, no text).

**mace_blessed** · TODO — mace_blessed 「축복의 메이스」 t3 r1, cleric.
Brief: A flanged mace in white and pale gold with a soft green healing glow in the head.

**mace_saint** · TODO — mace_saint 「성자의 홀」 t4 r2, cleric.
Brief: A sceptre-rod in white metal with a round prayer-bead cluster at the top and a gold ring collar, gentle glow.

**mace_grace** · TODO — mace_grace 「은총의 백합 홀」 t5 r2, cleric (job priest).
Brief: A slim white sceptre topped by a chunky golden lily bloom (thick petals).

**mace_purifier** · TODO — mace_purifier 「정화의 철퇴」 t5 r2, cleric (job exorcist).
Brief: A spiked iron flail-head mace with yellow paper talismans wrapped round the shaft (solid shapes, no letters).

**mace_requiem** · TODO — mace_requiem 「진혼의 쇠추 망치」 t5 r2, cleric.
Brief: A hammer with a short chunky chain and an iron plumb weight hanging from the head, muted silver and blue.

**mace_pearl** · TODO — mace_pearl 「진주 조개 메이스」 t6 r2, cleric.
Brief: A mace whose head is an open scallop shell holding a large glowing pearl.

**mace_judgment** · TODO — mace_judgment 「심판의 전쇠」 t7 r2, cleric.
Brief: A black-and-gold war hammer, blunt face on one side and a spike on the other, with a balance-scale emblem on the cheek.

**mace_dawn** · TODO — mace_dawn 「새벽의 홀」 t8 r3, cleric.
Brief: The Dawn Guild sceptre: white shaft with a gold rising-sun disc head and warm light rays sculpted as solid fins.

**mace_seraph** · TODO — mace_seraph 「세라핌의 홀」 t8 r3, cleric (job saint). Direction conflict: data says six wings and a double halo.
Brief: A white sceptre whose head carries six stylised blade-fins in three pairs and two thin gold emitter rings (rings attached, no feathers).

**mace_verdict** · TODO — mace_verdict 「판결의 망치」 t8 r3, cleric (job inquisitor).
Brief: A giant judge's gavel bound with iron bands, dark wood head and gold caps, used two-handed.
