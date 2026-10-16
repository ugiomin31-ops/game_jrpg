# Dungeon environment — brief catalog (per tileset)

Source of truth: piece builders under `Blender/environment/` (hunter_kits/{subway,factory,cave}.py,
hunter_kits_b/{school,hospital,guild_street}.py, verdant_ruins/build_verdant_ruins.py + frost_grotto/kit.py (both use
`NorthernKit` in `_kit_interact_a.py`), haunted_crypt/kit.py, ember_caverns/kit.py). Installed pieces:
`Assets/_Game/Resources/Art/Environment/<tileset>/<piece>.fbx`. Every tileset has the same 27 pieces. Tilesets used in
`dungeon.json`: subway (z1), verdant_ruins (z2), factory (z3), frost_grotto (z4 and z10), cave (z5), ember_caverns
(z6 and Red Gate), school (z7), haunted_crypt (z8 and z12), hospital (z9), guild_street (z11). Generated 2026-10-11.

**Briefed (non-tiling) pieces per tileset (15):** decor_1…6, chest, lore_stone, spring, torch, trap, warp,
foe_marker, overlay_1, overlay_2. 10 × 15 = 150; 2 done (subway/decor_1, factory/decor_1) → **148**. The three
hunter_kits_b foe_markers are one shared design → **146 unique generations**.

**Tiling / structural — decide later (12 per tileset, 120):** floor_a/b/c, wall_a/b/c, door, door_locked,
stairs_up, stairs_down, boss_gate, arena. They have to meet the 4 m grid, the wall shell (±2.0) or exact floor heights,
and doors/boss gates carry hinged `Door`/`Lock` children (`hunter_kits_b/common_b.py` make_door). Keep them
procedural unless main picks a special workflow. Short notes are at the end.

## Special handling for briefed pieces (Blender step after Tripo; keep the empties)
- **chest**: the runtime opens a separate `Lid` object hinged at the back top edge (`_kit_interact_a.py:141-163`).
  Split the Tripo mesh into body + Lid in Blender and set the Lid origin on the hinge.
- **trap**: 2 objects, a floor plate plus a moving spike part that sits retracted 0.5 m below (`_kit_interact_a.py:179-193`).
  Split the spikes off.
- **torch / spring / warp / foe_marker**: re-create the empties `LightAnchor*`, `Spot_warp`, `Spot_foe`
  (`_kit_interact_a.py:208-233, 312-318`).
- **overlay_1/2**: wall decals that hug the −Y face of a wall block (y −2.0 … −2.35, up to ~4.4 m tall). Model them
  flat-backed; they must fit a 4 m wall face.
- **decor_n**: freestanding, footprint well under one 4 m cell (placed 1.45 m + 1 m off the wall per
  `hunter_kits_b/school.py` corridor rule).
- Prompt frame for props: `README.md` §Prompt frame (prop). Toon, chunky, readable at phone size, plain background,
  no text (signs use abstract stroke shapes).

---

## subway (zone 1)
| piece | now | brief |
|---|---|---|
| decor_1 | ticket gate | **DONE** (Tripo, `.tripo` marker) |
| decor_2 | KayKit bench | A stainless subway platform bench with three moulded seats and a green line-2 stripe on the backrest. |
| decor_3 | grey bin + trash bag | A round station waste bin with a recycling split lid and a tied trash bag slumped beside it. |
| decor_4 | red vending machine | A Korean station drinks vending machine: red cabinet, lit product window with rows of cans, coin slot panel. |
| decor_5 | broken escalator | A short broken escalator section, top step missing, bent black handrail, yellow step edges. |
| decor_6 | station number pillar | A white tiled column with two line-colour bands and a round navy station-number sign on top (number shape, no letters). |
| chest | olive box, red mark | An olive-green emergency supply box with a red cross plate and latches (lid separate). |
| lore_stone | white kiosk + blue screen | A station information kiosk with a glowing blue touch screen (abstract map shapes). |
| spring | white cabinet + green panel | A wall-standing emergency AED/first-aid cabinet with a green glowing panel. |
| torch | wall fluorescent lamp | A wall-mounted fluorescent tube lamp in a white housing, slight flicker grime. |
| trap | floor plate | A cracked tactile-tile floor plate with a pit of short rift spikes. |
| warp | steel disc | A round steel floor hatch ringed by violet gate light. |
| foe_marker | red-brown disc | A floor ring with violet rift cracks and a small floating gate crystal (attached by a glow column). |
| overlay_1 | violet crack + rubble | A violet gate crack running up a tiled wall with fallen tile rubble at the base. |
| overlay_2 | fire-hose cabinet + fuse box | A red fire-hose cabinet with two conduits rising to the ceiling and a small grey fuse box. |

