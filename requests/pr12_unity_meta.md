# 요청: PR #12 crystal_cave_lord Unity 생성 파일(.meta·재질) 올리기

상태: **done**  (끝나면 이 줄을 `done`으로 바꾸고 결과를 아래 "결과"에 적어 주세요)
요청한 곳: 클라우드 스레드 "수정 동굴 4족 몬스터 웨이트 실패 원인 조사", PR #12
이전 검사: `requests/unity_recheck_pr12.md` (전투 통과)

코드 리뷰에서 다른 Tripo 보스(`scrap_colossus`, `subway_bat_lord`)처럼 Unity가 만든 `.meta`와 재질을 커밋해야 한다는 지적이 나왔습니다. 클라우드에서는 Unity를 못 돌리니, 재검사 때 이미 임포트한 PR12 worktree에서 **생성된 파일을 그대로** 올려 주세요. 이번에는 올리는 것이 일입니다. 단, **PR 브랜치(`claude/project-thread-69lmhy`)에는 직접 커밋하지 말고** 아래 위치에 올려 주세요. 클라우드 스레드가 PR로 옮깁니다.

## 할 일
1. PR12 worktree를 `5980700` 이상으로 받고 Unity로 한 번 임포트합니다(파일이 이미 있으면 그대로 써도 됩니다).
2. 아래 파일을 **저장소 경로를 유지한 채** `local-requests` 브랜치의 `drops/pr12_meta/` 아래로 복사해 커밋·푸시해 주세요. 예: `drops/pr12_meta/Assets/_Game/Resources/Art/Enemies/crystal_cave_lord.meta`
   - `Assets/_Game/Resources/Art/Enemies/crystal_cave_lord.meta` (폴더 meta)
   - `Assets/_Game/Resources/Art/Enemies/crystal_cave_lord/TRIPO.meta`
   - `Assets/_Game/Resources/Art/Enemies/crystal_cave_lord/crystal_cave_lord.fbx.meta`
   - `Assets/_Game/Resources/Art/Enemies/crystal_cave_lord/crystal_cave_lord_tex.meta`
   - `Assets/_Game/Resources/Art/Enemies/crystal_cave_lord/crystal_cave_lord_tex/crystal_cave_lord.png.meta`
   - `Assets/_Game/Resources/Art/Enemies/crystal_cave_lord/crystal_cave_lord_mat.meta`
   - `Assets/_Game/Resources/Art/Enemies/crystal_cave_lord/crystal_cave_lord_mat/crystal_cave_lord.mat`
   - `Assets/_Game/Resources/Art/Enemies/crystal_cave_lord/crystal_cave_lord_mat/crystal_cave_lord.mat.meta`
3. 그 밖에 이 폴더 안에서 Unity가 새로 만든 파일이 있으면 같이 올리고 목록을 적어 주세요. `Icons/Enemies/crystal_cave_lord.png.meta`는 이미 PR에 있으니, Unity가 그 파일을 바꿨다면 바뀐 내용도 같이 올려 주세요.
4. `.gitignore` 때문에 빠질 수 있으니 `git add -f`로 올리고, 푸시한 뒤 `git ls-tree -r --name-only origin/local-requests drops/pr12_meta`로 8개 이상 들어갔는지 확인해 주세요.

## 결과
- PR12 검사용 checkout을 `5980700c`로 갱신했습니다. 요청에서 허용한 대로 이전 재검사에서 Unity 6000.3.25f1이 이미 생성한 파일을 재사용했습니다(이번에는 재임포트하지 않음).
- `drops/pr12_meta/` 아래에 저장소 상대 경로를 유지해 필수 8개를 모두 복사했습니다. 해당 모델 폴더 안에 이 8개 외 추가 생성 파일은 없었습니다.
- 추가로 `Assets/_Game/Resources/Icons/Enemies/crystal_cave_lord.png.meta`도 복사해 총 9개입니다. Unity가 sprite 내부 ID/512×512 rect와 기본 importer 직렬화 필드를 추가한 버전입니다. GUID `f723b017a2855edca1c632f86be3fca9`는 유지됩니다.
- 복사한 9개는 각각 원본과 SHA-256이 동일함을 확인했습니다. 원본 FBX/PNG 및 프로젝트 설정·폰트 변경은 포함하지 않았으며 PR 브랜치에는 커밋하지 않았습니다.
