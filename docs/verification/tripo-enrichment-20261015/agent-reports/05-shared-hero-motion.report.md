**P2 — 윤지호(`h_jiho`)의 `[오의] 유성연사`에 활 발사용 `Ultimate` 모션이 없습니다.** 현재 공백은 궁극기 자체의 부재가 아니라, 공용 슬램을 대체할 궁수용 클립의 부재입니다.

- **기존 스킬 연결:** 윤지호는 레벨 8에 `ult_starfall_volley`를 배웁니다([heroes.json:360](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/heroes.json:360)). 스킬은 화살 8발, `pr_ult_archer` 연출을 지정합니다([skills.json:6434](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/skills.json:6434)).
- **현재 클립:** 공용 `HumanoidAnimations/Ultimate.fbx`는 존재하며, 현재 설치 기록은 이를 Tripo **Power Jump and Slam**으로 명시합니다([INSTALL.md:208](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/hunters/_anim_library/INSTALL.md:208)). 실제 폴더에서 궁수 클래스는 `Attack`, `BattleIdle`, 윤지호는 `BattleIdle`, `Victory`만 확인됐습니다.
- **선택 경로:** 궁극기는 `Ultimate`를 우선 선택하고 `PlanHeroTake`를 건너뜁니다. 따라서 이미 설치된 궁수의 활 당기기 `Attack`으로 대체되지 않습니다([BattleView.cs:705](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:705)).
- **접촉 매핑:** `Ultimate` 기본값은 `44/66 ≈ 0.667`입니다([BattleView.cs:903](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.cs:903)). 클래스·영웅 접촉 표에는 `archer/Ultimate`, `h_jiho/Ultimate`가 없습니다([ArtLibrary.cs:194](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:194)).

**정확한 다음 작업:** 부모가 Tripo Studio에서 윤지호용 활 당김→명확한 발사→회복 모션 한 개를 확보해 `HumanoidAnimationsByHero/h_jiho/Ultimate.fbx`로 설치하고, 실제 발사 프레임을 측정해 `ClassContact["h_jiho/Ultimate"]`를 등록하는 것이 적절합니다. 이후 실제 전투에서 유성연사의 투사체·타격 시점과 맞는지 검증해야 합니다.

읽기 전용으로 파일·매핑 확인을 마쳤습니다. 파일 수정, 테스트, Unity 실행은 하지 않았으며, 슬램의 시각적 형태는 설치 기록에 근거합니다. 현재 런타임 화면이나 발사 동기화 실패를 직접 관측한 결과는 아닙니다.