## factory (zone 3)
Note: the script's decor_1 is a conveyor, but the installed Tripo decor_1 is a steel cabinet
(`ArtSource/terrain/factory_cabinet`). The conveyor now has no piece. Brief it as an extra (decor_1b) only if main wants it back.
| piece | now | brief |
|---|---|---|
| decor_1 | conveyor (script) / cabinet (installed) | **DONE** |
| decor_2 | machine press | A hydraulic machine press: steel base, column frame, piston head, round gauge, hazard stripes. |
| decor_3 | three oil drums | Three dented oil drums, two upright and one on its side, rolled bands, oil drips. |
| decor_4 | forklift-like cart | A small yellow pallet forklift cart with two forks, a seat and small wheels. |
| decor_5 | crates + cargo box | Stacked wooden crates with a loose lid next to a plastic cargo box of gate stones. |
| decor_6 | dumpster + cabinet | A green industrial dumpster with a closed lid and rust patches. |
| chest | (procedural) | A steel toolbox crate with yellow corner guards and a hazard-stripe band (lid separate). |
| lore_stone | safety notice board | A safety notice board on a steel post with a yellow hazard header (no text). |
| spring | coolant tap station | A blue coolant water tank on a steel stand with a pipe, a tap and a glowing gauge. |
| torch | **DONE** (Tripo, `.tripo` marker) | An industrial dome cage lamp on a wall arm with a chain. |
| trap | spiked hazard plate | A floor plate with a hazard-stripe border and rusted spikes. |
| warp | gear pad | A large steel gear ring set in the floor with an orange glowing core. |
| foe_marker | (procedural) | A hazard-stripe floor ring with violet rift cracks and a small floating gate crystal. |
| overlay_1 | pipe bundle + hazard plate | A bundle of flanged pipes running up a wall with a hazard plate at the foot. |
| overlay_2 | electric box + gauge | A grey electrical box with a warning sticker (symbol only) and a rusted round gauge. |

## cave (zone 5)
| piece | now | brief |
|---|---|---|
| decor_1 | ore mine cart | A mine cart on a short stub of track, timber rim, iron body, heaped copper ore. |
| decor_2 | timber mine support | A timber mine support frame: two posts, a cap beam and diagonal braces. |
| decor_3 | miner's lantern on post | A miner's lantern on a wooden post, warm glass box under a cap. |
| decor_4 | giant cave mushrooms | A cluster of giant pale-stalked cave mushrooms with coloured caps, two glowing. |
| decor_5 | boulder pile | A pile of limestone boulders with ochre strata. |
| decor_6 | crystal cluster | A cluster of five blue and violet gate crystals, glowing. |
| chest | (procedural) | A miner's ore crate banded with iron, a crystal chip on the lock plate (lid separate). |
| lore_stone | (procedural) | A survey marker stone with a glowing crystal vein and a nailed survey tag. |
| spring | rock basin | An underground spring: a rock basin of still water with crystals at the rim. |
| torch | miner's lantern on bracket | A miner's lantern on an iron wall bracket. |
| trap | stalagmite spike pit | A pit of stalagmite spikes with glowing crystal chips. |
| warp | crystal portal ring | A ring of standing crystals around a glowing violet pool. |
| foe_marker | (procedural) | A rock-rimmed floor ring with violet crystal shards and a floating gate crystal. |
| overlay_1 | wall crystal + vein | A crystal cluster growing out of the wall with a vein of violet light. |
| overlay_2 | stalactite row | A row of stalactites along the top of the wall with a water drip. |

