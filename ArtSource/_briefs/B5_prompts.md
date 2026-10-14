# Batch B5 — image prompts (Sol-approved, 2026-10-12)

65 entries: 22 remaining VFX + 2 additions, 15 subway floor-1 pieces, 26 town entries. Priority P1 = first-screen/high-use, P2 = variety, P3 = later.
One ChatGPT web request per asset (GPT-6, Extra High verified before each); every prompt = lead sentence + brief + view hint + matching frame. Save `candidate_A..D.png` + `prompts.md` under `ArtSource/vfx/<id>/candidates/`, `ArtSource/terrain/subway/<id>/candidates/`, `ArtSource/town/<id>/candidates/` (use `v2_` if files exist; never overwrite).

## Lead sentence
Generate FOUR separate standalone images in this one response, each its own image, not a grid or contact sheet.

## Frames
- **VFX frame:** One opaque matte-grey sculptural reference of the subject, chunky stylised game geometry, clearly readable silhouette, neutral shading, plain mid-grey background, entire object with margins, square image. No glow, transparency, particles, motion blur, text or symbols. Vary proportions and silhouette within the brief.
- **Subway frame:** One chunky stylised present-day Seoul subway game asset, restrained cream tile, stainless steel, line-green and navy accents, slightly worn but readable, plain neutral background, whole asset visible, square image. No people, letters, numbers, logos or medieval motifs; screens and windows opaque.
- **Town frame:** One chunky polished Seoul hunter-guild street asset, modern Korean urban design, broad readable forms, clean restrained material colours, plain neutral background, complete object, square image. No people or readable signage.

## A. VFX (view hint in brackets)
- P1 ground_seal [high three-quarter]: Three concentric raised rings, eight broad spokes, a notched rim; no runes.
- P1 thrust_spike [side-biased three-quarter]: One long cone surrounded by six shorter spikes on a broad connected base.
- P1 nova_wave [high three-quarter]: A thick annular wave with a curling outer crest and an open centre.
- P1 shadow_tendril [side three-quarter]: A thick segmented root narrowing into one hooked claw, not several tentacles.
- P1 holy_cross [near-front three-quarter]: Four pointed geometric arms around a bevelled diamond core; no religious decoration.
- P1 flame_plume [front three-quarter]: Three connected broad flame lobes curling upward, thick rather than ribbon-thin.
- P1 heal_bloom [high three-quarter]: Eight broad open petals surrounding a rounded bud.
- P1 lightning_bolt [near-front three-quarter]: A chunky vertical zigzag with two short side forks, not branching wire.
- P1 rock_debris [three-quarter]: Five angular rocks arranged as one compact, clearly separated cluster.
- P1 ice_shard [side three-quarter]: One elongated hexagonal crystal, sharply pointed at both ends.
- P2 tornado_funnel [low three-quarter]: Four thick spiralling bands forming an open-centred tapered funnel.
- P2 chain_ring [high three-quarter]: Ten chunky interlocking links forming one closed ring with readable holes.
- P2 energy_lance [side three-quarter]: A long diamond-section lance with a thick ring guard one-third from its rear.
- P2 sword_phantom [front three-quarter]: A plain broad straight blade with a simple crossguard, no ornate hilt.
- P2 feather [near-front three-quarter]: A broad solid feather with a slight S-curve and shallow vane grooves; no hairlike strands.
- P2 crystal_prism [three-quarter]: An elongated faceted cut gem with a flat top, distinct from a double-pointed shard.
- P2 rift_gate [front three-quarter]: A vertical oval opening bounded by a thick jagged fractured rim; the centre stays empty.
- P2 barrier_panel [front three-quarter]: Connected 3×3 hexagonal shield panels on a gentle curved frame.
- P2 ice_spike_cluster [low three-quarter]: Seven crystal spikes erupting from one shallow cracked base, the centre tallest.
- P2 vine_coil [three-quarter]: A thick thorned vine forming an open two-turn spiral with broad attached thorns.
- P2 acid_splash [high three-quarter]: A shallow five-lobed liquid splash with a thick raised central mound and a solid curled perimeter.
- P3 bite_jaws [front three-quarter]: Upper and lower curved fang rows with rounded chunky teeth, no skull.
- P3 meteor_rock [three-quarter]: A rounded irregular boulder with deep branching grooves, no painted glow.
- P3 crow_silhouette [high front three-quarter]: One compact bird-shaped sculpture with broad swept wings, a small beak and a wedge tail; no individual feathers.

