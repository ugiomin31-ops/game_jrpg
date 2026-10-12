
## B3 candidates (ChatGPT web, GPT-6 Extra High, 2026-10-12, Haiku worker BROWSER-QUEUE 2b)
- Chat URL: https://chatgpt.com/c/6acbb9f9-de88-83ee-87b9-491a45eccb79 (model GPT-6, reasoning slider 3/4 = Extra High, checked before sending)
- Prompt (lead + brief + creature frame, from ArtSource/_briefs/B3_prompts.md): "Generate FOUR separate standalone images in this one response, each its own image, not a grid or collage. One chunky giant wasp, warm-yellow body with charcoal abdominal stripes, small socketed eyes and one short thick opaque stinger. Four compact, individually separated legs and two broad solid opaque wings spread symmetrically; short thick antennae; no transparent wings or needle-thin appendages. A subtle violet rift crack along the abdomen. No helmet or humanoid costume. One complete creature per image, chunky cute modern Seoul hunter-game toon 3D style, small socketed non-emissive eyes, glow only inside small blue/violet rift cracks, plain light-grey background, generous margins, square 1:1. No text, logos, crowns, capes, medieval ornament, transparent geometry, floating effects or thin dangling parts. Vary proportions and colour accents slightly between the four images while keeping the description."
- candidate_A.png: pass with note. Single wasp, stinger, four legs, violet crack on abdomen, plain background. Wings look semi-translucent pale yellow with vein lines (brief asks for solid opaque).
- candidate_B.png: pass with note. Fiercer head with feather-like fringe plates (less chunky-cute), amber wings that read more solid, violet crack, four legs. Head fringe is close to plumage, not the brief's clean head.
- candidate_C.png: pass with note. Lavender accent patches on wings (colour accent, allowed), four legs, violet crack. Wings look semi-translucent pale yellow (brief asks for solid opaque).
- candidate_D.png: pass. Single wasp, solid-looking wings, four separated legs, short thick stinger, violet crack along the abdomen, no helmet, plain background.
- Suggested pick: candidate_D.png (solid wings, clean legs, clean head). Runner-up: candidate_A.png. Main session makes the final pick.

## Tripo second account (2026-10-12, Haiku worker B3-TRIPO)
- Main final pick: candidate_D.png (main-approved pick)
- Source: https://studio.tripo3d.ai (Tripo Studio web, HD Model, Geometry & Texture, AI Model H3.1 - Best Quality, expected 55 credits)
- Task: 15884c64-3a46-4a40-82b2-5333bf096f71  URL https://studio.tripo3d.ai/workspace/generate/15884c64-3a46-4a40-82b2-5333bf096f71
- Generate cost: 55 credits; 3095 -> 3040

## Tripo second account (2026-10-12, Haiku worker B3-TRIPO)
- Main final pick: candidate_D.png (main-approved pick)
- Source: https://studio.tripo3d.ai (Tripo Studio web, HD Model, Geometry & Texture, H3.1 - Best Quality)
- Task: 15884c64-3a46-4a40-82b2-5333bf096f71  URL https://studio.tripo3d.ai/workspace/generate/15884c64-3a46-4a40-82b2-5333bf096f71
- Generate: 55 credits (3095 -> 3040)
- Retopo: Triangle, Smart Mesh on, target 5000 -> 5054 faces / 7214 vertices (cost 35; balance 2545 -> 2510)
- Rig: Other, Auto Rig, ONE attempt (cost 20; balance 2510 -> 2490). Skeleton visible in viewport. Skin-weight check in Blender: OPEN (not run by this worker).
- Animations: none (nothing bought; see ArtSource/enemies/_other_rig_animation_options.md).
- Export: FBX (Blender preset), texture 2k, Export Skeleton on, no animations. Downloaded bee+3d+model.zip (9.15 MB), extracted to tripo/.
- Export path: ArtSource/enemies/killer_bee/tripo/ (tripo_convert_*.fbx + .fbm)
- Credits spent on this asset: 110 (55+35+20).

