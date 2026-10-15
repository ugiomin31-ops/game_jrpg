읽기 전용 점검 결과, **새 소품 제작보다 기존 병원 에셋 활용 여부 확인이 우선**입니다. 병원 폴더에 FBX 27개가 있으며, 명백한 필수 장식 누락은 확인하지 못했습니다.

1. **P3 — 일반 병실 문이 던전 배치에서 사용되지 않는 후보입니다.**  
   `hospital/door.fbx`와 제작 소스가 존재하지만, 확인한 던전 생성 경로는 `L` 셀에 `door_locked`만 생성합니다. 일반 문을 추가할 수 있는 기존 자산입니다.  
   근거: [hospital.py:341](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Blender/environment/hunter_kits_b/hospital.py:341), [DungeonWorld.cs:100](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:100).  
   **다음 행동:** 부모가 병원 맵의 비잠금 병실 출입구 필요성을 확인한 뒤, 필요하면 기존 `door.fbx`를 활용하세요. 현재 통로에 장식으로 무작정 추가하면 통행 가능 여부가 혼동될 수 있습니다.

2. **P3 — `foe_marker.fbx`는 현재 던전 표식 경로에서 사용되지 않습니다.**  
   기존 소스에는 보라색 링·수정 조각·떠 있는 결정이 있습니다. 현재 코드는 적 모델을 생성하고 별도 링·비콘·경고 표식을 붙입니다. 따라서 에셋 후보는 있으나 **적 표식 기능 누락은 아닙니다.**  
   근거: [hospital.py:583](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Blender/environment/hunter_kits_b/hospital.py:583), [DungeonWorld.cs:144](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:144).  
   **다음 행동:** 현 표식 유지가 기본입니다. 병원 전용 시각 변형이 필요할 때만 기존 모델 재사용을 검토하세요.

3. **정보 — 병원 장식 다양성은 이미 구현돼 있습니다.**  
   `decor_1..6`은 침대, 수액대, 휠체어, 약품 카트, 화분, 안내판이며 모두 배치 선택 대상입니다. 바닥·벽 각각 3종과 오버레이 2종도 사용합니다. 전투장 소스에는 대기 의자·접수대·모니터·자판기가 별도로 있습니다.  
   근거: [DungeonWorld.cs:291](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:291), [hospital.py:268](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Blender/environment/hunter_kits_b/hospital.py:268).  
   **다음 행동:** 복도 다양성을 더할 경우 대기 의자를 우선 후보로 검토하되, 이는 개선 제안이며 확인된 결함은 아닙니다.

파일 변경·생성·테스트·Unity 실행은 하지 않았습니다. 미사용 판단은 확인한 런타임 경로에 한정하며, 프로젝트 전체 참조 부재나 실제 화면의 다양성·충돌·가독성을 입증하지 않습니다. 요청된 Astra High/priority의 실제 실행 설정은 이 세션에서 검증할 수 없었습니다.