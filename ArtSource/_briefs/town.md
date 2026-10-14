# Town (새벽 길드 거리 hub) — brief catalog

Source of truth: `Blender/town/guild.py` (current; writes `Assets/_Game/Resources/Art/Town/town.fbx`, docstring lines
1-30). `Blender/town/town.py` is the older "Hearthvale" storybook village and is **superseded** (guild.py keeps only
its marker names). Layout and markers: `Blender/town/markers.json`. Generated 2026-10-11.

## How the town is built today (constraint for Tripo)
`town.fbx` is **one combined FBX**: visual meshes plus `Spot_*` actor markers (spawn, innkeeper, shopkeeper, smith,
guild_clerk, elder, gate, villager_1..3, camera_title), `Col_*` invisible colliders and `LightAnchor*` empties.
`TownWorld.cs` reads the markers by name. Recommended route (main decides): keep guild.py as the layout, collider and
marker source, and have it import each Tripo building/prop FBX at its current transform in place of the procedural
mesh. Then the exported `town.fbx`, its markers and its colliders keep their names and TownWorld needs no change.
The alternative, spawning prefabs in Unity, needs code.

Status for every item: TODO. Footprints are in metres (Blender x, y; height z). Rig: none (static).
Size: buildings 10–20k tris (hero buildings at the top of that range), street props 3–6k. Texture 2k for buildings,
1k for small props.

## One model per distinct building (Tripo, non-tiling)

**guild_hq** · Dawn Guild HQ, back of the plaza. Footprint x −13.5…13.5, y −29…−17.5, h 15.4 (`guild.py:71, 464-538`).
Now: a multi-storey block with pilasters, floor bands, part-lit windows, a crest and a lit "DAWN GUILD" board, glass lobby,
blue-and-cream striped entrance canopy, a reception kiosk under it, a roof beacon. Spot_elder at the door, Spot_guild_clerk
at the kiosk. Split off the canopy and kiosk if they need colliders (Reception_Kiosk collider at `guild.py:527`).
Brief: A modern 4-storey Seoul guild headquarters of glass and pale stone, blue accents, a big gold rising-sun crest over the entrance, a blue-and-cream striped canopy over a glass lobby, a small reception kiosk beside the door, a beacon on the roof. Sign as a blank lit panel (no letters).

**guild_clinic** · infirmary (innkeeper 「윤 간호사 · 의무실」). `CLINIC = (-20.8, -15.6, -3.6, 6.6, 6.8)`, faces +X (`guild.py:77, 540-558`).
Brief: A small 2-storey clinic building with white walls, a mint trim, a glowing green-cross sign board, a glass door and upper windows; a little flag pole beside it.

**guild_market** · hunter market (shopkeeper 「박 사장 · 헌터 마켓」). `MARKET = (15.6, 20.8, -5.6, 2.6, 5.6)`, faces −X (`guild.py:78, 560-573`).
Brief: A corner convenience-store-style hunter shop with a lit sign band (blank), a big shop window showing potion bottles, a striped awning and produce crates out front.

**guild_workshop** · equipment workshop (smith 「곽 장인 · 장비 공방」). `WORKSHOP = (15.6, 20.8, 7.2, 14.0, 6.0)`, faces −X (`guild.py:79, 575-601`).
Brief: A garage-style metal workshop with an open roller-shutter bay showing a furnace glow inside, a wooden sign board (blank), and stacked cargo and a steel workbench beside it.

**gate_portal** · the dungeon gate (Spot_gate) (`guild.py:603-640`). Now: stone pillars with gold caps and an arch, a violet portal ring with a glowing disc, a rune circle, barricades with warning tape, two guard booths.
Brief: A violet gate rift standing in a cordoned-off plaza pocket: a ring of torn space with a glowing disc, framed by two steel pylons (not a stone arch), yellow-black barricades with warning tape. Make the two guard booths a separate model (see below).

**guard_booth** · one model used twice (west and east of the gate).
Brief: A small Korean police/security guard booth: white and navy box, windows on three sides, a little roof light.

