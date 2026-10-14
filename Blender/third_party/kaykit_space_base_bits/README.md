# KayKit Space Base Bits 1.0 (CC0)

By Kay Lousberg — https://kaylousberg.com
License: Creative Commons Zero (CC0 1.0), see `LICENSE.txt`. Credit is appreciated, not required.

Only the glTF parts used by the town hub and the hunter-theme dungeon kits are copied here (each `.gltf` with its `.bin` buffer and the
1024 px gradient atlas `spacebits_texture.png`). `Blender/environment/cc0_kit.py` (pack `ks`) samples the atlas per face corner,
bakes the colour into the `Col` attribute and the output FBX carries no texture.
Used by `Blender/town/guild.py` (Dawn Guild street): workshop cargo crates.
Used by `Blender/environment/hunter_kits/`: cargo_A, containers_A (factory cargo), rocks_A, rock_A, rock_B (cave boulders).
