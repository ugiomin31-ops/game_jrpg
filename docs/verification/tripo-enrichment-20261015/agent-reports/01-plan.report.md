**권장 1차 범위는 엘리트 버섯 1종 → 서아 시전 동작 1종 → 심판의 망치 형상 1종 → 기존 키카드 가독성 개선입니다.** 파일럿 합격 전 후속 유료 제작은 보류합니다.

1. **P0 — `elite_mushroom`: 후보 D로 진행 중인 생성 결과 검수**
   - B/D 이미지를 직접 비교했습니다. D의 높은 갓, 큰 팔 돌기, 날카로운 눈썹은 일반 버섯 B와 구분됩니다. 다만 정면 T/A 포즈가 아니므로 어깨와 갓 아래 메시가 붙거나 팔 가동을 방해하는지 확인해야 합니다.
   - 최신 [SOURCE.md:11](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/enemies/elite_mushroom/enrichment_20261015/SOURCE.md:11)에 **이미 생성 1회 제출, 55크레딧, 3460→3405**가 기록되어 있습니다. 계획 문서의 “사용 0”은 이 기록보다 오래되었습니다. 추가 생성하지 않습니다.
   - 원본 보존: `ArtSource/enemies/elite_mushroom/enrichment_20261015/`.
   - 통합: `Assets/_Game/Resources/Art/Enemies/elite_mushroom/elite_mushroom.fbx`; [enemies.json:1064](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/enemies.json:1064)의 해당 적 `model`만 `mushroom`→`elite_mushroom`.
   - 게이트: Triangle Smart Mesh 12k, 2k 텍스처, Humanoid/Mixamo, skeleton 포함 FBX. Blender에서 팔·다리 실제 변형 확인 후 기존 보라색 틴트와 소환 동작을 검수합니다. 능력치·스킬은 유지합니다.

2. **P1 — 서아 전용 `Cast`: 명확한 모으기→방출→복귀**
   - 현재 서아 전용 폴더에는 `Attack.fbx`만 있습니다. 이는 시전 기능 누락이 아니라 기존 공용/직업 폴백을 전용 동작으로 보강할 기회입니다. 기존 `Spell`은 [계획:39](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/plan/2026-10-15-tripo-enrichment.md:39)에 거절된 후보로 명시되어 있습니다.
   - 제안: 발을 안정적으로 디디고 손·무기를 모은 뒤 전방 방출, 전투 대기로 복귀하는 Tripo 동작 1종.
   - 원본: **신규 제안 경로** `ArtSource/hunters/h_seoa/enrichment_20261015/`.
   - 통합: `Assets/_Game/Resources/Art/HumanoidAnimationsByHero/h_seoa/Cast.fbx`.
   - 기존 [ArtLibrary.cs:149](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Art/ArtLibrary.cs:149)의 계층 로더와 `ClassContact`를 사용합니다. 실제 방출 프레임을 측정해 `h_seoa/Cast` 값을 지정하고, [BattleView.Moves.cs:109](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/Battle/BattleView.Moves.cs:109)의 선택 경로에서 확인합니다.

3. **P2 — ‘심판의 망치’에 읽히는 망치 형상 추가**
   - [skills.json:6688](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Data/skills.json:6688)은 빛의 망치 기술이지만, 현재 `pr_c_hammer`는 `stun_slam`과 `area_quake`를 사용합니다. 이름과 효과를 연결하는 구체적인 보강 대상입니다.
   - 제안: 두꺼운 망치 머리와 짧은 자루의 단일 발광 형상. 작은 크기에서도 외곽선이 읽히도록 설계합니다.
   - **신규 제안 경로:** `ArtSource/vfx/judgment_hammer/` → `Assets/_Game/Resources/Vfx/Meshes/judgment_hammer.fbx`.
   - `Assets/_Game/Resources/Vfx/effects.json`에 전용 효과를 추가하고 `Data/presentation.json`의 `pr_c_hammer.impact_vfx`에 연결합니다. 공용 `stun_slam`은 교체하지 않습니다.
   - 기존 [VfxLibrary.cs:415](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Presentation/Vfx/VfxLibrary.cs:415) 규약대로 축·스케일·피벗을 구운 단일 메시, 3k–6k 삼각형, 1k 텍스처를 목표로 합니다.

4. **P3 — 키카드: 새 제작보다 현재 배치 가독성 검수**
   - [key_item.tripo:1](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Resources/Art/Props/Common/key_item.tripo:1)은 **기존 gate_keycard가 이미 설치되었음**을 기록합니다. 미통합 자산으로 다시 계산하면 안 됩니다.
   - 기존 원본 `ArtSource/props/gate_keycard/tripo/`와 `Resources/Art/Props/Common/key_item.fbx`를 재사용합니다.
   - [DungeonWorld.cs:110](C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/Assets/_Game/Scripts/Runtime/World/DungeonWorld.cs:110)의 높이·벽 배치에서 카드 면, 청록 테두리, 접근 시 축소와 수집을 확인하고 필요한 방향·배치만 조정합니다. 신규 생성 비용은 없습니다.

**부모의 즉시 다음 행동:** 제출된 버섯 작업 결과를 확인하고, 다음 유료 단계의 표시 비용·잔액을 기록한 뒤 retopo부터 파일럿 검수를 진행합니다. 내보내기 다운로드 후 Studio 탭을 닫습니다.

읽기 전용 계획 완료: 두 지정 문서, 관련 코드·자산 기록, B/D 이미지를 확인했습니다. 수정·테스트·Unity·브라우저 실행은 없으며, 이전 259개 통과는 사용자 제공 기준선입니다. 새 자산의 런타임 합격과 실제 Astra High/priority 라우팅은 이 작업에서 검증하지 않았습니다.