VFX install: Tripo → Triangle Smart Mesh → cleanup per ArtSource/_briefs/skills_vfx.md mesh contract (Unity-space sizes/axes from Sol's B5 note: ground_seal Ø2 m XZ bottom-centre; thrust_spike 1.6 m base pivot tip +Z; nova_wave Ø2 m XZ sweep UV; shadow_tendril 1.8 m root pivot +Y curling +Z; holy_cross 1.6 m centre faces +Z; flame_plume 1.2 m bottom +Y; heal_bloom Ø1.6 m bottom +Y; tornado_funnel 2.4 m bottom-tip +Y sweep UV; chain_ring Ø1.6 m XZ; lightning_bolt 3 m bottom-tip +Y; rock_debris 0.6 m one particle mesh; ice_shard 0.8 m long axis +Z; energy_lance 2.4 m tip +Z; sword_phantom 1.4 m guard pivot blade +Y; feather 0.6 m quill pivot +Y; crystal_prism 0.7 m +Y; rift_gate 2.6 m bottom pivot faces +Z; barrier_panel 2.4 m wide concave face +Z; ice_spike_cluster 1.8 m bottom +Y; vine_coil 1.6 m bottom +Y; acid_splash 1 m XZ ≤200 tris; bite_jaws 1.2 m hinge pivot faces +Z; meteor_rock Ø1 m; crow_silhouette 0.7 m forward +Z ≤200 tris). Total catalog ≤ 18,000 tris. Mask body 0.6 / grooves 0.35 / highlights 0.8; white vertex RGB with edge/tip alpha fade.

## B. Subway floor 1 (subway frame; tiling pieces use the stated orthographic views)
- P1 decor_2 [front three-quarter]: A stainless three-seat platform bench with a green back stripe and broad supports.
- P2 decor_3 [front three-quarter]: A round station bin with a split lid, a green band and one tied rubbish bag beside it.
- P1 decor_4 [front three-quarter]: A red Korean drinks vending machine with recessed can rows, a coin panel and a delivery slot (about 0.9 m wide, 2 m high).
- P1 decor_5 [side three-quarter]: A short broken escalator with a missing top step, a bent black handrail and yellow step edges.
- P2 decor_6 [front three-quarter]: A white cylindrical station column with green/navy bands and a round blank cap sign.
- P1 chest [front three-quarter]: An olive emergency supply case with metal straps, latches and a blank red identification plate (lid must stay a separate hinged part).
- P2 lore_stone [front three-quarter]: A white information kiosk with a blue abstract transit-map screen and a yellow header; no legible text.
- P1 spring [front three-quarter]: A white AED/first-aid cabinet with a green status panel and a compact blue beacon; no red-cross emblem.
- P1 torch [front/side three-quarter]: A wide white fluorescent wall housing with steel end brackets.
- P1 warp [high three-quarter]: A low circular steel floor hatch with a violet annular inset and broad radial divisions; no floating portal.
- P1 foe_marker [high three-quarter]: An orange fractured floor ring with a low attached crystal accent on its rim; the centre clear.
- P1 wall_base [orthographic front elevation]: Cream subway tiles, a green horizontal band and restrained panel joints, flat side edges.
- P1 floor_base [orthographic overhead]: Pale granite platform paving with recessed grout and subtle wear, flat border.
- P1 stairs_up [side-biased orthographic three-quarter]: Broad cream-tiled station stairs with yellow step noses and a green landing stripe; no ornate rails.
- P1 door_locked [straight front]: A cream station frame around a closed steel-framed screen door with a compact access lock.

Subway install: props 3–6k tris / 1k, existing footprint and root pivot, front = Blender −Y, keep required children/empties (chest `Lid`, torch `LightAnchor`, warp `LightAnchor_warp`, foe_marker `Spot_foe`). Tiling per environment_tiling.md (wall 4×4.5 m, ≤0.20 m relief, flat 0.12 m side seams, 0.25 m skirting, 0.30 m cap, Face_N/S/E/W + Core; floor 4×4 m, recess ≤0.08 m, 0.15 m flat border, underside −0.3 m, keep Ceiling; stairs fit 4×4 m rising north to 2.5 m; door 4×4.5 m frame, 2 m opening, `Door` hinge x−1, child `Lock`, +95° opening). Wall texture wraps horizontally, floor on both axes. Pilot wall + floor first and inspect joins/corners before stairs/door.

## C. Town (town frame)
- P1 food_cart [front three-quarter]: A tteokbokki/odeng street cart with a striped awning on four sturdy posts and broad pans.
- P1 tree [three-quarter]: A ginkgo street tree with a layered broad canopy and a square tree grate; thick branches.
- P1 market_crates [front three-quarter]: Produce crates, an opaque glass-front drinks fridge and a blank A-board.
- P1 cargo [front three-quarter]: Stacked shipping boxes beside a low steel workbench; no labels.
- P1 anvil_barrel [front three-quarter]: A steel anvil on a stout stump beside a water barrel; modern repair-yard look.
- P1 barricade [front three-quarter]: A yellow-and-black water-filled road barrier with broad feet and moulded handle openings.
- P2 skyline_building_A [front three-quarter]: A five-storey cream shop-and-office block with blank sign bands and compact rooftop equipment.
- P2 skyline_building_B [front three-quarter]: A warm brick Seoul villa with broad balconies and recessed windows.
- P2 skyline_building_E [front three-quarter]: A small two-storey café block with a warm frontage and a plain awning.
- P2 skyline_building_F [front three-quarter]: A convenience-store ground floor with three office floors above and a blank fascia.
- P2 cafe_set [high three-quarter]: A round table, two chairs and a broad parasol as one arrangement.
- P2 flower_bed [high three-quarter]: A long granite planter with compact flower clusters and broad leaves; no thin stems.
- P2 scooter [side three-quarter]: A modern delivery scooter with a rear cargo box and sturdy mirrors.
- P2 bench [front three-quarter]: A wood-slat city bench with dark steel legs and armrests.
- P2 planter [high three-quarter]: A round concrete tub with a neatly trimmed rounded shrub.
- P2 car_sedan [front-side three-quarter]: A white contemporary sedan with broad dark windows.
- P2 car_taxi [front-side three-quarter]: An orange Seoul taxi with a solid roof light and blank doors; no lettering.
- P2 car_police [front-side three-quarter]: A white-and-navy Korean-style patrol car with a chunky red/blue lightbar; no crest or text.
- P2 traffic_light [front three-quarter]: An urban signal pole with vehicle lamps and a blank pedestrian panel; no digits or thin wires.
- P2 trash_bins [front three-quarter]: A general/recycling bin pair with contrasting lid colours; no labels.
- P3 skyline_building_C [low front three-quarter]: A slender blue-grey glass office tower with clear floor divisions.
- P3 skyline_building_D [low front three-quarter]: A pale apartment tower with strong striped balcony stacks.
- P3 skyline_building_G [low front three-quarter]: A tall glass-and-concrete tower with staggered solid façade bands.
- P3 skyline_building_H [front three-quarter]: An apartment high-rise with a compact rooftop water tank and service enclosure.
- P3 car_hatchback [rear-side three-quarter]: A compact mint-grey hatchback, visibly shorter than the sedan.
- (vending: reuse subway decor_4, no generation)

Town install: buildings 10–20k / 2k, props 3–6k / 1k, no rigs; keep guild.py locations, orientations, colliders and markers via tripo_pieces.json; do not stretch skyline meshes vertically.
