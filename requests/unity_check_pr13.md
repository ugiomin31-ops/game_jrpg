# 요청: PR #13 모션 수정을 Unity에서 확인

상태: **open**  (끝나면 이 줄을 `done`으로 바꾸고 결과를 아래 "결과"에 적어 주세요)
요청한 곳: 클라우드 스레드 "어색한 캐릭터 모션 점검", PR #13 (https://github.com/ugiomin31-ops/game_jrpg/pull/13)

클라우드에서는 Unity를 실행할 수 없어서, 캐릭터 모션 수정(쓰러짐·부활·마을 이동·방어·상태이상·접근 타이밍)과 새 공용 `Die.fbx`(Tripo `fall`)가 실제 에디터에서 문제없는지 확인을 부탁드립니다. 파일을 고치거나 PR 브랜치에 커밋하지는 말고 확인만 해 주세요.

## 1. 브랜치 받기
- 브랜치 **`claude/project-thread-2h6jsm`** (PR #13 head, 커밋 `ad61b72` 이상)를 `git worktree add --detach`로 별도 폴더에 받습니다.
- Unity 6000.3.25f1로 엽니다. 다른 워크트리의 Library를 복사해 와도 됩니다.

## 2. batchmode로 먼저 (PR #10 확인 때와 같은 방법)
1. 전체 임포트 후 **컴파일 오류(`error CS`)와 빨간 오류**를 모두 적어 주세요. 특히 `BattleView.Posture.cs`, `BattleView.cs`, `TownWorld.cs`, `ArtLibrary.cs`.
2. `Assets/_Game/Resources/Art/HumanoidAnimations/Die.fbx` 임포트 관련 로그를 적어 주세요. `Avatar`, `humanoid`, `T-Pose`, `Die` 가 들어간 경고/오류 전부. (메타를 GUID만 남겨 새로 만들게 했습니다.)
3. `Abyss > Validate Production Content` (`-executeMethod Abyss.EditorTools.AbyssProjectSetup.ValidateContent`) 결과 메시지.

## 3. 플레이 모드 눈 확인 (GUI 에디터)
자세한 순서는 PR 브랜치의 `docs/MOTION_POLISH_20261015.md` "Unity 확인 순서"입니다. 각 항목에 **정상 / 이상(무엇이 어떻게)** 만 적어 주시면 됩니다.
1. 도현·지호·민준·서아·유나 중 한 명이 쓰러질 때: 뒤로 넘어져 눕는지, **쓰러지기 시작할 때 몸 방향이 휙 돌지 않는지**, 바닥을 뚫거나 뜨지 않는지, 옆 헌터와 겹치지 않는지.
2. 그 헌터를 부활시킬 때: 자연스럽게 일어나 전투 자세로 돌아오는지(0.5초).
3. Blender 리그 헌터(예: 보라)가 쓰러지고 부활할 때 기존처럼 보이는지.
4. 쓰러진 헌터가 있는 채로 전투에 들어가면 처음부터 누워 있는지.
5. 마을 이동(키보드 = 조깅, Shift = 질주)과 동료 3명: 발이 미끄러지지 않는지.
6. 방어 → 맞기 → 다음 턴까지 방어 자세 유지되는지.
7. 빙결(멈춤), 수면·브레이크(느린 대기) 적.
8. 근접 공격 도착과 타격 타이밍, 도주(돌아서서 달림), 보스 페이즈 전환(2배속).
- 가능하면 1·2번 장면 스크린샷이나 짧은 GIF를 `docs/verification/pr13-unity-check/`에 넣어 주세요.

## 4. 하지 말 것
- PR #13 브랜치에 커밋·푸시하지 마세요. 결과는 이 파일에만 적습니다.

## 5. 결과 올리기
- 이 파일의 "결과"에 적고 상태를 `done`으로 바꾼 뒤 **`local-requests`** 브랜치에 커밋·푸시해 주세요(스크린샷도 같은 커밋). 이상이 있으면 제가 PR #13에서 고치겠습니다.

## 결과
(채워 주세요)
