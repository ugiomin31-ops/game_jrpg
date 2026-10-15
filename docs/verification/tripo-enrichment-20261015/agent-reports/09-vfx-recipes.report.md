추천 대상은 **① [오의] 메테오, ② 눈보라**입니다. 둘 다 기존 Tripo 메시가 있으나, 아래 특정 낙하 레이어에는 연결되지 않았습니다. 기능 오류 판정이 아닌 시각 개선 우선순위입니다.

1. **우선순위 1 — `[오의] 메테오`의 작은 운석 소나기**
   - 연결: `ult_meteor → pr_ult_mage → area_vfx: ultimate_mage`. [스킬 정의](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/skills.json:6388), [연출 연결](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/presentation.json:2646).
   - 현재: [effects.json:2259](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Vfx/effects.json:2259)의 `emitter / texture: meteor`에는 `mesh`가 없습니다. 중앙 운석의 `meteor_rock`, 충돌구, 화염 메시 레이어는 이미 있습니다.
   - **권장 매핑:** 작은 운석 emitter에 `mesh: "meteor_rock"`, `texture: "mesh_meteor_rock"` 적용. 현재 `rate:13.5`, `life:0.45`, `size:1.4`, `speed:-9`, `radius:4.32`, `y:3.6`, `delay:0.1`, `upright:true`를 첫 비교 기준으로 유지합니다.
   - 선정 이유: 전체 대상 3연타 오의의 핵심인 운석 소나기를 기존 중앙 운석과 동일한 입체 형태로 표현할 수 있습니다.

2. **우선순위 2 — `눈보라`의 지속 낙하 얼음 파편**
   - 연결: `sk_blizzard → pr_blizzard → area_vfx: blizzard`. [스킬 정의](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/skills.json:2435), [연출 연결](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/presentation.json:1944).
   - 현재: [effects.json:11390](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Vfx/effects.json:11390)의 `emitter / texture: ice_shard`에는 `mesh`가 없습니다. 회오리 `tornado_funnel`과 일회성 `burst: ice_shard`는 이미 연결돼 있습니다.
   - **권장 매핑:** 낙하 emitter에 `mesh: "ice_shard"`, `texture: "mesh_ice_shard"` 적용. 현재 `rate:40.5`, `life:0.7`, `size:0.3`, `speed:-7`, `radius:4.59`, `y:3`, `delay:0.1`, `upright:true`를 첫 비교 기준으로 유지합니다.
   - 선정 이유: 일회성 파편과 지속 낙하 파편의 형태를 통일하고, 전장 전체에 내리는 냉기 공격의 깊이감을 강화할 후보입니다.

**정확한 다음 조치:** 부모 작업에서 [메테오 생성 정의](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/vfx/gen_effects.py:241)와 [눈보라 생성 정의](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Tools/vfx/gen_effects.py:878)의 해당 emitter만 매핑하고, 생성된 JSON에도 반영합니다. 이후 실제 전투에서 크기·밀도·캐릭터 가림·성능을 비교해야 합니다. 기존 렌더러는 메시 emitter와 `upright`의 속도 방향 정렬을 지원합니다. [구현 근거](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:341)

검토 항목인 스킬 연결, 현재 레이어, 두 FBX와 텍스처의 존재, 변경 위치를 확인했습니다. 파일 수정·테스트·Unity 실행은 하지 않았으며, 실제 시각적 개선과 성능은 미검증입니다. 요청된 Astra High·priority 라우팅은 이 세션에서 독립적으로 확인할 수 없었습니다.