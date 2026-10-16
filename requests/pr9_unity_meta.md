# 요청: PR #9 숲 유적 Unity 생성 파일(.meta·재질) 올리기

상태: **done**  (끝나면 이 줄을 `done`으로 바꾸고 결과를 아래 "결과"에 적어 주세요)
요청한 곳: 클라우드 스레드 "Tripo 자산 모델링", PR #9 (https://github.com/ugiomin31-ops/game_jrpg/pull/9)
이전 검사: `requests/unity_check_pr9.md` (임포트·빌드·4층 화면 통과)

지하철 Tripo 조각처럼 Unity가 만든 `.meta`와 `_mat` 재질을 커밋해 GUID를 고정하려고 합니다. `requests/pr12_unity_meta.md`와 같은 방식입니다. 검사 때 임포트한 PR9 worktree에서 **생성된 파일을 그대로** 올려 주세요. **PR 브랜치(`claude/project-thread-m23hrb`)에는 직접 커밋하지 말고** 아래 위치에 올려 주세요. 클라우드 스레드가 PR로 옮깁니다.

## 할 일
1. PR9 worktree를 `d9c1d746` 이상으로 받고 Unity로 한 번 임포트합니다(검사 때 만든 파일이 이미 있으면 그대로 써도 됩니다).
2. 아래 파일 15조각 × 6개 = 90개를 **저장소 경로를 유지한 채** `local-requests` 브랜치의 `drops/pr9_meta/` 아래로 복사해 커밋·푸시해 주세요. 예: `drops/pr9_meta/Assets/_Game/Resources/Art/Environment/verdant_ruins/chest.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_1.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_1_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_1_tex/M_VerdantDecor1_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_1_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_1_mat/M_VerdantDecor1_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_1_mat/M_VerdantDecor1_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_2.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_2_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_2_tex/M_VerdantDecor2_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_2_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_2_mat/M_VerdantDecor2_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_2_mat/M_VerdantDecor2_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_3.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_3_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_3_tex/M_VerdantDecor3_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_3_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_3_mat/M_VerdantDecor3_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_3_mat/M_VerdantDecor3_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_4.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_4_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_4_tex/M_VerdantDecor4_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_4_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_4_mat/M_VerdantDecor4_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_4_mat/M_VerdantDecor4_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_5.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_5_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_5_tex/M_VerdantDecor5_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_5_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_5_mat/M_VerdantDecor5_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_5_mat/M_VerdantDecor5_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_6.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_6_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_6_tex/M_VerdantDecor6_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_6_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_6_mat/M_VerdantDecor6_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/decor_6_mat/M_VerdantDecor6_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/chest.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/chest_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/chest_tex/M_VerdantChest_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/chest_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/chest_mat/M_VerdantChest_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/chest_mat/M_VerdantChest_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/lore_stone.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/lore_stone_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/lore_stone_tex/M_VerdantLoreStone_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/lore_stone_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/lore_stone_mat/M_VerdantLoreStone_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/lore_stone_mat/M_VerdantLoreStone_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/spring.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/spring_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/spring_tex/M_VerdantSpring_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/spring_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/spring_mat/M_VerdantSpring_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/spring_mat/M_VerdantSpring_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/torch.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/torch_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/torch_tex/M_VerdantTorch_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/torch_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/torch_mat/M_VerdantTorch_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/torch_mat/M_VerdantTorch_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/trap.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/trap_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/trap_tex/M_VerdantTrap_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/trap_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/trap_mat/M_VerdantTrap_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/trap_mat/M_VerdantTrap_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/warp.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/warp_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/warp_tex/M_VerdantWarp_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/warp_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/warp_mat/M_VerdantWarp_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/warp_mat/M_VerdantWarp_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/foe_marker.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/foe_marker_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/foe_marker_tex/M_VerdantFoeMarker_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/foe_marker_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/foe_marker_mat/M_VerdantFoeMarker_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/foe_marker_mat/M_VerdantFoeMarker_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_1.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_1_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_1_tex/M_VerdantOverlay1_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_1_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_1_mat/M_VerdantOverlay1_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_1_mat/M_VerdantOverlay1_Tripo.mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_2.tripo.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_2_tex.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_2_tex/M_VerdantOverlay2_Tripo.png.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_2_mat.meta`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_2_mat/M_VerdantOverlay2_Tripo.mat`
   - `Assets/_Game/Resources/Art/Environment/verdant_ruins/overlay_2_mat/M_VerdantOverlay2_Tripo.mat.meta`
3. `verdant_ruins` 폴더에서 Unity가 바꾼 `<조각>.fbx.meta`(15개)가 있으면 같이 올리고 목록을 적어 주세요. GUID는 바뀌면 안 됩니다. 그 밖에 새로 생긴 파일도 같이 올려 주세요.
4. `.gitignore` 때문에 빠질 수 있으니 `git add -f`로 올리고, 푸시한 뒤 `git ls-tree -r --name-only origin/local-requests drops/pr9_meta | wc -l`로 90개 이상인지 확인해 주세요.
5. 검사 결과에 "13개"로 적힌 부분: 15조각(decor_1~6, chest, lore_stone, spring, torch, trap, warp, foe_marker, overlay_1, overlay_2)이 모두 `_mat`을 받았는지 한 줄로 확인해 주세요. foe_marker는 게임이 쓰지 않는 모델이라 화면에 안 나오는 게 정상입니다.

## 결과
- PR9 worktree는 `d9c1d746`(현재 PR head와 같음). 검사 때 Unity 6000.3.25f1이 만든 파일을 그대로 썼습니다(재임포트 안 함). PR 브랜치에는 커밋하지 않았습니다.
- `drops/pr9_meta/` 아래에 저장소 경로를 유지해 **105개**를 올렸습니다: 요청 목록 90개(15조각 × `.tripo.meta`·`_tex.meta`·`_tex/*.png.meta`·`_mat.meta`·`_mat/*.mat`·`.mat.meta`) + Unity가 바꾼 `<조각>.fbx.meta` 15개(chest, decor_1~6, foe_marker, lore_stone, overlay_1, overlay_2, spring, torch, trap, warp).
- `.fbx.meta` 15개 모두 GUID가 PR 커밋과 같습니다(바뀐 것 없음). 그 밖에 `verdant_ruins` 폴더에 새로 생긴 파일은 없습니다.
- 15조각 모두 `_mat` 재질을 받았습니다(decor_1~6, chest, lore_stone, spring, torch, trap, warp, foe_marker, overlay_1, overlay_2). 이전 검사의 "13개"는 화면에 나오는 조각만 센 숫자였습니다.
- 복사본은 원본과 SHA-256이 모두 같습니다.