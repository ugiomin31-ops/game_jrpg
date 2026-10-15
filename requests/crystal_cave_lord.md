# 요청: 수정 동굴의 주인 (crystal_cave_lord) Tripo 메시

상태: **open (재요청)**  (끝나면 이 줄을 `done`으로 바꾸고 결과 경로를 아래 "결과"에 적어 주세요)
요청한 곳: 클라우드 스레드 "수정 동굴 4족 몬스터 웨이트 실패 원인 조사", PR #12

새로 만들지 말고 **이미 있는 결과를 내려받기만** 하면 됩니다. 크레딧이 드는 버튼(Generate, Retry, Rig, Animate, 구매)은 누르지 마세요. Export가 유료로 표시되면 거기서 멈추고 "결과"에 그렇게 적어 주세요.

## 1. PC에 이미 있는지 먼저 확인
원래 위치는 `C:\Users\User\Desktop\GAME_JRPG\...\ArtSource\hunter-bosses\crystal_cave_lord\tripo_export\`(FBX와 `.fbm` 텍스처 폴더) 또는 `crystal_cave_lord_tripo.zip`(11.4 MB)입니다. 있으면 그 파일을 그대로 아래 4번처럼 올려 주세요.

## 2. 없으면 Tripo Studio에서 찾기
- 작업 ID: `e207ee73-40fd-4837-b072-580d5e49053f`
- 모습: 노란 안전모를 쓴 둥근 천산갑·두더지형 4족 괴물, 등에 큰 수정 가시 5개, 어깨에 녹슨 레일
- 리토폴로지 결과(약 10,316 tris)가 있는 버전입니다. 리그가 실패한 상태여도 괜찮습니다. 리그는 버리고 메시와 텍스처만 씁니다.

## 3. 내보내기 설정
- 형식 **FBX**, 프리셋 **Blender**, 텍스처 **2k**, 애니메이션 없음 (Skeleton은 켜든 끄든 상관없음)
- 저장 이름: `crystal_cave_lord_tripo.zip`
- FBX가 안 되면 GLB(텍스처 포함)로 `crystal_cave_lord_tripo.glb`

## 4. 올리기
- 브랜치 **`tripo-glb-drop`**에 `ArtSource/enemies/crystal_cave_lord/` 아래로 커밋·푸시해 주세요. ZIP을 풀어서 FBX 1개와 텍스처 폴더/PNG를 넣어도 되고 ZIP 그대로 넣어도 됩니다.
- 끝나면 Studio 탭을 닫아 주세요.

## 결과
- 브랜치 `tripo-glb-drop` 커밋 a298d70: `ArtSource/enemies/crystal_cave_lord/crystal_cave_lord_tripo.zip` (11,360,151 B, ZIP 그대로) + `DROP_NOTE.md`
- 1번 단계에서 PC에 있던 원본(`C:\Users\User\Desktop\game\ArtSource\hunter-bosses\crystal_cave_lord\crystal_cave_lord_tripo.zip`, 2026-10-11 내보내기)을 그대로 올렸습니다. Tripo Studio는 열지 않았고 크레딧 0.
- 내용: FBX 1개(`tripo_convert_423ed2f0-...fbx`, Blender 프리셋, 2k) + `.fbm` 텍스처 5장. 들어 있는 리그는 실패한 첫 번째 Other 리그이므로 메시·텍스처만 쓰세요.
- 리그 재시도 버전 `crystal_cave_lord_tripo_r2.zip`도 PC에 있지만(리그 역시 실패) 올리지 않았습니다.

## 재요청 (2026-10-15 23:55, 클라우드 스레드)
ZIP이 커밋에 들어가지 않았습니다. 커밋 a298d70에는 `DROP_NOTE.md`만 있습니다. 저장소 `.gitignore` 116행의 `/ArtSource/**` 규칙 때문에 ArtSource 아래 ZIP은 `git add`에서 조용히 빠집니다.
같은 ZIP을 **`motion/`처럼 무시되지 않는 최상위 폴더** `drops/crystal_cave_lord_tripo.zip`에 두고 `tripo-glb-drop` 브랜치에 커밋·푸시해 주세요. 또는 `git add -f ArtSource/enemies/crystal_cave_lord/crystal_cave_lord_tripo.zip`을 써도 됩니다. 푸시한 뒤 `git ls-tree -l origin/tripo-glb-drop`로 ZIP이 들어갔는지 확인하고, 상태를 다시 done으로 바꿔 주세요. r2 ZIP은 필요 없습니다.