**skyline_building_A…H** · 8 background KayKit City buildings, placed in two rows round the block and **stretched
vertically** ×1.0…2.5 (`guild.py:427-450`). Tripo meshes should not be stretched, so generate 4 low/mid-rise and
4 high-rise Seoul blocks at their final proportions (8 models), and keep the north row low for the title camera
(`guild.py` build_skyline comment).
Brief (vary per model): A Seoul apartment or office block in chunky toon style: (A) 5-storey shop-and-office block with signs as blank panels, (B) brick villa with balconies, (C) glass office tower, (D) apartment tower with stripe balconies, (E) small café building, (F) convenience store with offices above, (G) tall glass-and-concrete tower, (H) apartment block with a rooftop water tank.

**fountain** · three-tier stone fountain, ~4.7 m across, centre of the plaza (`guild.py:289`). It collides.
Brief: A modern plaza fountain: a round granite basin with a stepped middle tier and a sculptural sun disc in the centre, light-blue water.

## Street props (one model each, reused at every placement)
| model | now (guild.py) | brief |
|---|---|---|
| food_cart | street food stall 2.2 m, striped awning (`food_cart`) | A Korean street-food cart (tteokbokki/odeng style) with a striped awning on four posts, steaming pans, no text. |
| vending | drinks vending machine 0.9×1.9 m, glowing front (`vending`) | A Korean drinks vending machine with a glowing front panel of cans. (Can share the subway/decor_4 model.) |
| cafe_set | café table + two chairs + parasol (`cafe_set`) | A round café table with two chairs under a parasol. |
| flower_bed | 2.4 m stone planter with blossoms (`flower_bed`) | A long granite planter box with a row of blossoms. |
| notice_board | cork board on two posts (`notice_board`) | The guild quest notice board: cork board on two posts with blank pinned papers. |
| banner | guild pennant on a steel pole (`banner`) | A guild pennant on a steel pole with the gold sun crest on blue. |
| scooter | parked scooter (`scooter`) | A parked delivery scooter with a rear delivery box. |
| bench | KayKit `bench` ×4.6 | A city park bench with wooden slats and steel legs. |
| street_lamp | KayKit `streetlight` | A Seoul street lamp with a curved head. (Can share guild_street/torch.) |
| tree | procedural plaza tree (`tree`) | A ginkgo street tree in a square tree grate. |
| planter | KayKit `bush` planter (`planter`) | A round concrete planter with a trimmed bush. |
| car_sedan / car_taxi / car_police / car_hatchback | KayKit cars (`guild.py:281-284`) | Four parked cars: a white sedan, an orange Seoul taxi with a roof light, a white-blue Korean police car, a small hatchback (4 models). |
| traffic_light | KayKit `trafficlight_B` | A Korean traffic light pole with a pedestrian signal. |
| trash_bins | KayKit `trash_A`, `trash_B` | A pair of street bins (general and recycling). |
| market_crates | KayKit `crate_tomatoes/potatoes/carrots`, `fridge_A`, `menu` | Produce crates, a glass drinks fridge and an A-board, as one grouped storefront prop. |
| cargo | KayKit `cargo_A/B`, `table_low` | A stack of cargo boxes and a low steel workbench, as one grouped prop. |
| anvil_barrel | anvil + barrel in front of the workshop | A steel anvil on a stump with a water barrel. |
| barricade | KayKit Dungeon `barrier` (`build_kit_gate`) | A yellow-black water-filled road barricade segment (reused along the gate cordon). |

## Keep procedural or needs special handling
- Ground, roads, lane dashes, zebra crossings, plaza paving, kerbs (`build_ground`, `build_plaza`, `pave_rect`,
  `dashes_*`, `zebra_*`): **tiling**.
- `string_lights` (festoon strings between poles) and the overhead power cables: thin spans, so keep procedural.
- `Col_*` colliders, `build_boundaries` (1.2 m plaza walls), `Spot_*` / `LightAnchor*` empties: keep procedural.
- `text_mesh` signs ("DAWN GUILD", "MARKET", "WORKSHOP") are Latin-only placeholders. Tripo signs come out blank; if
  Hangul signage is wanted, add it later as decals, not in the generation.
