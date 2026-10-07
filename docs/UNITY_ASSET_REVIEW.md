# Unity 화면·에셋·터치 검증 — 2026-10-07

## 버전 기준

기준 브랜치는 `claude/project-thread-65bpbq`, 기준 커밋은 `50ecaf1`이다. 확인 당시 GitHub Pages의 `gh-pages` HEAD는 `1e99196`이며 배포 메시지는 `deploy: e4f72c504747ec417f3c7f5f3ff7de8451e9bd60`이다. `e4f72c5`와 `50ecaf1`의 차이는 `memory/PRODUCT-TRUTH.md`뿐이므로 게임 코드·에셋 기준은 같다.

이 개선은 PR #3의 `codex/modern-ui-smart-battle`에 있다. Pages에 배포된 화면이라는 뜻이 아니다. `Assets/Temp/battle-framing-preview.png`는 오래된 참고 이미지이며 이번 검증 근거에서 제외한다. 아래 캡처는 이 PR을 실제 Unity에서 실행해 얻었다.

## 적용한 개선

- 최신 텍스처 캐릭터·조형 몬스터를 유지하면서 공통 툰 재질의 두꺼운 윤곽, 강한 림광, 급격한 그림자 경계를 줄였다. 기존 재질도 갱신하고 배치 빌드 준비 단계에도 같은 조정을 적용한다.
- 마을의 과도한 노란 광원·블룸을 낮추고, 네 사냥터의 발광과 색보정을 조정했다. 서비스 색상의 깃발과 분수 화단을 제작 원본에 추가하고 Blender로 마을 FBX·편집 원본·미리보기를 실제 재생성했다.
- 스킬 효과 중 큰 발광 빌보드와 과밀한 입자층을 줄였다. 바닥 범위, 투사체, 타격·궁극기의 타이밍과 범위 표현을 유지한다.
- 작은 휴대폰에서는 AUTO·전투 명령·확인창·마을 시설·수첩 버튼이 최소 44 화면 픽셀 높이를 갖도록 조정했다. 전투 선택은 터치에서 페이지당 4개를 보여 주며, 결과 확인 버튼과 안내문 겹침도 수정했다.
- 태블릿에서 고정된 세로 시야각 때문에 양쪽 동료가 잘리던 전투 구도를 화면 비율에 맞춰 조정했다. 일반·행동·궁극기·전투 진입 카메라에 같은 기준을 적용한다.
- 공통 재질과 조명 개선은 전체 분류에 적용했다. 캐릭터·몬스터·장비 전체를 새 모델로 재제작한 작업은 아니다.

## 실제 검증

다른 작업 중인 Unity 프로젝트와 저장 데이터를 건드리지 않도록 Windows PC에 별도 Git 클론을 만들었다. Unity **6000.3.25f1**에서 실제 패키지·URP·Input System을 사용했다. 플레이 검증은 별도 제품 이름으로 저장 폴더를 분리했다.

| 검사 | 결과 | 근거 |
|---|---|---|
| Unity 의미 컴파일 | 오류 0건, `compilationFailed=false` | [콘솔 기록](verification/console.json), `Tools/unity_check.py --no-recompile` |
| Windows x64/Mono 빌드 | 실제 Unity 빌드 성공 | [빌드 보고서](verification/windows-build.json) |
| 제작 모델·재질·지원 셰이더 | FBX 298개, 문제 0건 | [모델 검사](verification/asset-audit.json) |
| 배우 애니메이션 | 캐릭터·몬스터·NPC의 Animator와 필수 7개 클립 확인 | 동일 모델 검사 |
| 게임 데이터 참조 | 동료 4, 몬스터 51, 장비 48 및 마을·바이옴 리소스 확인 | 동일 모델 검사 및 빌드 전 콘텐츠 검사 |
| 스킬 효과 | 221개 실제 생성·시작·중지, 텍스처 누락 0건 | [효과 검사](verification/vfx-audit.json) |
| 휴대폰 915×412 | 터치 검증 21/21 통과 | [휴대폰 결과](verification/mobile-review-915x412.json) |
| 태블릿 1024×768 | 터치 검증 21/21 통과 | [태블릿 결과](verification/mobile-review-1024x768.json) |
| 전투·보상·장비 로직 | 32/32 통과 | `python Tools/logic_test.py`, [상세 기록](UI_COMBAT_UPGRADE.md) |

298개 모델은 동료 4, 적 51, NPC 8, 사냥터 부품 108, 마을 1, 무기 20, 기타 장비 28, 아이템·상태·원소·UI·공통 소품 78개다. 전체의 렌더러와 재질을 검사했고 동료·몬스터·장비는 Unity 렌더링 갤러리로 확인했다.