## school (zone 7)
| piece | now | brief |
|---|---|---|
| decor_1 | desk + chair + books | A Korean classroom desk with its chair pulled out and a stack of textbooks (no text). |
| decor_2 | chalkboard easel | A small chalkboard on an easel with a chalk tray and doodles. |
| decor_3 | three potted tulips | Three potted tulip-like plants in plastic classroom pots. |
| decor_4 | sports bags + basketball | Two school sports bags and a basketball. |
| decor_5 | festival booth | A school-festival booth: striped canopy, counter, blank sign board, two paper lanterns. |
| decor_6 | stools + mop bucket + sign | A yellow mop bucket with a mop and a wet-floor A-sign (symbol only). |
| chest | (procedural) | A festival prize box wrapped like a gift with a ribbon (lid separate). |
| lore_stone | campus notice board | A campus cork notice board on legs with pinned notices (blank) and violet rune scratches on top. |
| spring | nurse corner | A school nurse corner: a cot, a first-aid cabinet and a water cooler. |
| torch | paper lantern on pole | A festival paper lantern on a school pole. |
| trap | (procedural) | A broken floor tile patch with spiky splinters and a violet crack. |
| warp | violet portal on dais | A standing oval violet gate portal on a stone dais with a rune ring. |
| foe_marker | shared (violet ring, 6 shards, floating crystal) | **Shared model** with hospital and guild_street: a violet floor ring, six crystal shards and a floating gate crystal. |
| overlay_1 | garland + paper lanterns | A festival garland of pennants and paper lanterns draped along the top of a wall. |
| overlay_2 | two calligraphy banners | Two hanging festival banners from a bamboo pole with abstract brush strokes (no readable text). |

## hospital (zone 9)
| piece | now | brief |
|---|---|---|
| decor_1 | ward bed | A hospital ward bed with a mint blanket and white pillow, side rails. |
| decor_2 | IV stand | An IV drip stand with a glowing drip bag on a round wheeled base. |
| decor_3 | wheelchair | A wheelchair with big blue wheels and a footrest. |
| decor_4 | medicine cart | A white three-shelf medicine cart with bottles and a drawer. |
| decor_5 | potted plant | A lobby potted plant: white pot with a blue band and big mint-green leaves. |
| decor_6 | A-frame sign + wet floor | An A-frame hospital sign stand with a red cross beside a wet-floor sign (symbols only). |
| chest | (procedural) | A white medical supply case with a red cross and steel clasps (lid separate). |
| lore_stone | patient info board | A patient information board: white chart with blue rules, a red cross and faint mint runes. |
| spring | recovery corner | A recovery corner: a made bed, an IV stand with a glowing bag and a mint healing ring. |
| torch | reading lamp | A slim warm reading lamp on a stand. |
| trap | syringe spikes | A floor plate with upright giant syringes as spikes. |
| warp | portal on white dais | A violet gate portal standing on a clean white dais. |
| foe_marker | shared | Same model as school/foe_marker. |
| overlay_1 | curtain rail + curtain | A ceiling curtain rail with a pastel ward curtain (wavy hem). |
| overlay_2 | hanging ivy | Hanging ivy in mint and green tumbling from the wall top. |

## guild_street (zone 11)
| piece | now | brief |
|---|---|---|
| decor_1 | striped road barricade | A red-and-white striped road barricade with a plank and two legs. |
| decor_2 | three traffic cones | Three orange traffic cones with reflective bands. |
| decor_3 | crashed car | A small sedan crashed nose-first into a barrier, crumpled bonnet (2.4 m long). |
| decor_4 | dumpster + trash + crates | Street bins: a dumpster, trash bags and two wooden crates. |
| decor_5 | A-frame shop standee | An A-frame shop standee with a blank board and a small guild sun emblem. |
| decor_6 | planter with bushes | A concrete street planter with three round bushes. |
| chest | (procedural) | A delivery parcel crate stamped with a guild sun emblem (lid separate). |
| lore_stone | wanted-poster board | A steel-post board of wanted posters (monster silhouettes, no text) with violet rune scratches. |
| spring | health vending machine | A green-glowing health-potion vending machine next to a bench, with a healing ring on the pavement. |
| torch | street lamp 3.4 m | A Seoul street lamp, 3.4 m tall, with a curved head. |
| trap | road spike strip | A road spike strip on a dark plate. |
| warp | cracked plate + rift arch | A cracked round road plate with a violet rift arch standing in the middle. |
| foe_marker | shared | Same model as school/foe_marker. |
| overlay_1 | striped awning | A striped shop awning sticking out from the wall top. |
| overlay_2 | power cables + paper signs | Sagging power cables along the wall top with two small blank paper signs. |

