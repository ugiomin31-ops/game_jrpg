# VRoid sample bodies (CC0)

`HairSample_Male.vrm` and `HairSample_Female.vrm` are pixiv's VRoid Studio sample models, published under
CC0 (VRM meta: licenseName CC0, commercialUssageName Allow; see VRoid Hub help article 4402614652569).
Source: https://github.com/vrm-c/vrm-specification samples / VRoid Studio sample data.

`lib_anime/vroid_base.py` imports one, poses it into the game rest pose, folds its weights onto the game's
20-bone Humanoid rig and recolours its textures per hero.
