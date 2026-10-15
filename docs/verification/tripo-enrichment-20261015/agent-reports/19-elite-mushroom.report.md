읽기 전용 점검 완료. 현재 브랜치는 `claude/motion-polish-pr9`이며 파일·설정 변경, 하위 에이전트, Unity 실행·테스트는 하지 않았습니다.

1. **높음 — 전용 모델 연결은 데이터 두 곳을 함께 변경해야 유지됩니다.**  
   현재 배포 [enemies.json:1064](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/enemies.json:1064)과 생성기 원본 [base_enemies.json:1003](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/content/world/base_enemies.json:1003)이 모두 `"model": "mushroom"`입니다. 두 곳의 해당 필드만 `"elite_mushroom"`으로 바꾸는 것이 기능상 최소 변경입니다.  
   생성기는 [enemies.py:165](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/content/world/enemies.py:165)에서 원본 행을 복사하고 능력치를 재계산합니다. 배포 JSON만 바꾸면 재생성 시 원래 모델 연결로 돌아갑니다. `OWN_MODEL_VARIANTS`는 [enemies.py:673](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/content/world/enemies.py:673)의 지역 보스 분기에서 사용되므로 여기에 이름만 추가하는 방식은 이 기존 엘리트에 적용되지 않습니다.

2. **중간 — 자체 모델은 틴트가 자동으로 생략됩니다.**  
   현재 틴트는 `[0.72, 0.45, 1, 1]`입니다. 하지만 [ArtVariants.cs:20](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Data/ArtVariants.cs:20)는 `Model == Id`이면 틴트를 반환하지 않습니다. 따라서 위 두 필드 변경만으로 새 모델의 원래 색상이 유지됩니다. 데이터 의미까지 정리하려면 두 JSON의 해당 `tint`를 `[1,1,1,1]`로 변경하면 됩니다. 이는 권장 정리이며 실행상 필수는 아닙니다.

3. **중간 — 경로·크기·애니메이션 계약을 충족해야 합니다.**  
   [ArtLibrary.cs:17](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:17)의 정확한 로드 경로는 `Art/Enemies/elite_mushroom/elite_mushroom`입니다. 대응하는 `Assets/_Game/Resources/Art/Enemies/elite_mushroom/elite_mushroom.fbx`는 **이미 존재**합니다. 신규 내보내기를 배치하기 전 기존 파일을 보존해야 합니다. 별도 `.prefab` 제작이나 로더 변경은 필요하지 않습니다.

   - `scale_mult: 1.35`는 그대로 유지합니다. 전투에서는 일반 적 가독성 배율 `1.25`가 추가되어 루트 배율은 **1.6875**입니다([BattleView.cs:561](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:561)). 모델 자체에 1.35배를 중복 적용하지 않아야 합니다.
   - `ModelScale`에는 현재 `forest_guardian`만 있습니다. 새 버섯의 추가 배율은 실측 없이 만들지 않는 것이 최소 변경입니다.
   - 모델 루트 Animator와 자체 `Idle` 클립이 필요합니다. 없는 모델은 예외가 발생하며, 호출되는 공격·시전·피격·사망 클립도 확인해야 합니다([CharacterModel.cs:101](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/CharacterModel.cs:101)).
   - Tripo 전용 처리 표시는 같은 폴더의 `TRIPO` 또는 `elite_mushroom.tripo`입니다. 텍스처·재질 폴더 규칙은 `elite_mushroom_tex`, `elite_mushroom_mat`입니다([AbyssArtImporter.cs:132](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Editor/AbyssArtImporter.cs:132)).

**정확한 다음 작업:** 부모가 검증한 신규 FBX를 기존 파일 보존 후 위 경로에 배치하고, 두 JSON에서 해당 적의 `model` 및 선택적으로 `tint`만 수정하십시오. 현재 배포 능력치인 레벨 5, HP/MP 760/40, 공격/마법 34/37, 방어/저항 18/19, 속도 14와 보상·드롭·소환·스킬은 그대로 둡니다. 생성기 원본의 레벨 7 능력치를 배포 행으로 복사하면 안 됩니다.

확인 항목인 데이터 연결·생성기 분기·틴트·배율·로드 계약은 점검했습니다. 기존 dirty 변경도 확인했으며 건드리지 않았습니다. 신규 모델의 실제 크기, 스킨 웨이트, 재질, 애니메이션 및 런타임 정상 동작은 이번 코드 점검으로 검증되지 않았습니다.