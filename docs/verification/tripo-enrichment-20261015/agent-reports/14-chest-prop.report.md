읽기 전용 검토를 마쳤습니다. **현재 코드에서 확정할 수 있는 상자 결함은 발견하지 못했습니다.** 개선은 기존 공장 캐비닛을 상자 주변의 환경 연출에 재사용하는 한 가지를 권합니다.

1. **우선 확인 — 힌지 간격 계산의 계층 제약**
   [DungeonWorld.cs:325](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:325)의 `ChestWallOffset()`은 `MeshFilter`가 `Lid` 자체에 붙어 있을 때만 열린 뚜껑으로 계산합니다. 나중에 `Lid` 아래에 메시 자식을 넣으면 해당 메시의 회전을 간격 계산에 반영하지 못합니다. 현재 설치 기록은 `Lid` 메시 분리를 설명하므로 **현행 고장이 아닌 모델 교체 시 주의사항**입니다. 뚜껑 계층을 바꾸는 경우에만 자손 메시까지 회전 변환을 반영하도록 확장하면 됩니다.

2. **확인됨 — 개폐·복원·재질 연결은 이미 구현**
   [DungeonWorld.cs:95](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:95)에서 정확한 이름 `Lid`를 찾고 벽 간격을 보정합니다. [404행](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:404)은 열린 상태를 복원하고, [481행](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:481)은 −92° 개방, 오버슈트, 금색 효과, reduced-motion 분기를 제공합니다. 지하철 상자의 importer→재질→`_BaseMap` GUID도 일치합니다.
   
   [상자 복원 기록:37](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/terrain/subway/chest/candidates/prompts.md:37)은 몸체 2,161 + 뚜껑 2,054삼각형, 균일 배율, 원본 UV 복원을 명시합니다. 이전 높이 왜곡 보고를 현재 결함으로 재사용할 근거는 없습니다.

3. **권장 개선 하나 — 공장 상자 주변을 ‘정비·보급 구역’으로 구성**
   이미 설치된 `Art/Environment/factory/decor_1` 캐비닛을 재사용합니다. [최신 설치 기록:32](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/terrain/factory_cabinet/candidates/prompts.md:32)은 원본 9,199삼각형과 2K 텍스처 보존을 명시합니다.
   
   **정확한 다음 작업:** [DungeonWorld.cs:291](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:291)의 `Dress()`에서 공장 상자에 인접한 일반 바닥의 **기존 장식 배치 후보 중 상자당 최대 한 곳**을 결정적으로 골라, 무작위 `decor_1..6` 선택 대신 `decor_1`을 사용합니다. 적합한 후보가 없으면 생략합니다. 기존 배치 확률·벽 간격 보정·오브젝트 수를 유지하고 상자 셀과 통로 중앙은 비워 둡니다. 새 모델·생성 비용 없이 상자 주변에 장소의 맥락을 더할 수 있습니다. 단, 대체 전 모델보다 삼각형 수가 늘 수 있습니다.

파일 수정, 자식 에이전트, Unity 실행, 테스트, 스크린샷 촬영은 하지 않았습니다. 설치 이력은 문서 근거이며 실제 FBX 계층·개방 중 관통·화면 품질은 이번 검토에서 검증하지 않았습니다. 후속 구현의 합격 조건은 부모 세션에서 닫힘→개방→재진입 및 인접 통로 시야를 실제 Unity로 확인하는 것입니다. 요청된 Astra High/priority 라우팅은 이 세션에서 확인 가능한 증거가 없어 검증했다고 주장하지 않습니다.