읽기 전용 점검을 마쳤습니다. **캐비닛은 미사용이 아니며 현재 FBX의 축·크기도 정상입니다.** 구체적인 문제는 다음과 같습니다.

1. **P2 — 공장 전투장 상자 뚜껑 4개가 본체보다 약 0.32m 떠 있습니다.**  
   [factory.py:599](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Blender/environment/hunter_kits/factory.py:599)에서 상자와 뚜껑을 각각 `scale=1.6`, 뚜껑 높이를 `1.6`으로 배치합니다. 현재 `factory/arena.fbx`를 직접 읽은 결과 본체 상단은 **1.279997m**, 뚜껑 하단은 **1.6m**였습니다. 이는 [BattleView.cs:164](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:164)가 실제 로딩하는 자산입니다.  
   **다음 조치:** 원본 상자의 실제 높이에 맞춰 뚜껑 위치를 약 `1.28m`로 조정하고, 승인된 자산 정리 절차로 설치 FBX에 반영한 뒤 화면 확인.

2. **P2 — 캐비닛이 소형 소품 폴리곤 예산을 초과합니다.**  
   현재 `factory/decor_1.fbx`는 **9,199면**이며, [원본 기록:32](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/terrain/factory_cabinet/candidates/prompts.md:32)도 9,199삼각형 복원을 명시합니다. 프로젝트 소형 소품 기준인 3,000–6,000삼각형보다 높습니다. 이전 4,999삼각형 정리 기록은 현재 파일 상태가 아닙니다.  
   **다음 조치:** 부모 작업에서 기존 정리본의 보존 여부를 확인하고, 허용된 파이프라인으로 3k–6k 예산을 복구. 성능 저하 자체는 측정하지 않았습니다.

3. **P3 — 캐비닛 교체는 탐험에만 연결되어 있습니다.**  
   [DungeonWorld.cs:309](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:309)는 `decor_1..6`을 선택하지만 전투장은 별도 `arena.fbx`를 로딩합니다. 현재 arena에는 캐비닛 메시·재질이 없으며, [factory.py:580](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Blender/environment/hunter_kits/factory.py:580)의 전투장 구성도 기존 컨베이어·프레스 등을 사용합니다.  
   **다음 조치:** 전투장까지 캐비닛을 적용하려는 요구가 있다면 별도 배치가 필요합니다. 탐험 전용 의도라면 결함이 아닙니다.

확인된 정상 연결:

- 현재 맵과 배치 수식을 계산하면 `factory_1/2/3`에 캐비닛이 각각 **9/10/9개** 선택됩니다. 실제 실행 관측치는 아닙니다.
- 캐비닛 FBX는 Y-up, 높이 **0.70001m**, 폭 **0.70001m**, 깊이 **0.384944m**, 기본 회전·스케일입니다. 과거 눕던 문제를 현재 결함으로 볼 근거는 없습니다.
- [ArtLibrary.cs:303](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:303)는 환경 자산을 추가 크기 보정 없이 생성합니다.

원본·설치 FBX·로딩 경로·배치 조건 확인을 완료했습니다. 파일 수정, 자식 실행, Unity 실행, 스크린샷 및 테스트는 수행하지 않았으므로 화면 품질이나 새로운 런타임 통과를 주장하지 않습니다.