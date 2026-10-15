# 29 — CharacterModel bounded source audit

- 요청 모델/effort: `gpt-6-astra` / `high`.
- 요청 서비스 티어: Fast/priority. 실제 모델 ID, effort 및 서비스 티어는 이 감사에서 독립적으로 확인할 수 있는 실행 메타데이터가 없어 검증하지 못했다. 설정 변경이나 모델 전환은 수행하지 않았다.
- 확인한 작업 기준: branch `codex/astra-enrichment-20261015`, HEAD `efdc1517`.
- 범위: `CharacterModel.cs`의 facing, bone mapping, renderer bounds, skeleton/socket attachment와 직접 관련된 생성·장비·전투 호출 경로. 정적 읽기 전용 감사이며 이 보고서만 작성했다.

## 결과

**보고할 구체적이고 도달 가능한 결함: 0건.** 확인한 소스만으로 재현 경로와 영향을 함께 입증할 문제를 찾지 못했다. 이는 런타임 시각 품질이나 모든 모델 에셋의 리깅 정상 판정을 뜻하지 않는다.

확인 근거:

- 방향: `Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:106-109`에서 visual을 별도 캐릭터 root 아래 생성하며, `Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:583-585`에서 진영별 방향을 그 root에 적용한다. `CharacterModel` 자체가 이를 덮어쓰는 경로는 없다.
- 본 매핑: `Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:146-152`는 이름 일치 본을 우선 사용하고 Humanoid일 때만 `weapon.R`/`weapon.L`을 해당 손으로 대체한다. `:169-195`의 손가락 기반 grip과 `:224-229`의 authored socket 구분을 확인했다. 전투 장비 부착 전 socket 검사도 `BattleView.cs:592-594`에 있다.
- 경계: `CharacterModel.cs:113-127`은 ParticleSystemRenderer를 제외하고 합산하며 flyer는 rest bounds를 사용한다. 영웅 표시 크기 변경 후 `ArtLibrary.cs:72-75`, 전투 적 크기 변경 후 `BattleView.cs:558-562`에서 재계산한다. 실제 임포트 bounds의 적정성이나 애니메이션 중 외형과의 일치는 이번 정적 검사로 확인하지 않았다.
- 부착: `CharacterModel.cs:210-236`에서 기존 socket attachment의 renderer/tint 목록 제거, 비활성화 및 파괴, 본 아래 새 인스턴스 생성, grip 및 scale 적용을 확인했다. `Assets/_Game/Scripts/Runtime/Art/GearDisplay.cs:87-112`의 후속 무기 크기·재질 처리도 확인했다. 이 메서드는 정적 장비 부착이며 스킨 웨이트 생성·재매핑을 수행하는 코드가 아니다.

## 수락 체크

- [x] 지정 branch와 HEAD 확인.
- [x] 지정 소스 및 직접 관련 호출부만 집중 검색·열람.
- [x] 최대 2건 제한 준수; 입증되지 않은 가설은 결함으로 보고하지 않음.
- [x] 중첩 에이전트, 테스트, 빌드, Unity/editor/browser, 네트워크, 이미지/Tripo, 인증정보·대화기록 접근 없음.
- [x] 게임 소스·설정·UI·바이너리 수정 없음; 지정 보고서만 작성.
- [x] 요청 모델/effort와 요청 티어를 기록하고 실제 검증 여부를 분리.
