# Dungeon tiling — walls, floors and structural set pieces through image → Tripo

Written 2026-10-12 (planner). Replaces the "Tiling / structural — decide later" section of `environment.md` (that file
keeps the 15 non-tiling props per tileset). Sources: `Scripts/Runtime/World/DungeonWorld.cs`,
`Scripts/Runtime/World/EnvironmentProcessor.cs`, `Scripts/Logic/Dungeon/DungeonGrid.cs:21`,
`Blender/environment/hunter_kits/common_a.py` (contract docstring 1-20, constants 39-49, `run_hunter_pieces` 372-395),
`Blender/environment/_pipeline.py`, `Blender/environment/arch_geo.py:26`, `hunter_kits/subway.py` (door 220-255,
stairs 259-278, boss_gate 353-366), `Resources/Data/dungeon.json` (39 floors).

## 1. How a dungeon floor is assembled (findings)

- **Grid crawler, not physics.** `DungeonWorld.Initialize` (57-130) walks the `rows` grid: `#` → `wall_<v>` only when
  it touches an open cell (75); every open cell gets `floor_<v>` except `>` (79); markers spawn `chest` (T), `door_locked`
  (L, rotated 90° when its N and S neighbours are walls, 88-90), `stairs_down` (>), `stairs_up` (<), `spring` (H),
  `warp` (W), `lore_stone` (N), `trap` (X), `boss_gate` (B), shared `Props/Common/key_item` (K); torches every ~9th
  cell against a wall; `Dress` adds decor/overlays. Variant `v = (x·17 + y·31) mod 3` → a/b/c, **for walls and floors**.
- **No rotation for walls, floors, stairs or boss gates.** Every wall block can show any of its 4 faces; floors are never
  rotated; stairs always rise toward north; boss gates always span the X axis.
- **Movement and the camera are grid logic** (`Position(cell) = (4x, 0, −4y)`, camera at cell centre +1.35 m, 90°
  turns, FOV 65). No `Physics` call in dungeon code (the only one is `TownWorld.cs:303`). `EnvironmentProcessor`
  strips `Col_*` renderers and collects colliders, but the dungeon does not use them. **Tiling pieces need no colliders.**
- **Kit contract** (`common_a.py:1-20, 39-49`): 1 cell = 4 m; Blender X = Unity X, Unity Z = −Blender Y, north = −Y.
  Floor top at z = 0, floor vertices clamped to |x|,|y| ≤ 2 and z ≤ 0 (raised detail must be flush, relief goes *down*);
  walls are rescaled to exactly [−2, 2]² × [0, 4.5] (`WALL_H = 4.5`, core at `SHELL = 1.98`, details to 2.0);
  ceilings at `CEIL = 4.48` ride on floor pieces as a `Ceiling` root object (hunter kits: subway, factory, cave; the
  Northern/crypt/ember kits per their scripts); torches 1.7 m from the cell centre.
- **Doors**: frame fills the cell (x ±2, depth y ±1, lintel from z 3.12), opening x ∈ [−1, 1]; leaf `Door` hinged at
  x = −1 opens yaw +95 (`RefreshProgress` 298); `Lock` parented to the leaf. The plain `door` piece is **not spawned**
  anywhere (only `door_locked`; `door` is still required by `AbyssProjectSetup.cs:116`) → do not spend credits on it.
- **Stairs**: `stairs_up` = steps rising to a 2.5 m landing over y ∈ [−2, 0]; `stairs_down` = half floor at y ∈ [0, 2]
  plus 5 steps descending to z −2.5 over y ∈ [−2, 0] (it replaces the floor tile).
- **Arena** (battle stage, `BattleView.cs:100`): 9.4 m disc, backdrop ring to r ≈ 10.2, ceiling 9.0 — separate,
  not part of this plan (zero-credit reskin idea in §8).
- **Counts** (all 39 floors): `#` 12,833 · open 7,711 · up to **350 visible wall blocks and 375 floor tiles per floor**
  (19×19 maps). L 85, B 13, `<` 39, `>` 38. Importer caps Tripo environment textures at **1k**
  (`AbyssArtImporter.cs:168-170`) → 256 px/m on a 4 m face, fine at phone resolution.

## 2. The tiling contract

