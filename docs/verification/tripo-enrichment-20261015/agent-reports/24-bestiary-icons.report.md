읽기 전용 검토 결과, **이름·설명 연결은 정상이며, 별도 모델 전환 시 아이콘·색상·동작 타이밍을 함께 확인해야 합니다.** 파일은 수정하지 않았습니다.

1. **P1 — 별도 모델로 전환하면 기존 보라색 틴트가 적용되지 않습니다.**  
   현재 [enemies.json:1064](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/enemies.json:1064)은 `"model": "mushroom"`입니다. [ArtVariants.cs:22](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Data/ArtVariants.cs:22)는 모델이 자기 ID이거나 빈 문자열이면 틴트를 반환하지 않습니다. 따라서 새 FBX 설치 후 `"model": "elite_mushroom"`으로 변경해도 `[0.72, 0.45, 1, 1]`을 유지하는 것만으로 보라색이 보존되지는 않습니다.  
   **요건:** 새 모델의 실제 색을 확인하고, 보라색이 필요하면 해당 모델에 한정한 재질 또는 틴트 적용을 명시적으로 처리해야 합니다. 다른 몬스터의 공통 틴트 규칙 변경은 피해야 합니다.

2. **P2 — 도감 아이콘도 모델 별칭을 따라갑니다.**  
   [GameUI.Town.cs:283](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/UI/Screens/GameUI.Town.cs:283)는 적 ID를 넘기지만, [UIArtwork.cs:64](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/UI/Kit/UIArtwork.cs:64)가 이를 모델 ID로 변환합니다. 현재 도감은 **`mushroom.png`**를 사용하며, 전용 `elite_mushroom.png`는 이 경로에서 선택되지 않습니다. 모델을 자기 ID로 전환하면 전용 아이콘으로 자동 전환됩니다.  
   **기존 이미지 재사용 요건:** 기존 `elite_mushroom.png`와 `.meta`를 보존하고 사용하십시오. 직접 확인한 두 아이콘은 사실상 같은 실루엣의 색상 변형입니다. 기존 후보 D는 큰 팔과 뚜렷한 표정 등 형태가 다르므로, 이 아이콘을 새 모델과 외형까지 일치한다고 표현해서는 안 됩니다. 후보 D 원본은 회색 배경의 콘셉트 이미지이므로 투명 게임 아이콘에 그대로 덮어쓰는 것도 권하지 않습니다. 모델 설치 전 아이콘만 구분하려면 `UIArtwork.Enemy`에 `elite_mushroom` 한정 아이콘 선택이 필요하며, 이를 위해 모델 별칭을 먼저 변경하면 안 됩니다.

3. **P2 — 새 모델에는 기존 시전 타이밍 보정이 자동 승계되지 않습니다.**  
   [ArtLibrary.cs:201](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:201)의 `mushroom/Cast = .27f`는 모델 ID 기준입니다.  
   **요건:** 새 모델의 Cast 클립을 확인해 `elite_mushroom/Cast` 보정 필요 여부를 결정하십시오. 기존 값을 측정 없이 복사하지 말고, `scale_mult: 1.35` 역시 새 모델에서 과대 확대되지 않는지 확인해야 합니다.

**이름·설명은 유지해도 됩니다.** [enemies.json:982](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/enemies.json:982)의 `독왕 버섯`, [text_ko.json:459](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/text_ko.json:459)의 “독버섯 무리를 거느린 왕. 맹독 구름을 내뿜는다.”는 소환 목록과 `sk_toxic_cloud`에 부합합니다. [quests.json:75](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/quests.json:75)의 이름·대상 ID도 일치합니다. ID, 도감 설명 키, 퀘스트 대상, 전투 수치는 변경할 이유가 없습니다.

**정확한 다음 조치:** 부모가 새 모델의 임포트·스킨 검증을 마친 뒤 모델 별칭을 변경하고, 기존 전용 아이콘을 재사용하면서 색상·배율·Cast 타이밍을 검증하십시오. 아이콘 manifest의 기존 렌더 출처를 새 모델에서 생성한 기록처럼 갱신하지 말고, 기존 이미지 재사용임을 기록해야 합니다.

검토 항목인 표시 연결·기존 이미지·모델 전환 영향은 확인했습니다. Unity 실행·테스트·스크린샷 검증은 하지 않았으며, 새 모델의 런타임 완료를 판정하지 않았습니다. 요청된 Astra High/priority의 실제 라우팅은 이 세션의 도구 결과로 확인할 수 없었습니다.