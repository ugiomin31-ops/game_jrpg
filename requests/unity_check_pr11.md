# 요청: PR #11 독왕 버섯(elite_mushroom) 모델·모션 7종을 Unity 전투에서 확인

상태: **open**  (끝나면 이 줄을 `done`으로 바꾸고 결과를 아래 "결과"에 적어 주세요)
요청한 곳: 클라우드 스레드 "독왕 버섯 설치", PR #11 (https://github.com/ugiomin31-ops/game_jrpg/pull/11)

Tripo 독왕 버섯 모델과 모션 7종(Idle·Run·Attack·Cast·Hit·Die·Victory)을 한 FBX로 합쳐 게임에 넣었습니다. 클라우드에서는 Unity를 못 돌려서 실제 에디터·전투에서 확인을 부탁드립니다. 파일을 고치거나 PR 브랜치에 커밋하지는 말고 확인만 해 주세요.

## 1. 브랜치 받기
- 브랜치 **`claude/project-thread-bq4qs8`** (PR #11 head, 최신 커밋)를 `git worktree add --detach`로 별도 폴더(예: `_wt\pr11`)에 받습니다.
- Unity 6000.3.25f1로 엽니다(batchmode로 임포트·검증 후 GUI로 전투 확인).

## 2. 확인할 것
1. 임포트 후 Console의 빨간 오류 전부, 그리고 `elite_mushroom`·`AbyssArtImporter`·`TexturedMaterials`·`Missing`이 들어간 경고.
2. `Assets/_Game/Resources/Art/Enemies/elite_mushroom/elite_mushroom.fbx`의 애니메이션 클립 이름·길이(프레임 또는 초)·Loop 여부. 기대값: Idle(루프), Run(루프), Attack, Cast, Hit, Die, Victory 7개.
3. 재질 `elite_mushroom`(또는 `elite_mushroom_mat`)이 만들어졌고 `elite_mushroom_tex/elite_mushroom.png` 텍스처가 붙었는지(분홍/흰색이 아닌 갈색 버섯).
4. `Abyss > Validate Production Content` 결과 메시지 그대로.
5. 플레이 모드에서 **독왕 버섯**이 나오는 전투를 한 번 하고(디버그 전투 진입이 있으면 그걸로) 다음을 눈으로 봐 주세요:
   - Idle이 자연스럽게 반복되는지, 크기(scale_mult 1.35)가 적당한지
   - Attack 타격 순간과 데미지 숫자가 맞는지, Cast 시전 순간
   - Hit 반응, **Die 때 몸이 바닥 아래로 꺼지지 않는지**(클라우드에서 보정을 넣었습니다), 쓰러진 뒤 사라지는 타이밍
   - 플레이어가 지면 Victory
6. 가능하면 스크린샷 2~4장(Idle, Attack, Die 마지막 자세)을 `docs/verification/pr11-unity-check/`에 저장.

## 3. 하지 말 것
- PR #11 브랜치에 커밋·푸시하지 마세요. Tripo 크레딧을 쓰지 마세요.

## 4. 결과 올리기
- 이 파일 "결과"에 적고 상태를 `done`으로 바꿔 **`local-requests`** 브랜치에 커밋·푸시(스크린샷 포함).

## 결과
(비어 있음)