## verdant_ruins (zone 2, E-rank gate forest) — NorthernKit(frozen=False)
| piece | now | brief |
|---|---|---|
| decor_1 | **DONE** (Tripo, `.tripo` marker) | A clump of ferns, ginkgo saplings and a few small green crystals. |
| decor_2 | **DONE** (Tripo, `.tripo` marker) | A broken mossy stone column with a fallen fluted drum beside it. |
| decor_3 | **DONE** (Tripo, `.tripo` marker) | A small shallow pool ringed with mossy stones and lily pads. |
| decor_4 | **DONE** (Tripo, `.tripo` marker) | A mossy stone urn on a plinth with a sprouting plant. |
| decor_5 | **DONE** (Tripo, `.tripo` marker) | A fallen carved stone lintel with rubble and grass. |
| decor_6 | **DONE** (Tripo, `.tripo` marker) | A small mossy stone wayfinder idol with a glowing green gem. |
| chest | **DONE** (Tripo, `.tripo` marker) | A moss-covered stone chest with root bands (lid separate). |
| lore_stone | **DONE** (Tripo, `.tripo` marker) | A mossy stone stele with a glowing green rift line. |
| spring | **DONE** (Tripo, `.tripo` marker) | A clear spring pool with a cyan glowing ring. |
| torch | **DONE** (Tripo, `.tripo` marker) | A stone post brazier with a warm flame. |
| trap | **DONE** (Tripo, `.tripo` marker) | A mossy floor slab with thorny root spikes. |
| warp | **DONE** (Tripo, `.tripo` marker) | A ring of mossy standing stones around a green-violet glow. |
| foe_marker | **DONE** (Tripo, `.tripo` marker) | A floor ring of moss with a floating orange gate crystal. |
| overlay_1 | **DONE** (Tripo, `.tripo` marker) | Ivy and flowering vines hanging from the wall top. |
| overlay_2 | **DONE** (Tripo, `.tripo` marker) | Thick roots creeping down the wall face. |

## frost_grotto (zone 4 ice gate; zone 10 sunken temple reuses it) — NorthernKit(frozen=True)
Briefs should also read as a sunken sea temple (zone 10): ice plus shell and coral hints.
| piece | now | brief |
|---|---|---|
| decor_1 | crystal garden | A cluster of ice crystals with frosted coral branches. |
| decor_2 | broken fluted column | A broken blue-stone column with an ice-crusted fallen drum. |
| decor_3 | frozen pool | A small frozen pool with cracked ice and a stone rim. |
| decor_4 | shrine urn | A frost-covered stone urn with shell inlays. |
| decor_5 | fallen lintel + rubble | A fallen carved lintel half buried in snow. |
| decor_6 | frozen wayfinder idol | A small idol encased in clear ice with a blue glow. |
| chest | hollow stone chest | An ice-crusted stone chest with a frosted lid (lid separate). |
| lore_stone | (stele) | A frosted stele with a glowing cyan rift line. |
| spring | glowing ring pool | A thawed spring pool with a glowing cyan ring amid the ice. |
| torch | crystal cluster lamp | A stone post topped by a glowing ice-crystal cluster. |
| trap | **DONE** (Tripo, `.tripo` marker) | A floor slab with icicle spikes. |
| warp | **DONE** (Tripo, `.tripo` marker) | A ring of ice pillars around a blue glowing pool. |
| foe_marker | orange bipyramid | A frosted floor ring with a floating ice-blue gate crystal. |
| overlay_1 | icicle row | A row of icicles along the wall top. |
| overlay_2 | (frost, sparse) | Frost and small ice crystals creeping down the wall face. |

