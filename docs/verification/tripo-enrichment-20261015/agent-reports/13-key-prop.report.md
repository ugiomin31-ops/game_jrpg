**판정: `gate_keycard`는 이미 DungeonWorld의 `key_item`으로 연결되어 있습니다. 미사용 자산이나 연결 누락으로 보고 새 일반 열쇠를 대체 생성할 근거는 없습니다.**

1. **중요 — 남은 차이는 층별 의미와 공용 외형입니다.**  
   [DungeonWorld.cs:109](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:109)는 모든 `K`에 `Common/key_item`을 사용합니다. 반면 [dungeon.json:1235](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/dungeon.json:1235)의 ‘덩굴 문 열쇠’, 1561행의 ‘성소 열쇠’, 8518행의 ‘병동 출입증’은 서로 다른 의미입니다. **층별 이름은 존재하지만 외형 선택에는 반영되지 않습니다.** 이는 아트 적합성 판단 대상이며, 기능 결함으로 단정할 수 없습니다.

2. **확인 — 기존 Tripo 원본에서 런타임 리소스까지 연결 증거가 있습니다.**  
   [key_item.tripo:1](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Art/Props/Common/key_item.tripo:1)은 원본을 `ArtSource/props/gate_keycard/tripo/SOURCE.md`로 명시하고, 균일 배율·피벗 변경을 기록합니다.  
   [key_item.fbx.meta:20](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Art/Props/Common/key_item.fbx.meta:20)의 `M_GateKeycard_Tripo` 참조는 실제 재질 GUID와 일치하며, 재질의 `_BaseMap`도 존재하는 텍스처 GUID와 일치합니다.

3. **확인 — 역할은 일반 잠금문용 소모 열쇠입니다.**  
   [DungeonRun.cs:247](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Dungeon/DungeonRun.cs:247)는 획득 위치를 기록하고 열쇠 수를 증가시킵니다. [DungeonGrid.cs:54](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Dungeon/DungeonGrid.cs:54)는 `L` 문을 열 때 하나를 소비합니다. [DungeonWorld.cs:413](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:413)는 획득한 열쇠를 숨깁니다. 보스 게이트는 다음 행에서 전투 클리어 상태로 처리하므로, 이름이 `gate_keycard`라는 이유로 보스 게이트에 연결하면 의미가 달라집니다.

**정확한 다음 조치:** 기존 연결을 유지하고, 부모가 키카드를 모든 층의 공용 표현으로 허용할지 결정하십시오. 층별 외형이 필요하다고 판단한 경우에만 110행의 고정 리소스 선택을 층/타일셋별 매핑으로 바꾸는 작은 후속 작업이 타당합니다.

읽기 전용 확인을 마쳤습니다. 파일 수정·생성, 자식 실행, Unity 실행, 테스트, 스크린샷 검증은 하지 않았습니다. 실제 표시 크기·방향·가독성과 FBX 내부 형상 동일성은 이번 증거로 확정하지 않습니다. 요청된 Astra High·priority 라우팅의 실제 적용 여부도 이 작업에서 확인할 수 없습니다.