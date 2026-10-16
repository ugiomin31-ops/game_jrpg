# 요청: PR #12 수정 동굴 보스(crystal_cave_lord) 새 모델을 Unity에서 확인

상태: **open**  (끝나면 이 줄을 `done`으로 바꾸고 결과를 아래 "결과"에 적어 주세요)
요청한 곳: 클라우드 스레드 "수정 동굴 4족 몬스터 웨이트 실패 원인 조사", PR #12 (https://github.com/ugiomin31-ops/game_jrpg/pull/12)

수정 동굴 보스가 `crystal_horror` 색 변형 대신 자체 모델(`Assets/_Game/Resources/Art/Enemies/crystal_cave_lord/`)을 씁니다. Blender에서는 검증을 끝냈지만, 클라우드에서는 Unity를 실행할 수 없어서 실제 에디터 임포트 확인을 부탁드립니다. **파일을 고치거나 PR 브랜치에 커밋하지 말고 확인만** 해 주세요.

## 1. 브랜치 받기
- 브랜치 **`claude/project-thread-69lmhy`** (PR #12 head, 커밋 `8973a49` 이상)를 `git worktree add`로 별도 폴더에 받습니다. PR #10 확인용 worktree와 섞이지 않게 해 주세요.
- Unity 6000.3.25f1로 엽니다. batchmode 전체 임포트 + `Abyss.EditorTools.AbyssProjectSetup.ValidateContent` 실행(PR #10 확인 때와 같은 방법)이면 충분합니다.

## 2. 확인할 것
1. Console의 **빨간 오류**와, `crystal_cave_lord`·`AbyssArtImporter`·`TexturedMaterials`·`Missing`이 들어간 경고를 그대로 적어 주세요.
2. `Validate Production Content` 결과 메시지를 적어 주세요.
3. `crystal_cave_lord.fbx` 임포트 결과를 적어 주세요(Inspector 또는 로그로).
   - Rig 탭: Animation Type(Generic이어야 함), Avatar 생성 여부
   - Animation 탭: 클립 이름 7개 `Idle, Run, Attack, Cast, Hit, Die, Victory`가 있는지, `Idle`·`Run`이 Loop Time 켜짐인지
   - 재질: `crystal_cave_lord_mat/crystal_cave_lord.mat`이 만들어지고 텍스처(`crystal_cave_lord_tex/crystal_cave_lord.png`)가 연결됐는지(분홍·흰색이면 실패)
4. 가능하면 GUI 에디터에서 FBX를 씬에 끌어다 놓고 Animation 미리보기로 `Idle`·`Attack`·`Die`를 재생해 본 뒤, 다리·꼬리가 몸에서 찢어지거나 바닥을 뚫는지 봐 주세요. 스크린샷 1~2장을 `docs/verification/pr12-unity-check/`에 넣어 주세요.
5. 가능하면 전투에서 이 보스를 띄워 크기가 전투 칸에 맞는지 봐 주세요(어렵다면 생략).

## 3. 하지 말 것
- PR #12 브랜치에 커밋·푸시하지 마세요. Unity가 만든 `.meta`·`.mat`도 커밋하지 마세요(결과에 "생성됨"만 적어 주세요).
- Tripo Studio는 열 필요가 없습니다.

## 4. 결과 올리기
- 이 파일의 "결과"에 적고 상태를 `done`으로 바꾼 뒤 **`local-requests`** 브랜치에 커밋·푸시해 주세요. 스크린샷도 같은 커밋에 넣어 주세요.

## 결과
(여기에 적어 주세요)
