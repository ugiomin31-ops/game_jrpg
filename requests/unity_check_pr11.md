# 요청: PR #11 독왕 버섯(elite_mushroom) 모델·모션 7종을 Unity 전투에서 확인

상태: **done**  (끝나면 이 줄을 `done`으로 바꾸고 결과를 아래 "결과"에 적어 주세요)
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
### 2026-10-16 Unity 로컬 검사 (unity session)
- 대상: `4aa7df4f` (`claude/project-thread-bq4qs8`), Unity 6000.3.25f1. 별도 worktree에서 batchmode 임포트 + `ValidateContent`, 이어서 Windows 플레이어를 빌드해 기존 ReviewBoot(`party=h_dohyun,h_seoa,h_jiho,h_yuna&level=3&groups=elite_mushroom`)로 실제 전투를 돌렸습니다. PR 브랜치에는 커밋하지 않았고 Tripo 크레딧도 쓰지 않았습니다(임시 검증 스크립트만 로컬에 두었습니다).

1. **빨간 오류**: 프로젝트 쪽 없음. `error CS` 없음, 임포트 예외 없음. 플레이어 전투 중 예외도 없었습니다. `elite_mushroom`·`TexturedMaterials`·`Missing`이 들어간 경고는 없습니다. `AbyssArtImporter` 경고는 기존 VFX 두 건뿐입니다: `VFX mesh Assets/_Game/Resources/Vfx/Meshes/aid_kit.fbx: 6018 triangles (budget about 1000).`, `VFX mesh Assets/_Game/Resources/Vfx/Meshes/riot_shield.fbx: 3674 triangles (budget about 1000).`
2. **클립** (24fps, Generic, avatar `elite_mushroomAvatar` valid): Idle 15.333초/368프레임 **Loop**, Run 2.333초/56프레임 **Loop**, Attack 2.208초/53프레임, Cast 3.667초/88프레임, Hit 1.292초/31프레임, Die 5.542초/133프레임, Victory 12.083초/290프레임. 7개 모두 있고 Idle·Run만 Loop입니다. (메시 11,662 tris, 본 65개)
3. **재질**: `elite_mushroom_mat/elite_mushroom.mat` 생성됨(shader `Abyss/Toon`), 텍스처 `elite_mushroom_tex/elite_mushroom.png` 연결됨. 전투 화면에서도 갈색 버섯으로 나옵니다(분홍·흰색 아님).
4. **Validate**: `All production 3D content resource paths resolve.`
5. **전투 눈 확인** (스크린샷 `docs/verification/pr11-unity-check/`):
   - Idle·크기(01): 파티 앞쪽 칸에 서서 대기, 헌터보다 약간 큰 정도로 칸에 맞습니다.
   - Attack(02)·Cast: 일반 공격 1회, `sk_toxic_cloud`·`poison_spore` 시전 여러 번, 소환(`mushroom`) 1회가 나왔고 데미지는 동작 시작 약 1.4~3초 뒤 들어갑니다(로그 `harness.txt`).
   - Hit(03): 피격 시 노란 번개 이펙트와 함께 반응합니다.
   - **Die(04)**: 쓰러진 0.2초 시점에 무릎을 꿇은 자세로 바닥 위에 있고 바닥 아래로 꺼지지 않습니다. 0.6초쯤 연기와 함께 사라집니다(Die 클립 5.5초 중 앞부분만 보임).
   - **Victory**: 파티가 이겨서 확인하지 못했습니다.
   - 참고: 소환 시점 카메라 컷이 어두운 보라색 벽면만 비췄습니다(카메라가 구조물 안쪽). 버섯 모델 문제는 아니고 카메라 연출 쪽으로 보입니다.
- 캡처 방법: 이 PC는 원격 데스크톱 화면이라 Game 뷰/화면 캡처가 검정·청록으로 나옵니다. 그래서 게임 카메라를 오프스크린으로 렌더해 저장했고, 화면 UI는 사진에 빠져 있습니다. (PR12 첫 캡처가 청록색이던 원인도 이것으로 보입니다.)
