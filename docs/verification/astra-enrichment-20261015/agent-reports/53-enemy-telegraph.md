# 53 — Enemy telegraph: 설명과 실제 효과 대조

- 요청 모델/effort: `gpt-6-astra` / `high`.
- 요청 서비스 tier: Fast/priority. 이 세션에 독립적인 모델·effort·서비스 tier 실행 메타데이터가 제공되지 않아 실제 라우팅과 priority 적용은 검증하지 못했다. 설정 변경이나 모델 전환은 하지 않았다.
- 저장소: `C:\Users\User\Desktop\GAME_JRPG\handoff-verify-20261015`.
- 확인한 브랜치: `codex/astra-enrichment-20261015`; HEAD 및 요청 기준: `efdc1517`.
- 방법: 지정된 데이터와 관련 전투/UI 소스만 정적으로 읽었다. 현재 작업 트리의 `BattleEngine.cs`에는 기존 변경이 있으므로 근거는 현재 디스크 내용이다. 테스트·빌드·Unity·브라우저·네트워크·하위 에이전트 실행은 없었다.
- 중복 확인: 기존 `05-enemy-ai.md`를 읽고, 존재하는 01–06 보고서에서 mirror/거울/도플 언급을 확인했으며 중복은 찾지 못했다.
- 결과: 구체적 불일치 **1건**. 게임 파일은 수정하지 않았다.

## F1 [P2] 도플갱어의 일반 마법 공격을 ‘반격/기술 되돌리기’로 안내한다

**수정 위치:** `Assets/_Game/Resources/Data/skills.json:3350-3351` (`id: sk_e_mirror_strike`, :3349).

현재 `display_name`은 `거울 반격`, `description`은 `상대의 기술을 비춰 되받아칩니다.`다. 그러나 같은 레코드의 :3352-3359는 Damage / Magic / Enemy / Single / None, power 1.5, 1회 타격, MP 6이다. 상대가 직전에 쓴 기술이나 받은 피해를 복사·반사하는 동작이 아니라 도플갱어 자신의 마력으로 계산하는 일반 공격이다.

근거:

- `Assets/_Game/Scripts/Logic/Data/GameData.cs:12-16`: 위 숫자 필드의 enum 의미. 기존 이름/설명 필드는 :115-116에 정의되어 있다.
- `Assets/_Game/Resources/Data/enemies.json:9322-9328,9366-9379`: 실제 적 도플갱어는 MP 60의 caster이며, 해당 스킬은 양수 가중치 2로 편성되어 있다.
- `Assets/_Game/Scripts/Logic/Battle/EnemyAI.cs:80-98,103-124`: 자원과 가중치로 스킬을 골라 자신의 행동으로 실행한다. 이 스킬을 고르기 위해 플레이어가 먼저 공격하거나 기술을 쓸 필요가 없다.
- `Assets/_Game/Scripts/Logic/Battle/BattleEngine.cs:1067-1098`: 선택한 스킬과 대상을 사용해 피해를 계산하고 적용한다. `Assets/_Game/Scripts/Logic/Battle/DamageFormula.cs:68-74,153-162`에서 이 스킬의 피해는 시전자 마력과 대상 저항을 사용하며 속성은 None이다.
- `Assets/_Game/Scripts/UI/Battle/BattleHUD.Cards.cs:325-327,361-366`: 적 행동 예고가 `DisplayName`을 그대로 출력한다. 따라서 설명 원문을 별도 UI에서 읽지 않더라도 실제 전투 예고에 `거울 반격 → 대상`이 표시된다. 이 감사에서는 적의 description 원문이 별도 화면에 표시된다고 주장하지 않는다.

**도달 경로 / 재현 절차(실행하지 않음):** `Assets/_Game/Resources/Data/dungeon.json:10370`의 `guild_street_2`에서 :10467-10471에 정의된 nightmare/doppelganger/doppelganger/void_eye 조우에 진입한다. 도플갱어가 `sk_e_mirror_strike`를 선택한 라운드의 예고를 확인한다. 파티가 방어·회복만 해도 도플갱어의 행동 차례에 해당 공격은 실행될 수 있다. 이는 플레이어 기술 사용에 반응하는 반격이 아니다.

**영향:** 정상 조우의 행동 예고가 반격 조건이나 기술 반사를 암시하므로, 플레이어가 공격을 삼가면 해당 공격을 피할 수 있다고 오해하게 한다. 실제 단일 마법 피해를 예측하는 데 필요한 표현도 빠져 있다.

**정확한 데이터 수정 제안(미적용):** 위 레코드의 두 문자열만 다음으로 바꾼다.

```json
"display_name": "거울 마탄",
"description": "거울에 모은 마력으로 적 하나에게 무속성 마법 피해를 1회 줍니다."
```

`id`, 효과·범위·위력·비용·presentation은 유지한다. 기존 스키마 안에서 예고 이름과 설명을 실제 동작에 맞추는 변경이며 새 에셋이나 반사 기능 구현은 필요 없다.

## 수락 확인

- [x] 요청 브랜치와 기준 커밋 확인.
- [x] 실제 적 편성, 정상 던전 조우, AI 선택, 피해 계산, 예고 표시까지 소스 근거 확보.
- [x] 정확한 위치와 재현 절차 및 기존 필드의 대체 문구 제시.
- [x] 발견 1건으로 제한; 이 보고서 외 파일 쓰기 없음.
- [x] 실행 검증 및 실제 priority 적용을 검증했다고 주장하지 않음. 통합과 실행 검증은 메인 조정자 담당.