터치 검증은 실제 `Touchscreen` 이벤트를 Input System에 넣고 게임의 UI 입력 모듈로 전달했다. 마을 스틱 이동·손 떼기, 시설 열기, 회복 확인/취소, 중복 제출 차단, 미궁 회전·지도, 네 바이옴 로딩, AUTO 켜기·승리·보상 확인·다음 전투 유지가 포함된다. 중복 입력 차단 시점은 버튼 직접 제출도 별도로 확인했다. 전투와 층 이동에는 재현 가능한 초기 상태를 사용했으며 자연스러운 전체 캠페인 완주 검증은 아니다.

초기 에디터 실행에는 오류가 없었지만 `Ran out of Graphics Ring Buffer space` 같은 경고가 최종 입력 검증 스트림에 2회 기록되었다. [이전 콘솔 기록](verification/console-history.json)에 원문을 보관했다. 모든 효과를 생성할 수 있다는 결과가 모든 연출의 프레임별 품질·실기기 성능을 보장하지는 않는다.

## 실제 화면

| 화면 | 휴대폰 | 태블릿 |
|---|---|---|
| 마을 | [화면](verification/town-915x412.png) | [화면](verification/town-1024x768.png) |
| 확인창 | [화면](verification/confirmation-915x412.png) | [화면](verification/confirmation-1024x768.png) |
| 숲의 유적 | [화면](verification/dungeon-915x412.png) | [화면](verification/dungeon-1024x768.png) |
| 빙결 동굴 | [화면](verification/frost_grotto-915x412.png) | [화면](verification/frost_grotto-1024x768.png) |
| 불타는 동굴 | [화면](verification/ember_caverns-915x412.png) | [화면](verification/ember_caverns-1024x768.png) |
| 망자의 묘소 | [화면](verification/haunted_crypt-915x412.png) | [화면](verification/haunted_crypt-1024x768.png) |
| 전투 | [화면](verification/battle-915x412.png) | [화면](verification/battle-1024x768.png) |
| 전투 결과 | [화면](verification/battle-result-915x412.png) | [화면](verification/battle-result-1024x768.png) |

[동료 4명](verification/heroes.png), [몬스터 51종](verification/enemies.png), [장비 48종](verification/equipment.png)의 갤러리는 실제 리소스 모델을 Unity 카메라로 렌더링했다. 각 `*-index.json`의 순서대로 왼쪽부터 읽는다.

## 재현 방법과 남은 범위

연결된 Unity CLI에 프로젝트 경로를 명시한다. 검증 도구는 `Assets` 밖에서 임시 컴파일되며 플레이어에 포함되지 않는다.

```text
python Tools/unity_check.py --project-path <project>
unity command run_script --project-path <project> -- --file Tools/UnityReview.cs --entry UnityReview.Audit
# 이후 Play 모드에서 실행
unity command run_script --project-path <project> -- --file Tools/UnityReview.cs --entry UnityReview.AuditEffects
unity command run_script --project-path <project> -- --file Tools/UnityReview.cs --entry UnityReview.PhoneView --args '[915,412]'
unity command run_script --project-path <project> -- --file Tools/MobileReview.cs --entry MobileReview.Begin
# Play 모드를 끈 뒤 실제 Windows 빌드 요청·완료 보고서 확인
unity command run_script --project-path <project> --timeout 600 -- --file Tools/UnityReview.cs --entry UnityReview.BuildWindows --timeout_ms 540000
```

`MobileReview`는 검증용 새 게임과 설정을 기록한다. 별도 클론·저장 폴더에서만 실행하고 완료된 `Review/mobile-review-<width>x<height>.json`을 확인한다.

`BuildWindows`는 플레이 모드와 스크립트 리로드가 완전히 멈춘 상태에서 실행한다. 명령 제한 시간을 600초로 지정하고 실제 빌드 보고서를 보관한다. 최종 판정은 `Review/windows-build.json`의 실제 `BuildReport`로 확인한다. 초기 빌드는 210초 명령 제한을 넘어 응답이 중단되었지만 Unity에서는 계속 실행되어 성공했다. 플레이어에서 검증 도구 Pipeline이 비활성화된다는 경고는 게임 콘텐츠 누락을 뜻하지 않는다. Windows 출력물은 검증 PC의 `Build/Windows/`에 있으며 Git에 실행 파일을 추가하지 않았다.

현재 PC에는 Windows 빌드 모듈만 설치되어 있으며 `adb devices -l`에 연결된 휴대폰이 없다. 이번 PR의 Android/iOS 실기 실행과 WebGL 재빌드·Pages 배포는 검증하지 않았다. 실제 단말의 안전 영역·OS 뒤로 버튼·성능, 키보드/게임패드 전체 동작, 전체 캠페인·보스·엔딩·경제 균형은 추가 관찰이 필요하다.
