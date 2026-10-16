# 요청: PR #12 수정 동굴 보스 전투 재확인 (아이콘 추가 후)

상태: **open**  (끝나면 이 줄을 `done`으로 바꾸고 결과를 아래 "결과"에 적어 주세요)
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
(여기에 적어 주세요)
