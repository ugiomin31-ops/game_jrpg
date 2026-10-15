읽기 전용 검토 완료. 스폰·스킬·검증 진입점 모두 확인했으며, 파일·밸런스 변경이나 Unity 실행은 하지 않았습니다.

1. **최우선: 전용 모델의 런타임 연결 확인이 필요합니다.**  
   두 적 모두 현재 `model: "mushroom"`을 참조합니다. 독왕 버섯은 보라색 tint·크기 1.35, 유령 버섯은 옅은 청색 tint·크기 1.0입니다. `elite_mushroom.fbx`가 존재해도 현재 데이터 경로에서는 기본 버섯 모델을 선택합니다. 전용 에셋 추가만으로 시각 보강이 적용됐다고 판정하면 안 됩니다.  
   근거: [enemies.json:1039](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/enemies.json:1039), [enemies.json:5289](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/enemies.json:5289), [ArtLibrary.cs:88](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:88).

2. **독왕 버섯: 소환·광역 독 역할, 2-2 강적 조우가 최적 검증 대상입니다.**  
   `gate_e_2` / **덩굴 회랑**, `foe_b5_1`, 초기 좌표 **(8,1)**. 조합은 `elite_mushroom + mushroom + goblin_shaman`, 강적 배율은 **1.3**입니다. 일반 버섯과 함께 나오므로 실루엣·크기·색 구분을 한 화면에서 비교하기 좋습니다.  
   `summoner` AI이며 빈 소환 슬롯이 있으면 35% 분기에서 `mushroom` 소환을 선택합니다. 소환 제한 설정은 2, 스킬 가중치는 기본 공격/독 포자/맹독 구름 **1:2:2**입니다.  
   근거: [dungeon.json:1148](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/dungeon.json:1148), [EnemyAI.cs:71](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Battle/EnemyAI.cs:71).

3. **유령 버섯: 광역 독·수면 제어 역할, 7-2 고정 이벤트를 권장합니다.**  
   `school_1~3` / **7-1 축제 교문, 7-2 교실 복도, 7-3 축제 무대**의 무작위 조우에 포함됩니다. 추가 배치는 다음과 같습니다.

   | 구역 | 고정 배치 |
   |---|---|
   | 7-2 | **(7,18)** 이벤트: 유령 버섯 3 + wisp 2 |
   | 7-2 | `foe_b20_2` 초기 (15,10), `midboss_b20` 초기 (11,15) |
   | 7-3 | (19,9) 선택 이벤트, `foe_b21_1` 초기 (7,7), showcase 그룹 |

   `caster` AI는 사용 가능한 비기본 스킬이 있으면 75% 분기에서 주문을 선택합니다. 독 포자와 수면의 빛의 가중치는 동일합니다.  
   근거: [고정 이벤트:6294](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/dungeon.json:6294), [EnemyAI.cs:86](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Logic/Battle/EnemyAI.cs:86).

스킬의 데이터상 효과는 다음과 같습니다. 확률은 실제 적중·저항 처리 전 설정값입니다.

| 스킬 | 역할 | MP / 상태 확률 |
|---|---|---|
| 독 포자 | 광역 피해 + `poison` | 3 / 40% |
| 맹독 구름 | 광역 피해 + `poison_strong` | 8 / 60% |
| 수면의 빛 | 광역 `sleep`, 위력 0 | 0 / 25% |

근거: [skills.json:1999](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/skills.json:1999), [4566](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/skills.json:4566), [5397](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/skills.json:5397).

**부모의 정확한 다음 행동:** 모델 연결을 확인한 뒤, `Assets/_Game/Scenes/Main.unity` 기반 현재 빌드에서 아래 인수를 각각 사용해 외형·시전·피격·사망을 관찰하고, 실제 위 고정 조우에서 재확인하십시오.

```text
-review "review=battle&floor=4&groups=elite_mushroom+mushroom+goblin_shaman&level=5&speed=1&loops=1"
-review "review=battle&floor=19&groups=ghost_mushroom+ghost_mushroom+wisp+ghost_mushroom+wisp&level=37&speed=1&loops=1"
```

기존 리뷰 모드는 AUTO이며 **Random 전투·배율 1**로 요청합니다. 따라서 첫 명령은 실제 강적 배율을 재현하지 않고, 한 번의 실행으로 모든 스킬 발동도 보장하지 않습니다. [ReviewBoot.cs:74](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/ReviewBoot.cs:74)

증거 범위는 현재 소스·데이터입니다. 새 런타임 동작, 화면 품질, 상태효과 발동은 검증하지 않았으며 이전 259개 테스트 결과를 이번 시각 보강의 증거로 사용하지 않았습니다.