| item | rule |
|---|---|
| grid | 4.000 m cells; piece origin = cell centre on the floor (0, 0, 0) |
| wall block | bbox exactly x, y ∈ [−2, 2], z ∈ [0, 4.5]; built from **4 face modules** (below) on a hidden core box ±1.80 |
| wall face module | one 4.0 m wide × 4.5 m tall relief slab; back plane at d = 1.80, front relief ≤ d = 2.00 (0.20 m deep) |
| face naming | each block exports 4 child objects `Face_N` (−Y), `Face_S` (+Y), `Face_E` (+X), `Face_W` (−X) + `Core` (for hook E-H1) |
| seam band (walls) | the outer 0.12 m at the left/right edges is **flat at d = 1.98** (no relief); the bottom 0.25 m is a flat skirting at d = 1.98 for the whole width; the top 0.30 m is a flat cap band. Neighbouring blocks and outer corners then meet on identical flat planes |
| floor tile | x, y ∈ [−2, 2], top at z = 0, recessed relief only (grout, cracks, drains ≤ 0.08 m deep), underside closed at z = −0.3 |
| seam band (floors) | vertices within 0.15 m of any edge snap to z = 0 (flat border) |
| UVs | **planar projection of the processed source image, not Tripo's atlas**: walls u = (x+2)/4, v = z/4.5 on each face's local axes; floors u = (x+2)/4, v = (y+2)/4. Same formula on every piece, so seams line up |
| texture | walls: horizontally **wrap-seamless** (left edge continues into right edge); floors: seamless on both axes. 1024² PNG per module (importer cap), sRGB. Albedo only, lighting baked flat (no shadows, no highlights) |
| material | Abyss/Toon via the Tripo importer path (`.tripo` marker next to the FBX), one material per module texture |
| triangles | face module ≤ 1,000 → wall block ≤ 4,200 (4 faces + core); floor ≤ 1,000 + existing `Ceiling`; door_locked ≤ 4,000; boss_gate ≤ 8,000 |
| colliders | none (no `Col_*` objects) |
| kept objects | floor pieces keep the current `Ceiling` object and any `LightAnchor*` from the existing FBX; door keeps `Door` + `Lock`; boss_gate keeps `LightAnchor_gate_*` and `Spot_*` empties |
| GUID | overwrite `Art/Environment/<tileset>/<piece>.fbx` in place, keep `.fbx.meta`; marker `<piece>.tripo` created first; backup old FBX to `ArtSource/terrain/<tileset>/<piece>/backup_YYYYMMDD/` |

## 3. Getting Tripo output to tile (per tileset)

**Credit plan per tileset: 8 Tripo generations** (55 + retopo 35 = 90 each → 720): `wall_base`, `wall_accent`,
`floor_base`, `floor_accent`, `door_locked`, `boss_gate`, `stairs_up`, `stairs_down`. Variants are composed, not generated:
- `wall_a` = base on all 4 faces; `wall_b` = base N/S + accent E/W; `wall_c` = accent N/S + base E/W.
- `floor_a` = floor_base; `floor_b` = floor_base mesh rotated 90° about Z with UVs re-projected (still seamless);
  `floor_c` = floor_accent.
- `stairs_up` / `stairs_down`: **made with Tripo too** (decision D5, supersedes the earlier procedural-reskin idea):
  1 generation each (image: straight side/three-quarter orthographic view of the stair run, per tileset brief).
  The Blender step must still hit the exact contract: `stairs_up` rises to a 2.5 m landing over y ∈ [−2, 0] with
  the rest of the cell flat at the landing height; `stairs_down` = half floor at y ∈ [0, 2] plus 5 steps descending to
  z −2.5 over y ∈ [−2, 0] (opening, no floor cap). Always rises toward north; cell bounds x, y ∈ [−2, 2].

**Step 1 — images (ChatGPT web, 4 candidates per module).** Frames:
- *Wall module*: "Generate FOUR separate images… one straight-on **orthographic front elevation** of a 4 m wide ×
  4.5 m tall dungeon wall section for a chunky stylised toon 3D game set in present-day Seoul: <brief>. Perfectly
  frontal, no perspective, no vanishing lines, even flat lighting, no shadows. The wall fills an 8:9 rectangle centred
  on a plain mid-grey canvas with margins. Shallow relief only (max 20 cm). A plain flat 25 cm skirting band along the
  bottom and a plain flat 30 cm cap band along the top, both full width. The left and right edges are plain flat
  bands and the pattern continues seamlessly from the right edge into the left edge. No text, letters, numbers,
  logos, runes or signs, no people, no props standing in front, 1:1."
- *Floor module*: "…one straight **top-down orthographic** view of a square 4 × 4 m dungeon floor section: <brief>.
  Seamless tileable on all four edges, perfectly overhead, no perspective, even flat lighting, no shadows, only
  recessed detail (grout lines, cracks, drains), plain flat border joints, fills the whole square, no text or symbols, 1:1."
- *Door / boss gate*: the prop frame from `README.md` but **straight front view**, "the doorway fills a 4 m wide ×
  4.5 m tall rectangle, closed door, the frame meets the floor flat, symmetric, no text".