## haunted_crypt (zone 8 B-gate; zone 12 abyss reuses it)
Direction: gate tomb, Korean stone-tomb hints, violet soul fire; skulls stay cute.
| piece | now | brief |
|---|---|---|
| decor_1 | coffin, lid shoved aside | A stone coffin with its lid shoved aside and purple light leaking out. |
| decor_2 | bone pile with skulls | A cute bone pile with three round skulls. |
| decor_3 | candle cluster on wax | A cluster of violet-flame candles on a wax puddle on a stone step. |
| decor_4 | leaning gravestones | Two leaning rounded gravestones (no crosses, no text). |
| decor_5 | jack-o'-lanterns | Flag: jack-o'-lanterns are off-theme in a tomb. Replace with a Korean stone lantern (seokdeung) with a violet flame. |
| decor_6 | soul urn + wisp | A stone urn on a plinth with a teal ghost flame and an orbiting wisp (wisp attached by a glow trail). |
| chest | (procedural) | A dark stone reliquary chest with violet rune seams (lid separate). |
| lore_stone | cross-diamond rune stone | A tomb stele with a glowing teal diamond rune (no cross). |
| spring | obelisk + soul wisps | A small stone obelisk over a basin of glowing teal soul water. |
| torch | skull post + brazier | A skull-faced stone post with an iron brazier of violet soul fire. |
| trap | (procedural) | A cracked slate floor with bone spikes. |
| warp | (procedural) | A sunken stone circle with a violet soul vortex. |
| foe_marker | (procedural) | A cracked floor ring with violet soul light and a floating crystal. |
| overlay_1 | big cobwebs + spider | Big corner cobwebs with a small cute spider. |
| overlay_2 | iron rod + violet banners | An iron rod with three tattered violet cloth strips (no emblems). |

## ember_caverns (zone 6 C-gate; Red Gate reuses it)
| piece | now | brief |
|---|---|---|
| decor_1 | clay urns | Two clay urns with zigzag bands. |
| decor_2 | broken temple pillar | A broken sandstone temple pillar with carvings and a fallen drum. |
| decor_3 | small lava pool | A small lava pool ringed by basalt with crust floes. |
| decor_4 | obsidian crystal cluster | An obsidian crystal cluster growing from basalt, glowing orange at the roots. |
| decor_5 | desert agave | A desert agave on a sand mound. |
| decor_6 | sun idol altar | A stepped altar with an upright gold sun disc and offering flames. |
| chest | half-cylinder lid, diamond lock | A sandstone chest with a half-round lid and a diamond lock plate (lid separate). |
| lore_stone | rune stele | A sandstone stele with glowing runes on both faces (abstract). |
| spring | sun-bowl fountain | A round basin of glowing teal water with a central pillar and a gold sun bowl spilling water. |
| torch | (procedural) | A basalt brazier post with a lava-orange flame. |
| trap | spike plate | A rust-red floor plate with dark cone spikes. |
| warp | four obelisks + rune ring | Four small obelisks with glowing tips around a floating rune ring (ring attached to the obelisks). |
| foe_marker | (procedural) | A basalt floor ring with lava cracks and a floating gate crystal. |
| overlay_1 | lava stalactite ledge | A rock ledge along the wall top dripping lava stalactites. |
| overlay_2 | lavafall | A lavafall pouring from a fissure down the wall into a small pool. |

---

## Tiling / structural — decide later (not briefed for Tripo)
**Superseded 2026-10-12** by `environment_tiling.md` (walls, floors, door_locked, boss_gate via image → Tripo; stairs
re-skinned). chest, lore_stone, spring and warp are now scheduled as artifacts (`artifacts.md`); their briefs stay here.
Per tileset: floor_a, floor_b, floor_c (grid floor + ceiling root), wall_a, wall_b, wall_c (4 m blocks, face details
to ±2.0), door / door_locked (frame + hinged `Door` leaf + `Lock`), stairs_up / stairs_down (exact 2.5 m landing),
boss_gate (sealed cell gate, `Spot_boss`), arena (battle stage ring: floor, backdrop, ceiling, props).
Known current looks: subway screen doors / station stairs / steel shutter boss gate; factory roller shutter / steel
catwalk stairs / press shutter; cave timber mine gate / rock steps / crystal-seal rock barrier; school sliding classroom
door, teachers' office door; hospital ward faces, nurse hatch; guild_street shop blocks, guild banner block, cracked
brick block; haunted_crypt hooded-statue rune veil; ember_caverns flame-bowl pylons with a sun seal; NorthernKit carved
arch boss gate. If main later wants Tripo here, boss_gate (one per tileset, very visible, no tiling) is the best first
candidate, after splitting off the hinge and seal parts.
