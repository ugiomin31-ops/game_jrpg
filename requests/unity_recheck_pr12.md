# 요청: PR #12 수정 동굴 보스 전투 재확인 (아이콘 추가 후)

상태: **done**  (끝나면 이 줄을 `done`으로 바꾸고 결과를 아래 "결과"에 적어 주세요)
요청한 곳: 클라우드 스레드 "수정 동굴 4족 몬스터 웨이트 실패 원인 조사", PR #12
이전 검사: `requests/unity_check_pr12.md` (임포트 통과, 전투에서 `Missing production UI sprite: Icons/Enemies/crystal_cave_lord`)

커밋 `eff1f1f`에서 보스 초상화 `Assets/_Game/Resources/Icons/Enemies/crystal_cave_lord.png`(+ .meta, manifest)를 추가했고, `Validate Production Content`가 이제 모든 적 초상화도 확인합니다. **확인만** 해 주세요(PR 브랜치에 커밋 금지, Unity가 만든 .meta/.mat 커밋 금지).

## 할 일
1. 이전 검사용 worktree에서 `claude/project-thread-69lmhy`를 `eff1f1f` 이상으로 받아 임포트합니다.
2. `Abyss.EditorTools.AbyssProjectSetup.ValidateContent` 결과 원문을 적어 주세요. 다른 적 초상화가 빠졌다고 나오면 그 목록을 그대로 적어 주세요.
3. 이전과 같은 ReviewBoot(group `crystal_cave_lord`)로 보스 전투에 들어가서
   - 턴 순서 UI 오류 없이 전투가 진행되는지, Console 빨간 오류 원문
   - 보스가 Idle·Attack(공격 1회)·Hit(피격)·Die(처치)를 재생할 때 다리·꼬리가 찢어지거나 바닥을 뚫는지
   - 크기가 전투 칸에 맞는지
4. 이전 캡처가 화면 전체 청록색이었습니다. 가능하면 원인(카메라·후처리·배치모드 렌더 등)을 확인하고, 보스가 보이는 스크린샷 1~3장을 `docs/verification/pr12-unity-recheck/`에 넣어 주세요. 청록색이 계속되면 GUI 에디터 Game 뷰 캡처로 대신해 주세요.

## 결과 올리기
이 파일 "결과"에 적고 상태를 `done`으로 바꾼 뒤 `local-requests`에 커밋·푸시해 주세요.

## 결과
### 2026-10-16 Unity 로컬 재검사 (unity session)
- 대상: `eff1f1ff`. 이전 PR12 worktree에서 임포트 + `ValidateContent`, 이어서 Windows 플레이어 빌드 후 ReviewBoot(group `crystal_cave_lord`)로 전투 2회. PR 브랜치에는 커밋하지 않았습니다.
1. **Validate 원문**: `All production 3D content resource paths resolve.` 빠진 적 초상화 목록은 나오지 않았습니다(예외 없음). `error CS` 없음. 빌드 성공(`Windows build: 1258430024 bytes`).
2. **전투**: 이번에는 `Missing production UI sprite` 오류가 없고, 플레이어 로그·검증 로그 모두 게임 쪽 빨간 오류가 없습니다. 턴이 끝까지 진행됐습니다.
   - 1회차(level 45, 1배속, 200초): 보스가 `sk_e_crystal_spike`·`sk_e_crystal_shell`·일반 Attack을 여러 번 사용, 헌터 1명 쓰러짐, 시간 내 보스 처치는 못 함.
   - 2회차(level 99, 2배속): 108.7초에 보스 처치(`UnitDown crystal_cave_lord`), `BattleEnd Victory`.
3. **모습** (`docs/verification/pr12-unity-recheck/`):
   - Idle(01)·Attack(02)·Hit(03): 수정 가시·안전모·다리 모두 몸에 붙어 있고 찢어짐이나 바닥 관통은 보이지 않습니다. 피격 때 빨간 이펙트가 덮입니다.
   - 크기: 헌터보다 약간 큰 정도로 전투 칸 안에 들어갑니다.
   - Die(04, 2배속): 쓰러지고 0.2초 시점에 바닥 위 정상 자세, 0.6초쯤 사라집니다. 사라지는 효과가 빨라 Die 동작 자체(다리·꼬리)는 거의 보이지 않습니다. 이 짧은 구간에서는 찢어짐·관통이 없었습니다.
4. **청록색 원인**: 이 PC가 원격 데스크톱 세션이라 에디터 Game 뷰/화면 캡처가 실제로 그려지지 않았습니다(빌드 플레이어 화면 캡처는 검정). 게임 카메라를 오프스크린 RenderTexture로 직접 렌더해 저장하는 방식으로 해결했습니다. 화면 UI(체력바 등)는 사진에 빠집니다. 게임 렌더링 자체 문제는 아닌 것으로 봅니다.