**Step 2 — pick + seam test (no credits).** Crop to the wall rectangle / floor square, make it wrap-seamless (offset by
half, blend a 48 px seam, Pillow; script lives outside the repo or under `Tools/art/`), and render a 3×1 (walls) /
2×2 (floors) tiled preview. Haiku pre-checks, main approves. Reject candidates with perspective or baked shadows.

**Step 3 — Tripo** image → 3D (H3.1, Geometry & Texture, 55) on the **cropped, seamless image**; Retopo Triangle
Smart Mesh at the lowest target (35). No rig. Export FBX. Close the tab.

**Step 4 — Blender (headless, Sonnet worker; new script `Blender/environment/tripo_tiles.py`)**:
1. Orient: a wall module is authored as the north face (`Face_N`): front toward −Y, back plane at y = −1.80, relief
   out to y = −2.00, x ∈ [−2, 2], z ∈ [0, 4.5]; the other faces are its copies rotated 90/180/270° about Z. Floor top → +Z. Scale to 4.0 × 4.5 (wall) / 4.0 × 4.0 (floor) from the bbox of the
   front/top surface.
2. Keep only the visible shell: delete faces whose normal points away from the front (back/underside), then
   **bisect** at x = ±2 and z = 0 / 4.5 (walls) or x, y = ±2 (floors) and delete outside geometry.
3. Clamp relief: walls d ∈ [1.80, 2.00]; floors z ∈ [−0.08, 0]. **Snap** seam bands (§2) flat; snap verts within 2 cm
   of a bound onto the bound.
4. Close: wall back plane at d = 1.80; floor underside at z = −0.3 with side skirts.
5. Decimate (planar 3°, then collapse) to the budget; recalc normals outward; smooth shading off for toon.
6. Planar UV per §2; assign the processed seamless PNG as the only texture (`<piece>_tex/`), material `M_<piece>`.
7. Assemble: wall_a/b/c blocks from the two modules (4 rotated copies each, named `Face_*`, + `Core` box 3.6 × 3.6 ×
   4.5 hidden inside), 4 corner posts are *not* needed because seam bands meet flush. Floor a/b/c from the two slabs;
   re-attach the current `Ceiling` (import from the existing FBX). Door: split `Door` leaf (x ∈ [−1, 1],
   z ∈ [0, 3.1], origin at hinge x = −1) and `Lock` (parented to `Door`); fill the opening behind the leaf.
   Boss gate: re-add the existing empties at their old positions.
8. Validate (script asserts): bbox, face names, tri counts, no verts outside bounds, UV range [0, 1], seam vertices
   on the band planes. Export FBX (Unity axes, scale 1). Render a 3×3 test layout (corridor with a corner, a T-junction,
   a door and stairs) to PNG for the reviewer.

**Step 5 — install + VERIFY**: marker, backup, overwrite in place; Unity reimport; dungeon capture (540×960) at
1-1: straight corridor, outer corner, T-junction, door_locked closed/open, stairs, boss gate, torch light on the new
walls; look for seams, z-fighting with overlays (overlay pieces hug the −Y face at y −2.0…−2.35, so the new front at
d ≤ 2.0 keeps them clear), floating decor (decor stands on z = 0), torch backs touching the wall at 2.0. Frame time
vs the procedural build within +15 %.

## 4. Code hooks (small)

| id | file | change |
|---|---|---|
| E-H1 | `DungeonWorld.cs:75` | after `Spawn("wall_" …)`, hide buried faces: for each facing, if the neighbour cell is `#`, `SetActive(false)` on child `Face_<N/E/S/W>` (via `EnvironmentProcessor.Find`); no-op when the children do not exist (procedural walls). Roughly halves wall triangles. Map: N = cell (x, y−1) = Blender −Y, S = (x, y+1), E = (x+1, y), W = (x−1, y). |
| E-H2 (optional, measure first) | `DungeonWorld.cs` | parent walls/floors under one child root and `StaticBatchingUtility.Combine` it after the build (chests/doors/props stay outside). Only if VERIFY frame time fails. |

## 5. Pilot: subway (zone 1) first

Why: first dungeon the player sees, three floors (1-1…1-3), tile-and-panel architecture is the easiest to make seamless,
and the existing subway ticket gate is already Tripo (style match). Sequence: T0 hooks + `tripo_tiles.py` tested on a
placeholder slab → images for the 4 modules → **Tripo wall_base + floor_base only (180)** → Blender → install
`wall_a` + `floor_a` (b/c temporarily = a) → VERIFY → if accepted, `wall_accent`, `floor_accent`, `door_locked`,
`boss_gate` (360) → `stairs_up` + `stairs_down` (180) → full VERIFY of 1-1…1-3. Only then start the next tileset.

## 6. Per-tileset briefs

