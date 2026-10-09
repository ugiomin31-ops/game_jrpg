# KayKit Furniture Bits 1.0 (CC0)

By Kay Lousberg — https://kaylousberg.com
License: Creative Commons Zero (CC0 1.0), see `LICENSE.txt`. Credit is appreciated, not required.

Only the glTF parts used by the town hub are copied here (each `.gltf` with its `.bin` buffer and the
1024 px gradient atlas `furniturebits_texture.png`). `Blender/environment/cc0_kit.py` (pack `kf`) samples the atlas per face corner,
bakes the colour into the `Col` attribute and the output FBX carries no texture.
Used by `Blender/town/guild.py` (Dawn Guild street): outdoor table.