## Rig gate (Other rig) 2026-10-12, Sonnet 5.5 worker S14 B3-ENEMIES, headless Blender 5.2.1. NOTHING INSTALLED.
- Method: import the Tripo FBX; count unweighted vertices; rotate each bone 40 deg on local X/Y/Z and count vertices moved >1 cm; render rest + posed frames (front ortho, Workbench, texture) by rotating bones about world Y at the bone head.
- What the FBX actually is: a real, valid skeleton of the same generic Tripo "Other" kind as the bat (40 bones `bone_0..39`, 1 skin, no animation takes, no Mixamo names), so it is not empty. The Tripo Animate page showing only a "Walk" preset and no skeleton overlay is therefore a Tripo-side limitation for this rig/task (not resolvable here, no browser); the exported rig itself loads and deforms. Hierarchy: spine bone_0>1>2>3 (head); antennae bone_4>5 and bone_6>7 under bone_3; front limbs bone_8>9>10>11 and bone_12>13>14>15 under bone_2; WINGS bone_16>17>18>19 (+X) and bone_20>21>22>23 (-X) under bone_1; abdomen bone_24 under bone_0; legs bone_25>..>29 (+X) and bone_30>..>34 (-X) under bone_24; stray bones bone_35/36 and bone_37/38/39 (three coincident bones at the stinger).
- Mesh 2529 verts, 5054 tris. UNWEIGHTED vertices: 687 of 2529 (27%): thorax/head/legs. 25 of 40 bones have no vertex group, among them all leg chains (bone_25-34), the front-limb chains (bone_8-11, 13-15) and antenna bones 4/5. Posing legs, front limbs or those antennae moves 0 vertices (not rigged).
- Posing: wings are good. bone_16..19 move 326/206/139/69 vertices and bone_20..23 281/202/151/66, all in the wing region; raising or lowering both wings (+-45 deg at bone_16/20, 35 deg at distal bone_17/21) deforms only the wings, cleanly (panels A and C of killer_bee_rig_gate_rest_A_B_C.png). Pitching the abdomen/body bone_24 (762 own verts) tears the head and thorax (panel B) because those are unweighted.
- Verdict: PARTIALLY USABLE: wing flap only (plus moving the whole GameObject for run/hit/die). Not usable for body or leg animation as exported; legs, front limbs and thorax need re-skinning. Render: scratchpad s14 (C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Desktop-game/3b4b867d-2aa4-4d7d-bb1b-a832694ad641/scratchpad/s14/) killer_bee_rig_gate_rest_A_B_C.png.

## Installed 2026-10-12 (Sonnet 5.5 F1-INSTALL, 0 credits, code-animated flyer route, user-approved exception)
Installed as a code-animated flyer (RiglessFlyerAnimator, same route as the bat pilot): Assets/_Game/Resources/Art/Enemies/killer_bee/ : TRIPO + FLYER markers first, killer_bee.fbx (GUID kept), killer_bee_tex/killer_bee.png (Tripo basecolor JPEG -> PNG 2048, material name `killer_bee`; Unity generates killer_bee_mat). Source ArtSource/enemies/killer_bee/tripo/*.fbx; the failed Tripo skin (40 bones) and rig discarded. Headless Blender 5.2.1, scratchpad f1/build_fly.py (staged copy + .blend in ArtSource/enemies/killer_bee/unity_staging/): existing faces only separated into Body 4246 / Wing_L 404 / Wing_R 404 = 5054 tris (nothing lost, no new geometry, UVs/normals/material kept, seam normal mismatch 0.0002). Wing faces = centroid |x| > 0.20 and z > 0.30, largest connected component per side; 27 small shoulder/arm faces per side stay on Body. Hinge pivot = centroid of the 34 seam vertices (+-0.1974, 0.0515, 0.4873), axis = PCA seam line (length 0.221 m, max seam-vertex distance to the line 3.6 cm). Native Tripo size (0.98 m span, 0.75 m tall) baked 0.30 m above the floor (hover, like the bat). Old model + meta: ArtSource/enemies/killer_bee/backup_20261012/. Pose check (idle +-16 deg roll, cast 34, attack sweep 40): wings stay attached; caveat as the bat pilot: a thin static membrane fan stays on the Body at each wing root and opens a small wedge at roll >= 30 deg. Unity import not run in this step (unverified).