`base` = the plain, most common surface; `accent` = same materials with one feature (it shows on a third of the cells).
Ceilings stay as built. Hunter-genre direction: present-day Korea, gate-rift violet/blue cracks are the only "magic";
no runes, text, heraldry, crowns or medieval motifs.

| tileset (zones) | wall_base | wall_accent | floor_base | floor_accent | door_locked | boss_gate |
|---|---|---|---|---|---|---|
| subway (1) | glossy white square wall tiles with a line-2 green band at hip height, grime toward the skirting | same tiles with a recessed advertising light-box frame (blank glowing panel) | grey speckled terrazzo platform tiles with a yellow tactile strip along one joint | same terrazzo with a hairline violet gate crack and a square drain grate | steel staff-only door in a tiled frame, push bar, hazard-striped kick plate | heavy steel roller shutter with hazard stripes and two side guide rails |
| verdant_ruins (2) | mossy fitted stone blocks with root tendrils in the joints | same wall with a carved pilaster niche holding a fern | worn stone slabs with grass in the cracks | slabs with a shallow root-lifted crack and moss patch | timber-and-stone door with root bands and an iron latch | ring of root-wrapped standing stones closing a gap, green-violet glow seam |
| factory (3) | corrugated grey steel panels on a concrete dado, rivets, hazard stripe at the skirting | same with a recessed pipe run and a pressure gauge | oil-stained concrete slab with painted yellow walkway lines (no text) | steel checker-plate panel set into concrete | sliding steel fire door with a round window and lever lock | rolling factory shutter with a hydraulic frame and amber beacons |
| frost_grotto (4, 10) | blue-grey stone blocks under clear ice glaze, shell inlays at the cap | same with a frozen waterfall seam | frosted flagstones with snow drifted into joints | cracked ice sheet over stone with trapped bubbles | iced stone door with a frosted iron ring | arch of ice pillars sealed by a cracked ice sheet with blue glow |
| cave (5) | rough limestone strata with ochre bands | same with a crystal vein and timber shoring post | packed earth and flat stone with a mine-rail groove joint | puddled stone with a small embedded crystal cluster | mine gate: timber frame, iron bars, padlock plate | crystal-sealed rock barrier with timber beams |
| ember_caverns (6, Red Gate) | basalt blocks with glowing lava seams in the joints | sandstone relief panel band over basalt | basalt flagstones with ash in the joints | flagstones with a cooled lava-crust crack glowing orange | sandstone door with a sun-disc boss (no symbols) and bronze bands | two flame-bowl pylons with a sealed sandstone slab, sun disc boss |
| school (7) | cream painted corridor wall, mint wainscot, steel handrail strip | same with a bulletin board frame (blank papers) | pale wood-look classroom vinyl planks | vinyl with a violet gate crack and scattered chalk dust | sliding classroom door with a glass window panel and a small lock | teachers'-office double door, reinforced, festival banner remnant (no text) |
| haunted_crypt (8, 12) | dark granite blocks, Korean stone-tomb style coursing, violet soul-light in joints | same with a carved niche holding a candle stub | dark slate slabs with violet moss | slate with a cracked tomb-lid slab inset | stone tomb door with bronze studs and a ring pull | hooded-statue gateway with a violet rift veil between two pillars |
| hospital (9) | white wall panels, mint hip rail, pale-blue skirting | same with a recessed glass-block window (frosted) | speckled white hospital vinyl with a mint direction stripe | vinyl with a floor drain and a faint violet crack | ward door with a narrow window and a keypad box (no digits) | sealed isolation-ward double doors with hazard tape (no text) and a red light |
| guild_street (11) | red brick shop wall with a concrete base course | same with a rolled-down shutter bay | grey street paving blocks with a curb joint line | paving with a manhole cover (blank) and a crack | back-alley steel door with a bar and a padlock | guild-banner block gate: steel frame, sun emblem plate, rift crack |

Total for all 10 tilesets: 80 generations (≈ 7,200 credits); per-tileset art direction checked against the existing
`environment.md` props for that tileset.

## 7. Risks

1. Tripo may round the edges of a straight-on slab or add a thick back; the bisect/snap step fixes geometry, and the
   planar re-projection makes the texture independent of Tripo's atlas.
2. GPT may add perspective or lighting; reject at Step 2 (cheap) rather than after Tripo.
3. Triangle load: up to 350 wall blocks per floor. E-H1 (hide buried faces) is part of T0; E-H2 only if needed.
4. Wall blocks are not rotated, so all four faces show the same module family; variety comes from the a/b/c composition.
5. Overlays (`overlay_1/2`) are authored against the old −Y face; recheck their placement on the pilot.

## 8. Later (not planned)
- Arena reskin at 0 credits: re-project `floor_base` onto the arena disc sectors and `wall_base` onto the backdrop ring.
- Plain `door` piece: unused at runtime; keep the procedural one.
