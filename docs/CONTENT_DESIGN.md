# 심연의 미궁 — Content Design Bible

게임 콘텐츠의 수치와 한국어 문구 설계 문서입니다. Unity 런타임은 `Assets/_Game/Resources/Data/*.json`을 읽습니다. 수치를 조정할 때는 JSON과 이 문서를 함께 갱신합니다. 아래의 기존 Godot 리소스·필드 표기는 원작 콘텐츠 스키마를 설명하며, 실행 파일이나 현재 프로젝트 경로를 뜻하지 않습니다.

## Unity 3D 구현

- 엔진: Unity 6000.3.25f1, URP. 3D 모델 원본과 생성기는 `Blender/`, FBX는 `Assets/_Game/Resources/Art/`입니다. 제작 규약은 `Blender/README.md`를 따릅니다.
- 데이터 스키마: `Assets/_Game/Scripts/Logic/Data/GameData.cs`. 표 이름은 `heroes`, `enemies`, `skills`, `statuses`, `items`, `equipment`, `dungeon`, `quests`, `presentation`, `text_ko`입니다.
- 전투: `Logic/Battle/BattleEngine.cs`와 `BattleEngine.Commands.cs`. `Start`, `Submit`, `Advance`가 순서가 보존된 `BattleEvent`를 반환합니다. 연출은 이벤트에 저장된 HP·MP·상태 스냅샷을 재생하며, 이미 다음 턴까지 진행된 엔진 값을 중간 프레임에 읽지 않습니다.
- 캠페인: `Logic/Game/`의 `GameState`, `PartyStats`, `TownServices`, `QuestLog`, `GameFlow`, `SaveCodec`.
- 탐험: `Logic/Dungeon/DungeonGrid.cs`, `DungeonRun.cs`. 이동·FOE·상자·열쇠·문·함정·층 전환·전투 결과 반영을 소유합니다. 보상은 `DungeonRun.ResolveBattle`에서 한 번만 지급합니다.
- 저장: 자동 저장과 수동 3슬롯은 `Application.persistentDataPath/campaign/`에 JSON으로 저장합니다. 임시 파일을 완전히 기록한 뒤 교체하며, 미해결 전투와 현재 층·위치·방향도 복원합니다.
- 실제 실행 확인: Lv.1 네 동료가 B1F에 진입하고 무작위 전투를 저장·복원한 뒤, 9회 명령과 15회 피해 이벤트로 승리하고 마을로 돌아왔습니다. 이 확인은 순수 C# 캠페인 실행 결과이며 Unity 화면·빌드 검증을 대신하지 않습니다.
- Unity 에디터에서도 실제 B1F 이동으로 자연 발생 전투를 시작해 3라운드 자동 전투 승리와 탐험 복귀·보상 반영을 확인했습니다. 상점에서 사슬 갑옷 1개 구매(214→144G), 장비 해제·재장착(가방 1→2→1), 회복약 대상 선택(검사 HP142→165, 수량 4→3), 음량 0.5의 파일 저장·읽기를 실행했습니다. Windows 네이티브 입력과 전체 캠페인 검증은 별도입니다.
- 전투 기본 카메라와 설명창은 네 동료의 3D 모델을 가리지 않도록 배치했습니다. 명령 설명은 상단의 마스크·스크롤 영역이며, 긴 스킬 설명을 자르지 않습니다. 실제 화면은 `Store/screenshots/battle-normal-editor.png`입니다.


**Conventions**
- Enum values used below (existing `SkillData`): Element `NONE=0 SLASH=1 BLUNT=2 PIERCE=3 FIRE=4 ICE=5 THUNDER=6 DARK=7 HOLY=8`; Kind `DAMAGE=0 HEAL=1 BUFF=2 DEBUFF=3 REVIVE=4 CLEANSE=5`; Scaling `ATK=0 MAG=1`; Target `ENEMY=0 ALLY=1 SELF=2` ("ENEMY" means the user's opponents, so an enemy skill with target ENEMY hits the party); Scope `SINGLE=0 ALL=1 RANDOM=2`.
- Status chance and status id are set per skill. Duration and magnitude come from the referenced `StatusEffectData` resource (§4). A skill that needs other numbers points at a variant status resource, for example `defense_up_l`.
- `extra_statuses` use the same `status_chance` as the first status.
- File naming in Unity: each table is `Assets/_Game/Resources/Data/<table>.json`; rows retain the original ids. Runtime DTOs replace the original per-row `.tres` resources.
- Existing ids and Korean names are kept unchanged. Existing resources whose numbers change here: `basic_attack`, `strong_attack`, `stunning_slam`, `double_shot`, `fireball`, `heal`, `holy_light`, `poison_spore`, the 4 statuses, `healing_potion`, and the 16 existing enemies.

---

## 0. Fields this bible assumes (add-only, for T11/T12/T13)

| Resource | Field (type, default) | Used for |
|---|---|---|
| CharacterData | `resistance:int` (default = `defense`), `hp_growth…spd_growth` (D4), `res_growth`, `hit:float=0.95`, `evade:float=0.05`, `crit:float=0.05` (**main-approved addition for T12**), `learnset` (D4), `starter_equipment:Dictionary` {weapon, armor, accessory} | §2 |
| EnemyData | `resistance:int` (D3), `evade:float=0.05`, `hit:float=0.95` (**evade/hit are main-approved additions for T12**), `skill_weights:Array[int]` (D3), `break_shield:int=0`, `gold_reward:int=0`, `drops:Array[Dictionary]`, `tint:Color=WHITE`, `scale_mult:float=1.0`, `summons:Array[StringName]=[]`, `summon_limit:int=0` | §7 |
| EnemyData.phases dict | keys `hp_below, skills, weights (optional, default 1 each), actions_per_turn, line, summon` | §7.4 |
| EnemyData.gimmicks | `cc_immune` (stun/sleep/freeze never land), `cc_resist` (the chance for those three is halved), `dot_resist` (poison/burn/bleed tick ×0.25) | §7 |
| StatusEffectData | `tint:Color` (rig tint while the status is active). BARRIER uses `magnitude` × own max HP as the absorb amount (`absorb_amount` = 0 means "use magnitude"). MANA_SHIELD / INVINCIBLE exist in the enum but this bible uses neither. | §4 |
| ItemData | `status_id:StringName` (BUFF items), `power:float` (REVIVE ratio), `value:int` (other types) — matches the in-flight T12 schema | §5 |
| DungeonFloorData | `encounter_rate`, `min_encounter_steps` (= "grace" below), `foes`, `treasures`, `lore_stones`, `boss_group`, `boss_pre_text`/`boss_post_text` (lines joined by newline), `key_name:String` (new) | §8 |

---

## 1. Core formulas

### 1.1 XP
- `xp_to_next(L) = round(25 × L^1.6) + 25`, level cap 40. This is D4 unchanged.
- Every living party member gets the full XP total of the battle; KO'd members get 0. Difficulty XP multiplier: easy ×1.2, normal ×1, hard ×1.1.

| L | to next | cumulative to reach L |
|---|---|---|
| 1 | 50 | 0 |
| 4 | 255 | 321 |
| 7 | 587 | 1,394 |
| 10 | 1,020 | 3,568 |
| 14 | 1,730 | 8,668 |
| 19 | 2,804 | 19,388 |
| 23 | 3,798 | 32,060 |
| 28 | 5,194 | 53,777 |
| 32 | 6,425 | 76,368 |
| 36 | 7,752 | 104,030 |
| 40 | — | 137,139 |

- Stats: `stat(L) = round(base + growth × (L − 1))`. Leveling up raises current HP/MP by the gained maximum (it is not a full heal).

### 1.2 Damage pipeline (`Logic/Battle/DamageFormula.cs`)
Damage is computed once per hit, in this order:
1. `type` = physical when `scaling_stat = ATK`, magical when `MAG`.
2. `off` = effective ATK (physical) or effective MAG (magical). Statuses apply here: ATTACK_UP/ATTACK_DOWN and MAGIC_UP multiply.
3. `def` = effective DEF (physical) or effective RES (magical), then `def × (1 − defense_ignore)`. DEFENSE_UP and DEFENSE_DOWN scale both DEF and RES.
4. `base = max(1, off × power + flat − def × 0.55)`, then × `randf(0.92, 1.08)`.
5. **Hit check** (physical only): `p = clamp(actor.hit × (0.6 if BLIND) − target.evade, 0.25, 1.0)`. A miss deals 0 and gives no TP. Magical damage, HEAL, BUFF, REVIVE and CLEANSE never miss.
6. **Crit** (physical only): `p = actor.crit + skill.crit_bonus`, ×1.5 (the existing `crit_multiplier`).
7. **Element**: the skill's element is in target.weaknesses → ×1.5 and the "약점!" popup; in target.resistances → ×0.5 and the "내성" popup. Heroes take ×0.5 from an element listed in any equipped item's `element_resists` (these do not stack). NONE is ×1.
8. **BROKEN** target ×1.5.
9. `bonus_vs_status`: when the target has a status with that id → × `bonus_vs_status_mult`.
10. **FREEZE**: a physical hit on a frozen target is ×1.3 and removes FREEZE.
11. **Guard** ×0.5.
12. **BARRIER** absorbs damage first. Then the result is rounded, minimum 1.

- **Multi-hit**: `hit_count` hits, each fully computed. With **RANDOM** scope each hit picks a random living opponent. With **ALL** scope every opponent takes `hit_count` hits.
- **Healing**: `MAG × power × randf(0.95, 1.05)`. The target's BURN halves healing received. REVIVE sets HP to `max_hp × power`.
- **Status landing**: roll `status_chance` per target, once per skill use (not per hit), only when at least one hit connected (DAMAGE) or always (BUFF/DEBUFF). `cc_immune`/`cc_resist` apply to STUN, SLEEP and FREEZE.
- **Turn order**: each round, sort by effective speed (SLOW ×0.75, SPEED_UP ×(1+m)); ties go to the party first. `actions_per_turn` gives extra consecutive actions in the same slot.

### 1.3 Break (D3)
- `break_shield` N > 0 shows N pips. Each **hit** whose element is a weakness removes 1 pip, so multi-hit skills break faster by design.
- At 0 the unit is **BROKEN**: it loses its next action, and takes ×1.5 damage until the end of that skipped turn. Then the shield refills to N. Each break gives every living party member +10 TP.
- Shields: normals 2–5, elites 3–7, bosses 4–6 (see §7).

### 1.4 TP (D3)
- Range 0–100. +8 per action that dealt damage (once per action), +12 per action that damaged this unit, +20 when an ally falls, +10 per break (§1.3). Reset after battle.
- Ultimates cost 100 TP and 0 MP. Silence does not block them.

### 1.5 Difficulty (D3, applied in EnemyStats.build)
| | easy | normal | hard |
|---|---|---|---|
| enemy HP | ×0.75 | ×1 | ×1.35 (bosses ×1.2) |
| enemy ATK & MAG | ×0.8 | ×1 | ×1.2 (bosses ×1.1) |
| XP | ×1.2 | ×1 | ×1.1 |
| gold | ×1 | ×1 | ×1.2 |
| `basic` AI acts `aggressive` | — | — | 40 % |
| gold lost on defeat | 0 % | 50 % | 50 % |

T28: the hard boss values are per-kind overrides (`EnemyStats.DIFFICULTY_KIND_SCALES`, kind `boss` = `is_boss`); every other enemy, including boss summons, uses the plain hard column. Easy and normal have no overrides.

### 1.6 Flee
- Normal flee: `clamp(0.55 + (party_avg_spd − enemy_avg_spd) × 0.02, 0.15, 0.90)` (existing).
- `smoke_bomb` always succeeds in **normal and FOE battles only**.
- **Boss and event (`E`) battles can never be fled, including with `smoke_bomb`.** The item must be disabled in those battles and is not consumed by a rejected use.
- The ordinary flee command is disabled in FOE battles; use `smoke_bomb` to escape a FOE.

---

## 2. Heroes

### 2.1 Base stats (Lv 1) and growth per level
| id | 이름 | role | HP | MP | ATK | MAG | DEF | RES | SPD | hit | evade | crit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| warrior | 검사 | 전위 탱커·물리 딜러 (참격/타격) | 165 | 18 | 22 | 8 | 17 | 10 | 10 | 0.95 | 0.03 | 0.05 |
| mage | 마법사 | 후위 원소 딜러 (화염/빙결/뇌전/암흑) | 105 | 38 | 11 | 25 | 9 | 16 | 12 | 0.95 | 0.05 | 0.03 |
| archer | 궁수 | 후위 정밀 사격·상태이상 (관통) | 125 | 24 | 19 | 10 | 11 | 11 | 22 | 1.00 | 0.10 | 0.10 |
| cleric | 성직자 | 후위 회복·지원·신성 | 120 | 40 | 10 | 20 | 12 | 18 | 11 | 0.95 | 0.05 | 0.04 |

| id | hp_growth | mp_growth | atk_growth | mag_growth | def_growth | res_growth | spd_growth |
|---|---|---|---|---|---|---|---|
| warrior | 14.0 | 1.6 | 2.6 | 0.6 | 2.0 | 1.2 | 0.7 |
| mage | 8.5 | 4.2 | 0.9 | 3.0 | 1.1 | 2.2 | 0.9 |
| archer | 10.5 | 2.2 | 2.4 | 0.8 | 1.4 | 1.4 | 1.3 |
| cleric | 10.0 | 4.0 | 1.0 | 2.5 | 1.5 | 2.4 | 0.8 |

Reference values with the expected gear (§12): Lv10 T2 warrior HP 311 / ATK 59 / DEF 48, mage MAG 66 / MP 86. Lv36 T5 warrior HP 755 / ATK 169, mage MAG 186 / MP 225, archer ATK 153 / SPD 68, cleric MAG 156 / MP 220.

### 2.2 Starter equipment
| hero | weapon | armor | accessory |
|---|---|---|---|
| warrior | sword_bronze | armor_chain | — |
| mage | staff_oak | robe_cloth | — |
| archer | bow_short | garb_leather | — |
| cleric | mace_wood | robe_cloth | — |

New games start with 150 gold, 3 `healing_potion` and 1 `return_stone`.

### 2.3 Learnsets
`basic_attack` is always available and is not counted. The existing `skills` arrays stay as the Lv1 entries. Each hero has 8 skills plus 1 ultimate.

| Lv | warrior 검사 | mage 마법사 | archer 궁수 | cleric 성직자 |
|---|---|---|---|---|
| 1 | strong_attack | fireball, heal | double_shot | heal, holy_light |
| 3 | stunning_slam | | sk_poison_arrow | sk_cure |
| 4 | | sk_ice_lance | | |
| 6 | sk_cleave | | sk_hunter_mark | sk_heal_all |
| 8 | **ult_heaven_rend** | **ult_meteor** | **ult_starfall_volley** | **ult_seraph_hymn** |
| 9 | | sk_chain_spark | | |
| 10 | sk_provoke | | sk_weak_point | sk_revive |
| 12 | | sk_flame_wave | | |
| 14 | | | sk_flame_arrow | sk_greater_heal |
| 15 | sk_bleed_edge | | | |
| 17 | | sk_frost_nova | | |
| 18 | | | sk_arrow_rain | |
| 20 | sk_iron_wall | | | sk_sanctuary |
| 22 | | sk_thunder_storm | | |
| 24 | | | sk_sleep_arrow | |
| 26 | sk_war_cry | | | |
| 27 | | | | sk_divine_judgment |
| 28 | | sk_void_lance | | |
| 32 | | | sk_piercing_gale | |
| 34 | sk_titan_crash | | | |

Design intent:
- Ultimates arrive at Lv8, before the first boss.
- Thunder arrives at Lv9, before the frost biome (Lv11).
- Ice AoE arrives at Lv17, before the ember biome.
- Holy AoE arrives at Lv27, before the crypt.
- Revive arrives at Lv10.

---

## 3. Skills

### 3.1 Hero skills (36)
Columns: kind / scale / target / scope / element / power × hits / MP / TP / status (chance) / crit+ / def ign / bonus vs status / tier / presentation preset.

| id | 이름 | 설명 | kind | sc | tgt | scope | elem | pow×hit | MP | TP | status (chance) | crit+ | ign | bonus | tier | pres |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| basic_attack | 기본 공격 | MP를 소모하지 않는 기본 공격입니다. | DAMAGE | ATK | ENEMY | SINGLE | NONE | 1.0×1 | 0 | 0 | — | 0 | 0 | — | 1 | (none, as today) |
| strong_attack | 강타 | 힘껏 베어 방어를 일부 무시합니다. | DAMAGE | ATK | ENEMY | SINGLE | SLASH | 1.7×1 | 4 | 0 | — | 0 | 0.15 | — | 2 | strong_attack |
| stunning_slam | 기절 강타 | 방패로 내리쳐 기절시킬 수 있습니다. | DAMAGE | ATK | ENEMY | SINGLE | BLUNT | 1.0×1 | 6 | 0 | stun (0.35) | 0 | 0 | — | 2 | stunning_slam |
| sk_cleave | 가로베기 | 검을 크게 휘둘러 적 전체를 벱니다. | DAMAGE | ATK | ENEMY | ALL | SLASH | 0.75×1 | 8 | 0 | — | 0 | 0 | — | 2 | pr_slash_all |
| sk_provoke | 도발의 포효 | 적의 공격을 자신에게 끌어들이고 방어를 높입니다. | BUFF | ATK | SELF | SINGLE | NONE | 0 | 5 | 0 | provoke (1.0) + extra defense_up | 0 | 0 | — | 2 | pr_buff_self |
| sk_bleed_edge | 혈흔 베기 | 깊게 베어 출혈을 일으킵니다. | DAMAGE | ATK | ENEMY | SINGLE | SLASH | 1.15×1 | 7 | 0 | bleed (0.8) | 0 | 0 | — | 2 | pr_slash_bleed |
| sk_iron_wall | 철벽 | 아군 전체의 방어력을 크게 높입니다. | BUFF | ATK | ALLY | ALL | NONE | 0 | 12 | 0 | defense_up_l (1.0) | 0 | 0 | — | 2 | pr_buff_party |
| sk_war_cry | 투지의 함성 | 아군 전체의 공격력과 속도를 높입니다. | BUFF | ATK | ALLY | ALL | NONE | 0 | 14 | 0 | attack_up (1.0) + extra speed_up | 0 | 0 | — | 2 | pr_buff_party |
| sk_titan_crash | 대지 분쇄 | 땅을 내리쳐 적 전체를 강타하고 둔화시킵니다. | DAMAGE | ATK | ENEMY | ALL | BLUNT | 1.25×1 | 20 | 0 | slow (0.3) | 0 | 0 | — | 2 | pr_blunt_all |
| ult_heaven_rend | [오의] 천열참 | 하늘을 가르는 일격. 방어를 절반 무시합니다. | DAMAGE | ATK | ENEMY | SINGLE | SLASH | 4.0×1 | 0 | 100 | — | 0.25 | 0.5 | bleed ×1.3 | 3 | pr_ult_warrior |
| fireball | 파이어볼 | 적 하나를 화염으로 태우고 화상을 입힐 수 있습니다. | DAMAGE | MAG | ENEMY | SINGLE | FIRE | 1.5×1 | 6 | 0 | burn (0.3) | 0 | 0 | — | 2 | fireball |
| heal | 힐 | 아군 한 명의 HP를 회복합니다. | HEAL | MAG | ALLY | SINGLE | NONE | 1.2 | 5 | 0 | — | 0 | 0 | — | 2 | heal |
| sk_ice_lance | 아이스 랜스 | 얼음 창으로 꿰뚫고 둔화시킬 수 있습니다. | DAMAGE | MAG | ENEMY | SINGLE | ICE | 1.45×1 | 6 | 0 | slow (0.4) | 0 | 0 | — | 2 | pr_ice |
| sk_chain_spark | 체인 스파크 | 무작위 적에게 번개를 네 번 떨어뜨립니다. | DAMAGE | MAG | ENEMY | RANDOM | THUNDER | 0.55×4 | 10 | 0 | — | 0 | 0 | — | 2 | pr_thunder |
| sk_flame_wave | 플레임 웨이브 | 불길의 파도로 적 전체를 태웁니다. | DAMAGE | MAG | ENEMY | ALL | FIRE | 0.95×1 | 12 | 0 | burn (0.15) | 0 | 0 | — | 2 | pr_fire_all |
| sk_frost_nova | 프로스트 노바 | 냉기를 폭발시켜 적 전체를 얼립니다. | DAMAGE | MAG | ENEMY | ALL | ICE | 0.95×1 | 14 | 0 | freeze (0.15) | 0 | 0 | — | 2 | pr_ice_all |
| sk_thunder_storm | 썬더 스톰 | 뇌운을 불러 적 전체를 내리치고 침묵시킬 수 있습니다. | DAMAGE | MAG | ENEMY | ALL | THUNDER | 1.2×1 | 20 | 0 | silence (0.15) | 0 | 0 | — | 2 | pr_thunder_all |
| sk_void_lance | 보이드 랜스 | 공허의 창으로 마법 방어를 꿰뚫습니다. | DAMAGE | MAG | ENEMY | SINGLE | DARK | 2.4×1 | 18 | 0 | — | 0 | 0.3 | — | 2 | pr_dark |
| ult_meteor | [오의] 메테오 | 운석을 떨어뜨려 적 전체를 세 번 강타합니다. | DAMAGE | MAG | ENEMY | ALL | FIRE | 1.2×3 | 0 | 100 | burn (0.6) | 0 | 0 | — | 3 | pr_ult_mage |
| double_shot | 더블 샷 | 적 하나에게 빠르게 두 발을 쏩니다. | DAMAGE | ATK | ENEMY | SINGLE | PIERCE | 0.72×2 | 4 | 0 | — | 0 | 0 | — | 2 | double_shot |
| sk_poison_arrow | 독화살 | 독을 바른 화살로 중독시킵니다. | DAMAGE | ATK | ENEMY | SINGLE | PIERCE | 0.9×1 | 5 | 0 | poison (0.9) | 0 | 0 | — | 2 | pr_arrow_poison |
| sk_hunter_mark | 사냥꾼의 표식 | 표식을 새겨 대상의 방어력을 낮춥니다. | DEBUFF | ATK | ENEMY | SINGLE | NONE | 0 | 5 | 0 | defense_down (1.0) | 0 | 0 | — | 2 | pr_debuff |
| sk_weak_point | 약점 저격 | 급소를 노려 치명타 확률이 크게 오릅니다. | DAMAGE | ATK | ENEMY | SINGLE | PIERCE | 1.9×1 | 8 | 0 | — | 0.4 | 0 | — | 2 | pr_arrow_snipe |
| sk_flame_arrow | 화염 화살 | 불붙은 화살로 화상을 입힐 수 있습니다. | DAMAGE | ATK | ENEMY | SINGLE | FIRE | 1.35×1 | 8 | 0 | burn (0.4) | 0 | 0 | — | 2 | pr_arrow_fire |
| sk_arrow_rain | 화살비 | 적 전체에 화살을 퍼붓습니다. 중독된 적에게 1.5배. | DAMAGE | ATK | ENEMY | ALL | PIERCE | 0.7×1 | 10 | 0 | — | 0 | 0 | poison ×1.5 | 2 | pr_arrow_all |
| sk_sleep_arrow | 수면 화살 | 약을 바른 화살로 잠재웁니다. | DAMAGE | ATK | ENEMY | SINGLE | PIERCE | 0.6×1 | 9 | 0 | sleep (0.6) | 0 | 0 | — | 2 | pr_arrow_sleep |
| sk_piercing_gale | 관통 질풍 | 바람을 두른 화살이 적 전체의 방어를 꿰뚫습니다. | DAMAGE | ATK | ENEMY | ALL | PIERCE | 1.1×1 | 18 | 0 | — | 0 | 0.3 | — | 2 | pr_arrow_all |
| ult_starfall_volley | [오의] 유성연사 | 유성처럼 화살 여덟 발을 무작위로 쏟아붓습니다. | DAMAGE | ATK | ENEMY | RANDOM | PIERCE | 0.7×8 | 0 | 100 | — | 0.1 | 0 | — | 3 | pr_ult_archer |
| holy_light | 성스러운 빛 | 신성한 빛으로 적 하나에게 마법 피해를 줍니다. | DAMAGE | MAG | ENEMY | SINGLE | HOLY | 1.4×1 | 6 | 0 | — | 0 | 0 | — | 2 | holy_light |
| sk_cure | 정화 | 아군 한 명의 해로운 상태이상을 모두 없앱니다. | CLEANSE | MAG | ALLY | SINGLE | NONE | 0 | 4 | 0 | — | 0 | 0 | — | 2 | pr_buff_party |
| sk_heal_all | 치유의 기도 | 아군 전체의 HP를 회복합니다. | HEAL | MAG | ALLY | ALL | NONE | 0.75 | 12 | 0 | — | 0 | 0 | — | 2 | pr_heal_all |
| sk_revive | 소생 | 쓰러진 아군을 HP 35%로 일으킵니다. | REVIVE | MAG | ALLY | SINGLE | NONE | 0.35 | 16 | 0 | — | 0 | 0 | — | 2 | pr_revive |
| sk_greater_heal | 대치유 | 아군 한 명의 HP를 크게 회복합니다. | HEAL | MAG | ALLY | SINGLE | NONE | 2.4 | 12 | 0 | — | 0 | 0 | — | 2 | heal |
| sk_sanctuary | 성역의 가호 | 아군 전체에 재생과 보호막을 겁니다. | BUFF | MAG | ALLY | ALL | NONE | 0 | 20 | 0 | regen (1.0) + extra barrier | 0 | 0 | — | 2 | pr_buff_party |
| sk_divine_judgment | 신성 심판 | 하늘의 빛으로 적 전체를 심판합니다. | DAMAGE | MAG | ENEMY | ALL | HOLY | 1.15×1 | 18 | 0 | — | 0 | 0 | — | 2 | pr_holy_all |
| ult_seraph_hymn | [오의] 천사의 찬가 | 아군 전체를 크게 회복하고 재생을 부여합니다. | HEAL | MAG | ALLY | ALL | NONE | 2.0 | 0 | 100 | regen (1.0) | 0 | 0 | — | 3 | pr_ult_cleric |

Notes:
- CLEANSE removes every negative status: poison, poison_strong, stun, burn, bleed, slow, freeze, silence, attack_down, defense_down, sleep, blind.
- Ultimate cut-ins use `CharacterData.cut_in`.

### 3.2 Enemy skills (33)
Authoring defaults for columns omitted from this table: `tp_cost = 0`, `crit_bonus = 0.0`, `defense_ignore = 0.0`, `tier = 2`, `flat_power = 0.0` (if the field exists), `extra_statuses = []` unless explicitly listed. A `—` status means `status_effect = null` and `status_chance = 0.0`; a `—` bonus means `bonus_vs_status = &""` and `bonus_vs_status_mult = 1.0`. A scalar `pow` without `×hits` means `hit_count = 1`. Names and descriptions in both skill tables are literal resource strings, not examples. Reused hero skills reference the same resource; they do not create differently named or differently numbered enemy variants.
| id | 이름 | 설명 | kind | sc | tgt | scope | elem | pow×hit | MP | status (chance) | bonus | pres | used by |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| poison_spore | 독 포자 | 독 포자를 흩뿌려 전체를 중독시킵니다. | DAMAGE | MAG | ENEMY | **ALL** | NONE | 0.45×1 | 3 | poison (0.4) | — | poison_spore | mushroom, elite_mushroom |
| sk_acid_spit | 산성 침 | 산성 침을 뱉어 방어력을 낮춥니다. | DAMAGE | ATK | ENEMY | SINGLE | NONE | 0.9×1 | 0 | defense_down (0.4) | — | poison_spore | slime |
| sk_root_bind | 뿌리 속박 | 뿌리로 휘감아 둔화시킵니다. | DAMAGE | ATK | ENEMY | SINGLE | NONE | 0.7×1 | 0 | slow (0.6) | — | pr_root | sprout, forest_guardian |
| sk_screech | 초음파 | 날카로운 초음파로 전체를 실명시킵니다. | DEBUFF | MAG | ENEMY | ALL | NONE | 0 | 0 | blind (0.35) | — | pr_debuff | bat, elite_bat |
| sk_lullaby | 수면의 빛 | 몽롱한 빛으로 전체를 잠재웁니다. | DEBUFF | MAG | ENEMY | ALL | NONE | 0 | 0 | sleep (0.25) | — | pr_debuff | jellyfish |
| sk_harden | 굳히기 | 몸을 단단히 굳혀 방어력을 크게 높입니다. | BUFF | ATK | SELF | SINGLE | NONE | 0 | 0 | defense_up_l (1.0) | — | pr_buff_self | coral_crab, skeleton, elites |
| sk_ice_shard | 얼음 파편 | 얼음 파편을 날려 얼릴 수 있습니다. | DAMAGE | MAG | ENEMY | SINGLE | ICE | 1.2×1 | 4 | freeze (0.2) | — | pr_ice | penguin_mage |
| sk_blizzard | 눈보라 | 눈보라로 전체를 공격하고 둔화시킵니다. | DAMAGE | MAG | ENEMY | ALL | ICE | 0.65×1 | 8 | slow (0.2) | — | pr_ice_all | penguin_mage |
| sk_twin_bite | 쌍아 물기 | 두 번 물어뜯어 출혈을 일으킵니다. | DAMAGE | ATK | ENEMY | SINGLE | SLASH | 0.65×2 | 0 | bleed (0.3) | — | pr_bite | ice_wolf, elite_ice_wolf |
| sk_sandstorm | 모래 폭풍 | 모래바람으로 전체를 때리고 실명시킵니다. | DAMAGE | ATK | ENEMY | ALL | NONE | 0.45×1 | 0 | blind (0.35) | — | pr_sand | sand_golem, elite_sand_golem |
| sk_rebirth_flame | 재생의 불꽃 | 아군 전체의 상처를 불꽃으로 아물게 합니다. | HEAL | MAG | ALLY | ALL | NONE | 0.55 | 10 | — | — | pr_heal_all | phoenix |
| sk_fire_breath | 화염 브레스 | 불길을 내뿜어 전체를 태웁니다. | DAMAGE | MAG | ENEMY | ALL | FIRE | 0.8×1 | 6 | burn (0.3) | — | pr_breath | fire_drake, elite_fire_drake |
| sk_curse_screech | 저주의 비명 | 소름 끼치는 비명으로 전체를 침묵시킵니다. | DEBUFF | MAG | ENEMY | ALL | NONE | 0 | 0 | silence (0.3) | — | pr_debuff | grave_bat |
| sk_crow_swarm | 까마귀 떼 | 까마귀 떼가 무작위로 네 번 쪼아 댑니다. | DAMAGE | ATK | ENEMY | RANDOM | PIERCE | 0.45×4 | 0 | — | — | pr_arrow_all | scarecrow, elite_scarecrow |
| sk_spirit_fire | 혼불 | 푸른 혼불로 영혼을 태웁니다. | DAMAGE | MAG | ENEMY | SINGLE | DARK | 1.3×1 | 5 | — | — | pr_dark | wisp |
| sk_hex | 저주 | 저주를 걸어 전체의 공격력과 마력을 낮춥니다. | DEBUFF | MAG | ENEMY | ALL | NONE | 0 | 6 | attack_down (0.5) | — | pr_debuff | wisp |
| sk_toxic_cloud | 맹독 구름 | 짙은 독구름으로 전체를 맹독에 빠뜨립니다. | DAMAGE | MAG | ENEMY | ALL | NONE | 0.5×1 | 8 | poison_strong (0.6) | — | poison_spore | elite_mushroom |
| sk_inferno | 인페르노 | 지옥불로 전체를 크게 태웁니다. | DAMAGE | MAG | ENEMY | ALL | FIRE | 1.15×1 | 12 | burn (0.5) | — | pr_fire_all | elite_fire_drake |
| sk_dread_stare | 공포의 눈빛 | 섬뜩한 눈빛으로 한 명을 깊이 잠재웁니다. | DEBUFF | MAG | ENEMY | SINGLE | NONE | 0 | 0 | sleep (0.6) | — | pr_debuff | elite_scarecrow, boss |
| sk_harvest_reap | 수확의 낫 | 거대한 낫으로 전체를 벱니다. 잠든 대상에게 1.5배. | DAMAGE | ATK | ENEMY | ALL | SLASH | 0.95×1 | 0 | — | sleep ×1.5 | pr_slash_all | elite_scarecrow |
| sk_vine_lash | 덩굴 채찍 | 굵은 덩굴로 전체를 후려칩니다. | DAMAGE | ATK | ENEMY | ALL | NONE | 0.6×1 | 0 | — | — | pr_root | forest_guardian |
| sk_photosynthesis | 광합성 | 빛을 받아 매 턴 HP를 재생합니다. | BUFF | MAG | SELF | SINGLE | NONE | 0 | 0 | regen (1.0) | — | pr_buff_self | forest_guardian |
| sk_tentacle_crush | 촉수 강타 | 거대한 촉수로 내리칩니다. 빙결된 대상에게 1.5배. | DAMAGE | ATK | ENEMY | SINGLE | BLUNT | 1.4×1 | 0 | — | freeze ×1.5 | pr_heavy_enemy | frost_kraken |
| sk_freezing_tide | 빙결의 해류 | 얼어붙는 해류로 전체를 덮칩니다. | DAMAGE | MAG | ENEMY | ALL | ICE | 0.75×1 | 0 | freeze (0.25) | — | pr_ice_all | frost_kraken |
| sk_ink_cloud | 먹물 분사 | 먹물을 뿜어 전체를 실명시킵니다. | DEBUFF | MAG | ENEMY | ALL | NONE | 0 | 0 | blind (0.5) | — | pr_debuff | frost_kraken |
| sk_riddle_silence | 침묵의 수수께끼 | 풀 수 없는 수수께끼로 전체를 침묵시킵니다. | DEBUFF | MAG | ENEMY | ALL | NONE | 0 | 0 | silence (0.45) | — | pr_debuff | flame_sphinx |
| sk_solar_flare | 태양 섬광 | 작열하는 섬광으로 전체를 태웁니다. | DAMAGE | MAG | ENEMY | ALL | FIRE | 0.9×1 | 0 | burn (0.35) | — | pr_fire_all | flame_sphinx |
| sk_sun_aegis | 태양의 가호 | 태양의 힘으로 마력과 방어력을 높입니다. | BUFF | MAG | SELF | SINGLE | NONE | 0 | 0 | magic_up (1.0) + extra defense_up | — | pr_buff_self | flame_sphinx |
| sk_sun_judgment | 태양의 심판 | 태양을 떨어뜨려 전체에 막대한 화염 피해. | DAMAGE | MAG | ENEMY | ALL | FIRE | 1.5×1 | 0 | — | — | pr_breath | flame_sphinx |
| sk_abyss_bolt | 심연의 화살 | 심연의 어둠을 응축해 한 명을 꿰뚫습니다. | DAMAGE | MAG | ENEMY | SINGLE | DARK | 1.5×1 | 0 | — | — | pr_dark | boss |
| sk_abyss_wave | 심연의 파동 | 어둠의 파동으로 전체를 덮고 힘을 빼앗습니다. | DAMAGE | MAG | ENEMY | ALL | DARK | 0.85×1 | 0 | attack_down (0.3) | — | pr_dark_all | boss |
| sk_abyss_wall | 심연의 장벽 | 어둠의 장벽을 둘러 피해를 흡수합니다. | BUFF | MAG | SELF | SINGLE | NONE | 0 | 0 | barrier_abyss (1.0) + extra defense_up | — | pr_buff_self | boss |
| sk_soul_reap | 영혼 수확 | 영혼을 거두는 낫질. 잠든 대상에게 1.5배. | DAMAGE | MAG | ENEMY | ALL | DARK | 1.2×1 | 0 | — | sleep ×1.5 | pr_dark_all | boss |

Enemies also reuse these hero skills: `basic_attack` (all), `fireball` (magma_slime), `strong_attack` (forest_guardian), `sk_bleed_edge` (elite_bat, elite_skeleton, flame_sphinx), `sk_war_cry` (elite_ice_wolf), `sk_titan_crash` (elite_coral_crab, elite_sand_golem), `sk_cleave` (elite_skeleton).

Total: 36 hero skills + 33 enemy-only skills = 69 skill resources. That is above the ~45–55 target, because 4 heroes × 9 skills already fill 36. Every enemy hook in §7 needs its own enemy skill.

### 3.3 Presentation presets (`data/presentation/<id>.tres`)
Existing files stay unchanged: `attack_party, attack_enemy, strong_attack, stunning_slam, double_shot, fireball, heal, holy_light, poison_spore`. Only existing VFX keys are used: `slash critical impact fire heal buff debuff smoke magic_circle spark flame ring`. Approaches: `none / lunge / dash_to_target`. Actions: `attack / cast / shoot`. `sfx_*` stay empty until T19.

| preset | tier | actor_action | approach | charge_vfx | travel_vfx | impact_vfx | hit_interval | hit_stop | shake | screen_flash | light_color |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pr_slash_all | 2 | attack | lunge | — | — | slash | 0.09 | 0.05 | 0.40 | false | (0.62, 0.84, 1.0) |
| pr_slash_bleed | 2 | attack | dash_to_target | — | — | slash | 0.09 | 0.06 | 0.35 | false | (1.0, 0.35, 0.35) |
| pr_blunt_all | 2 | attack | dash_to_target | — | — | impact | 0.09 | 0.07 | 0.55 | false | (1.0, 0.71, 0.28) |
| pr_buff_self | 2 | cast | none | magic_circle | — | buff | 0.09 | 0.0 | 0.0 | false | (1.0, 0.82, 0.35) |
| pr_buff_party | 2 | cast | none | magic_circle | — | buff | 0.09 | 0.0 | 0.0 | false | (1.0, 0.88, 0.45) |
| pr_debuff | 2 | cast | none | magic_circle | — | debuff | 0.09 | 0.03 | 0.15 | false | (0.72, 0.42, 1.0) |
| pr_ice | 2 | cast | none | magic_circle | spark | ring | 0.09 | 0.06 | 0.35 | false | (0.2, 0.67, 1.0) |
| pr_ice_all | 2 | cast | none | magic_circle | — | ring | 0.09 | 0.06 | 0.45 | false | (0.2, 0.67, 1.0) |
| pr_thunder | 2 | cast | none | magic_circle | spark | spark | 0.07 | 0.05 | 0.35 | false | (1.0, 0.93, 0.27) |
| pr_thunder_all | 2 | cast | none | magic_circle | — | spark | 0.07 | 0.06 | 0.50 | false | (1.0, 0.93, 0.27) |
| pr_fire_all | 2 | cast | none | magic_circle | — | flame | 0.09 | 0.06 | 0.45 | false | (1.0, 0.47, 0.13) |
| pr_dark | 2 | cast | none | magic_circle | smoke | smoke | 0.09 | 0.06 | 0.35 | false | (0.35, 0.12, 0.54) |
| pr_dark_all | 2 | cast | none | magic_circle | — | smoke | 0.09 | 0.07 | 0.50 | false | (0.35, 0.12, 0.54) |
| pr_holy_all | 2 | cast | none | magic_circle | — | ring | 0.09 | 0.06 | 0.40 | false | (1.0, 0.9, 0.54) |
| pr_heal_all | 2 | cast | none | magic_circle | — | heal | 0.09 | 0.0 | 0.0 | false | (0.2, 1.0, 0.53) |
| pr_revive | 2 | cast | none | magic_circle | — | ring | 0.09 | 0.0 | 0.0 | false | (1.0, 0.95, 0.7) |
| pr_arrow_snipe | 2 | shoot | none | — | spark | critical | 0.09 | 0.08 | 0.40 | false | (1.0, 1.0, 1.0) |
| pr_arrow_all | 2 | shoot | none | — | spark | slash | 0.08 | 0.05 | 0.35 | false | (0.62, 0.84, 1.0) |
| pr_arrow_fire | 2 | shoot | none | — | fire | fire | 0.09 | 0.06 | 0.35 | false | (1.0, 0.47, 0.13) |
| pr_arrow_poison | 2 | shoot | none | — | spark | smoke | 0.09 | 0.04 | 0.20 | false | (0.48, 0.82, 0.23) |
| pr_arrow_sleep | 2 | shoot | none | — | spark | smoke | 0.09 | 0.04 | 0.20 | false | (0.55, 0.6, 1.0) |
| pr_root | 2 | attack | lunge | — | — | impact | 0.09 | 0.05 | 0.30 | false | (0.48, 0.82, 0.23) |
| pr_bite | 2 | attack | lunge | — | — | slash | 0.10 | 0.05 | 0.30 | false | (1.0, 0.4, 0.4) |
| pr_sand | 2 | cast | none | — | — | smoke | 0.09 | 0.04 | 0.40 | false | (0.95, 0.8, 0.5) |
| pr_breath | 2 | attack | none | flame | — | fire | 0.09 | 0.07 | 0.50 | false | (1.0, 0.47, 0.13) |
| pr_heavy_enemy | 2 | attack | dash_to_target | — | — | impact | 0.09 | 0.08 | 0.60 | false | (1.0, 0.71, 0.28) |
| pr_ult_warrior | 3 | attack | dash_to_target | magic_circle | — | critical | 0.09 | 0.12 | 0.80 | true | (1.0, 0.95, 0.76) |
| pr_ult_mage | 3 | cast | none | magic_circle | fire | flame | 0.14 | 0.12 | 0.80 | true | (1.0, 0.47, 0.13) |
| pr_ult_archer | 3 | shoot | none | magic_circle | spark | slash | 0.06 | 0.12 | 0.80 | true | (0.75, 0.9, 1.0) |
| pr_ult_cleric | 3 | cast | none | magic_circle | — | heal | 0.09 | 0.0 | 0.0 | true | (1.0, 0.95, 0.7) |

`screen_flash` is true only on ultimates. The existing "화면 깜빡임 줄이기" toggle covers it (rule 9).

---

## 4. Statuses

Effect-type order (append-only): `POISON=0 STUN=1 ATTACK_UP=2 DEFENSE_UP=3 BURN=4 BLEED=5 SLOW=6 FREEZE=7 SILENCE=8 ATTACK_DOWN=9 DEFENSE_DOWN=10 REGEN=11 BARRIER=12 PROVOKE=13 SLEEP=14 BLIND=15 MAGIC_UP=16 SPEED_UP=17`.

**Shared rules**
- Durations count down at the end of the affected unit's own turn.
- Re-applying the same id refreshes the duration; nothing stacks.
- Different ids with the same effect type multiply.
- "Negative" means CLEANSE and `remedy` remove it.

| id | 이름 | effect_type | dur | mag | neg | semantics | tint |
|---|---|---|---|---|---|---|---|
| poison | 중독 | POISON | 3 | 0.06 | ✔ | Loses mag × max HP at the end of its turn. | (0.55, 0.85, 0.3) |
| poison_strong | 맹독 | POISON | 4 | 0.10 | ✔ | Same as poison, stronger. | (0.45, 0.7, 0.2) |
| stun | 기절 | STUN | 1 | 1.0 | ✔ | Skips its next turn. | (1.0, 0.95, 0.5) |
| attack_up | 공격력 상승 | ATTACK_UP | 3 | 0.25 | | ATK × (1 + mag). | (1.0, 0.6, 0.4) |
| attack_up_berserk | 광폭화 | ATTACK_UP | 5 | 0.50 | | Berserker enrage (§7.1). | (1.0, 0.3, 0.2) |
| defense_up | 방어력 상승 | DEFENSE_UP | 3 | 0.25 | | DEF and RES × (1 + mag). | (0.5, 0.7, 1.0) |
| defense_up_l | 철벽 | DEFENSE_UP | 2 | 0.50 | | Strong short guard (iron wall / harden). | (0.4, 0.6, 1.0) |
| burn | 화상 | BURN | 3 | 0.05 | ✔ | Loses mag × max HP at the end of its turn; healing received ×0.5 (this counters regen). | (1.0, 0.5, 0.25) |
| bleed | 출혈 | BLEED | 3 | 0.04 | ✔ | Loses mag × max HP each time it acts (before the action). | (0.85, 0.2, 0.25) |
| slow | 둔화 | SLOW | 3 | 0.25 | ✔ | SPD × (1 − mag). | (0.6, 0.6, 0.8) |
| freeze | 빙결 | FREEZE | 1 | 0.30 | ✔ | Skips its next turn; the next physical hit taken is × (1 + mag), then freeze is removed. | (0.6, 0.9, 1.0) |
| silence | 침묵 | SILENCE | 2 | 1.0 | ✔ | Cannot use skills with mp_cost > 0. Basic attack, items and ultimates are allowed. | (0.7, 0.7, 0.75) |
| attack_down | 공격력 저하 | ATTACK_DOWN | 3 | 0.25 | ✔ | ATK and MAG × (1 − mag). | (0.6, 0.45, 0.7) |
| defense_down | 방어력 저하 | DEFENSE_DOWN | 3 | 0.30 | ✔ | DEF and RES × (1 − mag). | (0.7, 0.5, 0.4) |
| regen | 재생 | REGEN | 3 | 0.06 | | Heals mag × max HP at the end of its turn (halved by burn). | (0.5, 1.0, 0.6) |
| barrier | 보호막 | BARRIER | 3 | 0.20 | | Absorbs up to mag × own max HP; removed when depleted or expired. | (0.85, 0.95, 1.0) |
| barrier_abyss | 심연의 장벽 | BARRIER | 3 | 0.08 | | Boss version (8 % of 8,500 = 680). | (0.45, 0.2, 0.6) |
| provoke | 도발 | PROVOKE | 3 | 1.0 | | Opponents' SINGLE-scope offensive actions must target this unit; ALL and RANDOM are unaffected. | (1.0, 0.35, 0.3) |
| sleep | 수면 | SLEEP | 3 | 1.0 | ✔ | Cannot act; removed on any damage taken (after that hit is resolved). | (0.55, 0.55, 0.9) |
| blind | 실명 | BLIND | 3 | 0.40 | ✔ | Physical hit chance × (1 − mag) = ×0.6. | (0.4, 0.4, 0.45) |
| magic_up | 마력 상승 | MAGIC_UP | 3 | 0.25 | | MAG × (1 + mag). | (0.8, 0.5, 1.0) |
| speed_up | 신속 | SPEED_UP | 3 | 0.30 | | SPD × (1 + mag). | (0.6, 1.0, 0.9) |

Existing resources `poison`, `stun`, `attack_up` and `defense_up` keep their ids and values. Their Korean names remain those in §4. Add `tint` and replace their English descriptions with the exact Korean strings in §4.1.

### 4.1 Exact `description` strings for every status resource
Use these strings verbatim; do not translate or paraphrase the English semantics column. Variant resources have their own ids and the names given in §4.

| id | description |
|---|---|
| poison | 턴이 끝날 때마다 최대 HP의 6%를 잃습니다. |
| poison_strong | 턴이 끝날 때마다 최대 HP의 10%를 잃습니다. |
| stun | 다음 턴에 행동할 수 없습니다. |
| attack_up | 공격력이 25% 오릅니다. |
| attack_up_berserk | 공격력이 50% 오릅니다. |
| defense_up | 방어력과 마법 방어가 25% 오릅니다. |
| defense_up_l | 방어력과 마법 방어가 50% 오릅니다. |
| burn | 턴이 끝날 때마다 최대 HP의 5%를 잃고, 받는 회복량이 절반이 됩니다. |
| bleed | 행동할 때마다 최대 HP의 4%를 잃습니다. |
| slow | 속도가 25% 낮아집니다. |
| freeze | 다음 턴에 행동할 수 없으며, 다음 물리 피해가 30% 증가한 뒤 해제됩니다. |
| silence | MP를 소모하는 스킬을 사용할 수 없습니다. |
| attack_down | 공격력과 마력이 25% 낮아집니다. |
| defense_down | 방어력과 마법 방어가 30% 낮아집니다. |
| regen | 턴이 끝날 때마다 최대 HP의 6%를 회복합니다. |
| barrier | 최대 HP의 20%만큼 피해를 흡수합니다. |
| barrier_abyss | 최대 HP의 8%만큼 피해를 흡수하는 어둠의 장벽입니다. |
| provoke | 적의 단일 대상 공격을 자신에게 끌어들입니다. |
| sleep | 행동할 수 없으며, 피해를 받으면 깨어납니다. |
| blind | 물리 공격의 명중률이 40% 낮아집니다. |
| magic_up | 마력이 25% 오릅니다. |
| speed_up | 속도가 30% 오릅니다. |

All 22 status resources have exactly one Korean display name (§4) and one Korean description (§4.1); no additional status variants are implied.

---

## 5. Items (`ItemData`)
Type enum (append-only): `HEALING=0 MP_RESTORE CURE REVIVE ESCAPE_DUNGEON FLEE_BATTLE DAMAGE MATERIAL BUFF`.

The table's `value` column maps mechanically as follows: HEALING → `heal_amount` and `value`; MP_RESTORE/DAMAGE → integer `value`; REVIVE → ratio `power` (integer `value = 0`); BUFF → `status_id` (integer `value = 0`). CURE with `value = 0` removes all negative statuses. Target labels map to `single_ally`, `all_allies`, `all_enemies`, `none`; `single KO ally` uses `single_ally` plus REVIVE's KO-only filter.

Sell price is 50 % of the buy price. `max_stack` is 9 for consumables and 99 for materials.

### 5.1 Consumables (14)
| id | 이름 | 설명 | type | value | target | price | sell | shop_tier |
|---|---|---|---|---|---|---|---|---|
| healing_potion | 회복약 | 아군 한 명의 HP를 60 회복합니다. | HEALING | 60 | single ally | 30 | 15 | 1 |
| hi_potion | 고급 회복약 | 아군 한 명의 HP를 250 회복합니다. | HEALING | 250 | single ally | 150 | 75 | 2 |
| mega_potion | 특제 회복약 | 아군 한 명의 HP를 600 회복합니다. | HEALING | 600 | single ally | 450 | 225 | 3 |
| elixir | 엘릭서 | 아군 전원의 HP를 모두 회복합니다. | HEALING | 9999 | all allies | 1500 | 750 | 4 |
| ether | 마나 물약 | 아군 한 명의 MP를 30 회복합니다. | MP_RESTORE | 30 | single ally | 120 | 60 | 1 |
| hi_ether | 고급 마나 물약 | 아군 한 명의 MP를 90 회복합니다. | MP_RESTORE | 90 | single ally | 400 | 200 | 3 |
| remedy | 만능약 | 아군 한 명의 해로운 상태이상을 모두 치료합니다. | CURE | 0 | single ally | 60 | 30 | 1 |
| phoenix_feather | 불사조의 깃털 | 쓰러진 아군을 HP 30%로 되살립니다. | REVIVE | 0.30 | single KO ally | 300 | 150 | 2 |
| return_stone | 귀환의 돌 | 전투 밖에서 사용하면 마을로 돌아갑니다. | ESCAPE_DUNGEON | 0 | none | 150 | 75 | 1 |
| smoke_bomb | 연막탄 | 일반·FOE 전투에서 반드시 도망칩니다. | FLEE_BATTLE | 0 | none | 40 | 20 | 1 |
| bomb | 폭탄 | 적 전체에 60의 고정 피해를 줍니다. | DAMAGE | 60 | all enemies | 80 | 40 | 1 |
| big_bomb | 대형 폭탄 | 적 전체에 400의 고정 피해를 줍니다. | DAMAGE | 400 | all enemies | 500 | 250 | 3 |
| power_tonic | 투지의 영약 | 아군 전원의 공격력을 3턴 동안 높입니다. | BUFF | attack_up | all allies | 250 | 125 | 2 |
| guard_tonic | 수호의 영약 | 아군 전원의 방어력을 3턴 동안 높입니다. | BUFF | defense_up | all allies | 250 | 125 | 2 |

### 5.2 Materials (16; type MATERIAL, price 0, shop_tier 0)
| id | 이름 | 설명 | sell | source |
|---|---|---|---|---|
| slime_gel | 슬라임 젤 | 말랑하고 끈적한 젤. 접착제로 쓰인다. | 6 | slime |
| forest_fiber | 질긴 덩굴 섬유 | 유적의 덩굴에서 얻은 질긴 섬유. | 8 | sprout, mushroom |
| bat_wing | 박쥐 날개 | 얇지만 질긴 박쥐의 날개막. | 10 | bat |
| jelly_core | 해파리 핵 | 희미하게 빛나는 해파리의 핵. | 25 | jellyfish |
| coral_shard | 산호 조각 | 바위처럼 단단한 산호 껍질 조각. | 30 | coral_crab |
| frost_fur | 서리 털가죽 | 냉기를 머금은 부드러운 털가죽. | 30 | ice_wolf, penguin_mage |
| magma_core | 용암 핵 | 식지 않는 용암 덩어리. | 60 | magma_slime |
| golem_sandstone | 골렘 사암 | 마력이 깃든 단단한 사암. | 70 | sand_golem |
| drake_scale | 드레이크 비늘 | 열을 견디는 붉은 비늘. | 75 | fire_drake, phoenix |
| old_bone | 오래된 뼈 | 묘소 기사의 단단한 뼈. | 90 | skeleton |
| cursed_straw | 저주받은 짚 | 원한이 스민 허수아비의 짚. | 100 | scarecrow |
| ghost_essence | 망령의 정수 | 차갑게 일렁이는 영혼의 조각. | 110 | wisp, grave_bat |
| verdant_crystal | 신록의 결정 | 숲의 봉인 조각. 생명력이 깃들어 있다. | 150 | verdant elites, forest_guardian |
| frost_crystal | 빙결의 결정 | 바다의 봉인 조각. 결코 녹지 않는다. | 300 | frost elites, frost_kraken |
| ember_crystal | 홍염의 결정 | 태양의 봉인 조각. 손에 쥐면 따뜻하다. | 600 | ember elites, flame_sphinx |
| abyss_crystal | 심연의 결정 | 마지막 봉인에서 새어 나온 검은 결정. | 1000 | crypt elites, scarecrow/wisp (4 %), B11/B12 chests |

---

## 6. Equipment (`EquipmentData`, 48)
- Sell price = 50 % of price; craft-only items sell for 1,500.
- `classes` empty = all heroes.
- Stats not listed are 0. `hit`, `evade` and `crit` are additive floats.
- Element resist on heroes is ×0.5 (§1.2).

### 6.1 Weapons (20)
| id | 이름 | classes | stats | price | tier | craft (materials + gold) |
|---|---|---|---|---|---|---|
| sword_bronze | 청동 장검 | warrior | atk 6 | 80 | 1 | — |
| sword_iron | 무쇠 장검 | warrior | atk 14 | 320 | 1 | — |
| sword_knight | 기사의 검 | warrior | atk 26, def 2 | 1150 | 2 | — |
| sword_flamberge | 플람베르주 | warrior | atk 40, crit 0.03 | 2700 | 3 | — |
| sword_dawn | 여명검 | warrior | atk 56, hit 0.05, crit 0.05 | 0 | 0 | old_bone 4, ember_crystal 1, abyss_crystal 1 + 2400 |
| staff_oak | 참나무 지팡이 | mage | mag 6, mp 5 | 80 | 1 | — |
| staff_crystal | 수정 지팡이 | mage | mag 14, mp 10 | 330 | 1 | — |
| staff_sage | 현자의 지팡이 | mage | mag 26, mp 15, res 4 | 1180 | 2 | — |
| staff_ruby | 홍옥 지팡이 | mage | mag 40, mp 20 | 2750 | 3 | — |
| staff_starlight | 성광의 지팡이 | mage | mag 56, mp 30, spd 4 | 0 | 0 | ghost_essence 4, frost_crystal 1, abyss_crystal 1 + 2400 |
| bow_short | 경석궁 | archer | atk 5, crit 0.03 | 80 | 1 | — |
| bow_hunter | 사냥꾼의 석궁 | archer | atk 12, crit 0.04 | 310 | 1 | — |
| bow_composite | 합성 석궁 | archer | atk 23, crit 0.05, hit 0.03 | 1120 | 2 | — |
| bow_gale | 질풍 석궁 | archer | atk 36, crit 0.06, spd 4 | 2650 | 3 | — |
| bow_star | 유성 석궁 | archer | atk 50, crit 0.08, hit 0.05 | 0 | 0 | cursed_straw 3, ghost_essence 2, abyss_crystal 1 + 2400 |
| mace_wood | 나무 메이스 | cleric | atk 3, mag 5 | 70 | 1 | — |
| mace_silver | 은빛 메이스 | cleric | atk 6, mag 12, mp 5 | 300 | 1 | — |
| mace_blessed | 축복의 메이스 | cleric | atk 10, mag 22, res 4 | 1100 | 2 | — |
| mace_saint | 성자의 홀 | cleric | atk 14, mag 34, mp 15 | 2600 | 3 | — |
| mace_dawn | 새벽의 홀 | cleric | atk 20, mag 48, mp 25, res 8 | 0 | 0 | old_bone 3, ghost_essence 3, abyss_crystal 1 + 2400 |

### 6.2 Armor (15)
| id | 이름 | classes | stats | price | tier | craft |
|---|---|---|---|---|---|---|
| armor_chain | 사슬 갑옷 | warrior | def 6, res 2 | 70 | 1 | — |
| armor_scale | 비늘 갑옷 | warrior | def 13, res 4, hp 20 | 280 | 1 | — |
| armor_plate | 판금 갑옷 | warrior | def 22, res 8, hp 40 | 980 | 2 | — |
| armor_dragon | 용린 갑옷 | warrior | def 33, res 12, hp 70 | 2300 | 3 | — |
| armor_dawn | 여명의 갑주 | warrior | def 46, res 18, hp 100 | 0 | 0 | old_bone 5, golem_sandstone 3, abyss_crystal 1 + 2200 |
| garb_leather | 가죽 경갑 | archer | def 4, res 2 | 60 | 1 | — |
| garb_ranger | 레인저 조끼 | archer | def 9, res 5, hp 10, evade 0.02 | 260 | 1 | — |
| garb_shadow | 그림자 가죽옷 | archer | def 16, res 9, hp 25, evade 0.03 | 920 | 2 | — |
| garb_wind | 바람의 경갑 | archer | def 24, res 14, hp 45, evade 0.04, spd 3 | 2200 | 3 | — |
| garb_dawn | 여명의 경갑 | archer | def 34, res 20, hp 70, evade 0.06, spd 5 | 0 | 0 | cursed_straw 4, drake_scale 3, abyss_crystal 1 + 2100 |
| robe_cloth | 무명 로브 | mage, cleric | def 2, res 5, mp 5 | 50 | 1 | — |
| robe_silk | 비단 로브 | mage, cleric | def 5, res 11, mp 10 | 240 | 1 | — |
| robe_mystic | 신비의 로브 | mage, cleric | def 10, res 19, mp 18, hp 15 | 880 | 2 | — |
| robe_sage | 현자의 법의 | mage, cleric | def 16, res 29, mp 28, hp 30 | 2100 | 3 | — |
| robe_dawn | 여명의 법의 | mage, cleric | def 23, res 41, mp 40, hp 50 | 0 | 0 | ghost_essence 3, frost_fur 3, abyss_crystal 1 + 2000 |

### 6.3 Accessories (13, all classes)
| id | 이름 | 설명 | stats / effects | price | tier | craft |
|---|---|---|---|---|---|---|
| acc_lucky_charm | 행운의 부적 | 네잎 문양이 새겨진 부적. | crit 0.05, evade 0.02 | 300 | 1 | — |
| acc_antidote_ring | 해독의 반지 | 독을 막아 주는 녹색 반지. | res 3; immune poison, poison_strong | 350 | 1 | forest_fiber 3, slime_gel 2 + 150 |
| acc_power_band | 힘의 팔찌 | 착용자의 근력을 끌어올린다. | atk 8 | 600 | 2 | — |
| acc_sage_pendant | 현자의 펜던트 | 마력이 맑게 흐르게 한다. | mag 8, mp 10 | 650 | 2 | — |
| acc_awake_bell | 각성의 방울 | 맑은 소리가 잠을 쫓는다. | spd 2; immune sleep | 700 | 2 | — |
| acc_frost_amulet | 서리 부적 | 냉기를 막아 주는 푸른 부적. | res 6; resist ICE | 900 | 2 | frost_fur 3, coral_shard 2 + 400 |
| acc_wind_boots | 질풍의 장화 | 바람처럼 가벼운 장화. | spd 8, evade 0.05 | 1800 | 3 | — |
| acc_flame_amulet | 화염 부적 | 불길을 막아 주는 붉은 부적. | res 10; resist FIRE | 2000 | 3 | drake_scale 3, magma_core 2 + 900 |
| acc_eagle_eye | 매의 눈 | 먼 곳의 급소까지 보이게 한다. | hit 0.10, crit 0.08 | 2200 | 3 | — |
| acc_clarity_earring | 청명의 귀걸이 | 정신을 맑게 지켜 준다. | mp 20; immune silence, blind | 3000 | 4 | — |
| acc_shadow_amulet | 어둠막이 부적 | 심연의 어둠을 밀어낸다. | res 14; resist DARK | 3200 | 4 | ghost_essence 3, old_bone 2 + 1500 |
| acc_guardian_ring | 수호의 반지 | 봉인의 힘을 담은 반지. | def 15, res 15, hp 60; immune stun | 0 | 0 | coral_shard 3, golem_sandstone 3, frost_crystal 1, ember_crystal 1 + 2500 |
| acc_hero_emblem | 영웅의 문장 | 네 봉인의 결정을 모은 증표. | atk 12, mag 12, def 10, res 10, spd 6, hp 80, crit 0.05 | 0 | 0 | verdant_crystal 1, frost_crystal 1, ember_crystal 1, abyss_crystal 1 + 5000 |

### 6.4 Mechanical authoring: slots and exact Korean descriptions
- All 20 entries in §6.1 have `slot = &"weapon"`; all 15 entries in §6.2 have `slot = &"armor"`; all 13 entries in §6.3 have `slot = &"accessory"` and `classes = []`.
- §6.3's `설명` cells are the exact accessory `description` strings. Use the exact strings below for the other 35 resources. No UI-generated string substitutes for a resource's `description`.
- The `tier` columns in §6.1–6.3 mean **shop_tier**, not progression gear tier. The five weapon/armor rows per family are progression T1–T5 in their listed order. Recipe quantities, stats, prices and shop tiers remain exactly as listed above.
- A `—` recipe means `craft_materials = {}` and `craft_gold = 0`. All unspecified stats are 0, and unspecified resist/immunity arrays are empty.

| id | description |
|---|---|
| sword_bronze | 처음 미궁에 들어서는 검사를 위한 청동 장검입니다. |
| sword_iron | 단단한 무쇠로 벼린 실용적인 장검입니다. |
| sword_knight | 기사단의 문장이 새겨진 믿음직한 검입니다. |
| sword_flamberge | 물결치는 칼날이 적의 급소를 노리는 검입니다. |
| sword_dawn | 봉인의 힘을 담아 어둠을 가르는 여명의 검입니다. |
| staff_oak | 원소 마법의 기초를 익히는 참나무 지팡이입니다. |
| staff_crystal | 맑은 수정이 마력을 모아 주는 지팡이입니다. |
| staff_sage | 현자의 지혜가 깃든 마법 지팡이입니다. |
| staff_ruby | 붉은 홍옥이 강한 마력을 이끌어 내는 지팡이입니다. |
| staff_starlight | 별빛과 봉인의 결정을 엮은 최상급 지팡이입니다. |
| bow_short | 가볍고 다루기 쉬운 입문용 석궁입니다. |
| bow_hunter | 사냥꾼이 즐겨 쓰는 균형 잡힌 석궁입니다. |
| bow_composite | 여러 재료를 겹쳐 힘과 정확도를 높인 석궁입니다. |
| bow_gale | 바람처럼 빠르게 겨눌 수 있는 질풍의 석궁입니다. |
| bow_star | 유성처럼 정확한 화살을 쏘는 봉인의 석궁입니다. |
| mace_wood | 초보 성직자를 위한 소박한 나무 메이스입니다. |
| mace_silver | 은빛 머리 장식에 기도를 담은 메이스입니다. |
| mace_blessed | 치유와 수호의 축복을 받은 메이스입니다. |
| mace_saint | 성자의 기도가 깃든 신성한 홀입니다. |
| mace_dawn | 마지막 봉인을 밝히는 새벽의 홀입니다. |
| armor_chain | 움직임을 크게 방해하지 않는 사슬 갑옷입니다. |
| armor_scale | 겹친 금속 비늘이 몸을 보호하는 갑옷입니다. |
| armor_plate | 두꺼운 판금으로 전위를 지키는 갑옷입니다. |
| armor_dragon | 드레이크의 단단한 비늘로 보강한 갑옷입니다. |
| armor_dawn | 봉인의 결정을 품은 최상급 여명의 갑주입니다. |
| garb_leather | 궁수의 움직임을 살리는 가벼운 가죽 경갑입니다. |
| garb_ranger | 숲의 탐색자를 위한 질긴 가죽 조끼입니다. |
| garb_shadow | 그림자처럼 몸을 숨기기 좋은 유연한 가죽옷입니다. |
| garb_wind | 바람처럼 가볍게 움직일 수 있는 경갑입니다. |
| garb_dawn | 여명의 힘으로 회피와 기동성을 높인 경갑입니다. |
| robe_cloth | 마법사와 성직자가 함께 입는 소박한 로브입니다. |
| robe_silk | 마력의 흐름을 돕는 부드러운 비단 로브입니다. |
| robe_mystic | 신비한 문양이 마법 방어를 높여 주는 로브입니다. |
| robe_sage | 현자의 지식으로 짜인 고급 마법 법의입니다. |
| robe_dawn | 봉인의 힘이 착용자를 감싸는 여명의 법의입니다. |

---

## 7. Enemies

### 7.1 AI profiles (design intent for T11)
| profile | behavior |
|---|---|
| basic | Weighted random over `skills`/`skill_weights`; skips skills it lacks MP for; SINGLE targets are random. |
| aggressive | Same skill choice; SINGLE offensive targets = lowest current HP %. |
| caster | 75 % chance to pick the weighted non-basic skill it can afford; falls back to basic_attack when out of MP. |
| support | When any ally is below 60 % HP and it has a HEAL skill → heal. Otherwise weighted pick. |
| summoner | When it has fewer than `summon_limit` living summoned units and the group has fewer than 5 enemies: 35 % chance to summon one random id from `summons` (log line "동료를 불러냈다!"). Otherwise weighted pick. |
| berserker | The first time it falls below 30 % HP, it applies `attack_up_berserk` to itself (log "광폭화했다!"), and from then on targets like aggressive. |
| boss | Uses the current phase's `skills`/`weights`/`actions_per_turn`. Entering a phase emits `phase_changed(line)` once and spawns `summon` ids (up to 5 enemies total). Phases are checked after every hit. |

### 7.2 Normal enemies (16)
All rank 0. `evade` defaults to 0.05 and `hit` to 0.95. `grave_bat` is **new**: it reuses the bat rig with `tint (0.62, 0.52, 0.85)` and `scale_mult 1.0`. It is added so the crypt also has 4 normal enemies. All other ids are existing.

| id | 이름 | Lv | HP | MP | ATK | MAG | DEF | RES | SPD | eva | brk | weak | resist | AI | skills (weights) | xp | gold | drops |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| slime | 숲 슬라임 | 2 | 90 | 0 | 20 | 17 | 9 | 9 | 11 | .05 | 2 | FIRE | BLUNT | basic | basic_attack 3, sk_acid_spit 1 | 12 | 20 | slime_gel .40, healing_potion .08 |
| sprout | 풀뿌리 | 3 | 110 | 0 | 22 | 19 | 14 | 10 | 10 | .05 | 2 | FIRE, SLASH | PIERCE | basic | basic_attack 3, sk_root_bind 2 | 16 | 24 | forest_fiber .40 |
| mushroom | 독버섯 | 5 | 160 | 20 | 27 | 32 | 15 | 19 | 11 | .05 | 2 | FIRE | — | caster | basic_attack 2, poison_spore 3 | 49 | 44 | forest_fiber .35, remedy .08 |
| bat | 동굴 박쥐 | 6 | 145 | 0 | 31 | 26 | 12 | 15 | 24 | .15 | 2 | PIERCE, THUNDER | BLUNT | aggressive | basic_attack 4, sk_screech 1 | 65 | 48 | bat_wing .40 |
| jellyfish | 물방울 해파리 | 11 | 210 | 30 | 41 | 48 | 21 | 41 | 17 | .08 | 2 | THUNDER | ICE | caster | basic_attack 2, sk_lullaby 2 | 95 | 46 | jelly_core .40, ether .05 |
| coral_crab | 산호 소라게 | 13 | 225 | 0 | 49 | 38 | 56 | 16 | 15 | .03 | 4 | THUNDER | PIERCE | basic | basic_attack 3, sk_harden 1 | 115 | 58 | coral_shard .40 |
| penguin_mage | 펭귄 마법사 | 14 | 240 | 40 | 43 | 57 | 23 | 37 | 22 | .05 | 3 | FIRE | ICE | caster | basic_attack 1, sk_ice_shard 3, sk_blizzard 2 | 130 | 64 | frost_fur .35, ether .08 |
| ice_wolf | 서리 늑대 | 16 | 265 | 0 | 55 | 43 | 25 | 26 | 36 | .08 | 3 | FIRE | ICE | aggressive | basic_attack 3, sk_twin_bite 2 | 150 | 70 | frost_fur .40 |
| magma_slime | 용암 슬라임 | 20 | 380 | 24 | 65 | 61 | 37 | 39 | 25 | .05 | 2 | ICE | FIRE | summoner (summons [magma_slime], summon_limit 1) | basic_attack 3, fireball 2 | 312 | 120 | magma_core .40 |
| sand_golem | 모래 골렘 | 22 | 510 | 0 | 72 | 56 | 72 | 41 | 21 | .02 | 5 | ICE | PIERCE, FIRE | basic | basic_attack 3, sk_sandstorm 1 | 403 | 150 | golem_sandstone .40 |
| phoenix | 새끼 불사조 | 24 | 430 | 40 | 69 | 75 | 35 | 55 | 45 | .12 | 2 | ICE | FIRE | support | basic_attack 2, sk_rebirth_flame 2 | 416 | 150 | drake_scale .30, phoenix_feather .06 |
| fire_drake | 불꽃 드레이크 | 25 | 540 | 30 | 75 | 82 | 53 | 56 | 32 | .05 | 4 | ICE | FIRE | caster | basic_attack 2, sk_fire_breath 2 | 481 | 175 | drake_scale .40 |
| skeleton | 해골 병사 | 29 | 625 | 0 | 82 | 61 | 64 | 41 | 32 | .05 | 3 | HOLY, BLUNT | PIERCE, DARK | basic | basic_attack 3, sk_harden 1 | 240 | 185 | old_bone .45 |
| grave_bat | 무덤 박쥐 | 30 | 575 | 0 | 84 | 82 | 39 | 56 | 48 | .15 | 2 | HOLY, PIERCE | DARK | aggressive | basic_attack 3, sk_curse_screech 1 | 246 | 180 | ghost_essence .35 |
| scarecrow | 호박 허수아비 | 32 | 815 | 0 | 97 | 81 | 68 | 64 | 30 | .05 | 3 | HOLY, FIRE | DARK | berserker | basic_attack 2, sk_crow_swarm 2 | 282 | 210 | cursed_straw .40, abyss_crystal .04 |
| wisp | 도깨비불 | 34 | 720 | 60 | 84 | 112 | 47 | 99 | 42 | .10 | 2 | HOLY | DARK, FIRE | caster | basic_attack 1, sk_spirit_fire 3, sk_hex 1 | 312 | 230 | ghost_essence .40, abyss_crystal .04 |

Each enemy's hook:
- **slime**: its acid lowers DEF, which teaches the value of `defense_up`.
- **sprout**: slows a hero, which shows turn order matters.
- **mushroom**: party-wide poison, so you bring `remedy` and use `sk_cure`.
- **bat**: fast, evasive and hunts the weakest hero; it blinds attackers, and archers and thunder answer it.
- **jellyfish**: sleeps the party, so hit the sleeper to wake them or cleanse.
- **coral_crab**: a wall with DEF 56 and RES 16, which teaches you to switch to magic and thunder.
- **penguin_mage**: a back-row AoE caster to kill first with fire.
- **ice_wolf**: a fast pack hunter that goes for the lowest HP; provoke counters it.
- **magma_slime**: splits, so kill it fast or AoE it.
- **sand_golem**: a big shield of 5 pips; break it with ice.
- **phoenix**: heals its allies, so focus it.
- **fire_drake**: AoE burn, which makes `acc_flame_amulet` worth buying.
- **skeleton**: resists piercing and is weak to blunt and holy, which rewards the cleric's mace and the warrior's slam.
- **grave_bat**: silences casters, so `acc_clarity_earring` and `remedy` matter.
- **scarecrow**: random pecks plus an enrage.
- **wisp**: a high-RES caster that debuffs the whole party; use physical damage or holy.

### 7.3 Elites / FOEs (rank 1, 8)
All elites use the base rig with `tint` and `scale_mult`, and the gimmick `cc_resist`. Each elite's level is set to the floor where it first appears, plus 2–3.

| id | 이름 | base rig | tint | scale | Lv | HP | MP | ATK | MAG | DEF | RES | SPD | eva | brk | act | weak | resist | AI | skills (weights) | xp | gold | drops |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| elite_mushroom | 독왕 버섯 | mushroom | (0.72, 0.45, 1.0) | 1.35 | 7 | 760 | 40 | 40 | 44 | 22 | 24 | 15 | .05 | 4 | 1 | FIRE | — | summoner [mushroom], max 2 | basic_attack 1, poison_spore 2, sk_toxic_cloud 2 | 390 | 225 | verdant_crystal .6, forest_fiber 1.0, phoenix_feather .2 |
| elite_bat | 밤의 박쥐 군주 | bat | (1.0, 0.45, 0.45) | 1.4 | 10 | 820 | 30 | 52 | 40 | 20 | 26 | 34 | .18 | 3 | 2 | PIERCE, THUNDER | BLUNT | aggressive | basic_attack 3, sk_screech 1, sk_bleed_edge 2 | 585 | 330 | verdant_crystal .6, bat_wing 1.0 |
| elite_ice_wolf | 설원의 우두머리 | ice_wolf | (0.75, 0.9, 1.0) | 1.35 | 14 | 1150 | 30 | 66 | 50 | 32 | 30 | 40 | .08 | 4 | 2 | FIRE | ICE | summoner [ice_wolf], max 2 | basic_attack 2, sk_twin_bite 3, sk_war_cry 1 | 900 | 450 | frost_crystal .6, frost_fur 1.0 |
| elite_coral_crab | 거대 산호 집게 | coral_crab | (1.0, 0.55, 0.4) | 1.45 | 17 | 1500 | 40 | 72 | 50 | 80 | 28 | 18 | .03 | 6 | 2 | THUNDER | PIERCE, SLASH | basic | basic_attack 3, sk_harden 1, sk_titan_crash 2 | 1200 | 600 | frost_crystal .6, coral_shard 1.0 |
| elite_fire_drake | 홍염 비룡 | fire_drake | (1.0, 0.35, 0.3) | 1.35 | 23 | 2000 | 60 | 92 | 94 | 55 | 55 | 34 | .05 | 5 | 2 | ICE | FIRE | caster | basic_attack 2, sk_fire_breath 3, sk_inferno 1 | 2200 | 1100 | ember_crystal .6, drake_scale 1.0 |
| elite_sand_golem | 사막의 거상 | sand_golem | (0.95, 0.8, 0.5) | 1.4 | 26 | 2600 | 40 | 104 | 70 | 95 | 50 | 24 | .02 | 7 | 1 | ICE | PIERCE, FIRE | berserker | basic_attack 3, sk_sandstorm 1, sk_titan_crash 2 | 2700 | 1300 | ember_crystal .6, golem_sandstone 1.0 |
| elite_skeleton | 해골 장군 | skeleton | (0.6, 0.65, 0.85) | 1.35 | 32 | 2500 | 60 | 120 | 80 | 85 | 60 | 38 | .05 | 5 | 2 | HOLY, BLUNT | PIERCE, DARK | summoner [skeleton], max 2 | basic_attack 2, sk_cleave 2, sk_bleed_edge 2, sk_harden 1 | 2400 | 1600 | abyss_crystal .6, old_bone 1.0 |
| elite_scarecrow | 허수아비 왕 | scarecrow | (0.55, 0.35, 0.7) | 1.4 | 35 | 2700 | 40 | 128 | 110 | 72 | 70 | 40 | .05 | 5 | 2 | HOLY, FIRE | DARK | berserker | basic_attack 1, sk_crow_swarm 2, sk_dread_stare 1, sk_harvest_reap 2 | 3000 | 2000 | abyss_crystal .6, cursed_straw 1.0 |

### 7.4 Bosses (rank 2, `is_boss = true`, gimmicks `cc_immune, dot_resist`)
The `skills` array = the union of all phase skills; `skill_weights` is unused for bosses.

| id | 이름 | Lv | HP | MP | ATK | MAG | DEF | RES | SPD | brk | weak | resist | xp | gold | drops |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| forest_guardian | 고목 수호자 | 10 | 3960 | 40 | 101 | 97 | 25 | 27 | 16 | 4 | FIRE, SLASH | ICE, BLUNT | 1100 | 500 | verdant_crystal 1.0, phoenix_feather 1.0 |
| frost_kraken | 빙해의 크라켄 여왕 | 19 | 6435 | 0 | 137 | 130 | 40 | 43 | 26 | 5 | THUNDER, FIRE | ICE, PIERCE | 3000 | 1500 | frost_crystal 1.0, hi_potion 1.0 |
| flame_sphinx | 불꽃 스핑크스 | 28 | 7560 | 60 | 138 | 132 | 57 | 60 | 34 | 5 | ICE, THUNDER | FIRE, HOLY | 5500 | 3000 | ember_crystal 1.0, mega_potion 1.0 |
| boss | 심연의 망령술사 | 36 | 5600 | 0 | 203 | 216 | 70 | 78 | 40 | 6 | HOLY | DARK, ICE | 8000 | 5000 | abyss_crystal 1.0 |

**Phases**: `hp_below` is a fraction of max HP; skills are listed with their weights.

| boss | hp_below | actions | skills (weights) | summon | line |
|---|---|---|---|---|---|
| forest_guardian | 1.0 | 1 | basic_attack 3, sk_vine_lash 2, sk_root_bind 2, sk_photosynthesis 1 | — | 숲을 어지럽히는 자들이여… 뿌리 아래 잠들어라. |
| | 0.5 | 2 | sk_vine_lash 2, strong_attack 2, sk_root_bind 1, sk_photosynthesis 2 | sprout, sprout | 뿌리여, 깨어나라! 이 숲을 지켜라! |
| frost_kraken | 1.0 | 2 | basic_attack 2, sk_tentacle_crush 2, sk_freezing_tide 2, sk_ink_cloud 1 | — | 쉿… 노래를 멈추지 마. 바다가 깨어나면 모두 얼어붙을 테니. |
| | 0.6 | 2 | sk_tentacle_crush 3, sk_freezing_tide 2, sk_ink_cloud 1 | jellyfish, jellyfish | 내 아이들아, 이리 오렴. 차가운 품으로. |
| | 0.25 | 3 | sk_tentacle_crush 3, sk_freezing_tide 2 | — | 심해의 분노를… 느껴라! |
| flame_sphinx | 1.0 | 2 | basic_attack 2, sk_bleed_edge 2, sk_solar_flare 2, sk_riddle_silence 1 | — | 답하지 못하는 자에게 태양은 자비가 없다. |
| | 0.6 | 2 | sk_sun_aegis 2, sk_solar_flare 3, sk_bleed_edge 2, sk_riddle_silence 1 | — | 태양이 나를 감싼다. 너희의 지혜를 보여라! |
| | 0.3 | 2 | sk_sun_judgment 2, sk_solar_flare 2, sk_bleed_edge 1 | — | 마지막 수수께끼다. 태양의 심판을 견뎌라! |
| boss | 1.0 | 2 | sk_abyss_bolt 3, sk_abyss_wave 2, sk_dread_stare 1, sk_abyss_wall 1 | skeleton, skeleton | 루멘의 종지기들인가. 늦었다. 봉인은 이미 내 손 안에 있다. |
| | 0.5 | 3 | sk_soul_reap 3, sk_abyss_wave 2, sk_abyss_bolt 2, sk_dread_stare 1, sk_abyss_wall 1 | wisp, wisp | 이 몸이 부서져도 좋다! 심연이여, 나를 영원하게 하라! |

What each boss teaches:
- **고목 수호자**:
  - Fire is its weakness, and burn halves its photosynthesis regen.
  - Break its 4 pips with fire or slash to skip its turn.
  - In phase 2 its sprouts must be cleaved with AoE.
- **크라켄 여왕**:
  - Freeze sets up the tentacle crush (+30 % from freeze ×1.5 bonus), so cleanse or `remedy` frozen allies.
  - Ink causes blind, so magic-first is the plan.
  - Thunder AoE kills the jellyfish adds and breaks her at the same time.
- **불꽃 스핑크스**:
  - Silence shuts down the healer, so carry `remedy` and `acc_clarity_earring`.
  - Fire resist amulets halve its flare and judgment.
  - Holy is resisted, so the cleric heals.
  - Breaking it with ice during phase 3 cancels a judgment turn.
- **심연의 망령술사**:
  - Sleep followed by soul reap (×1.5 vs sleep) punishes neglect, so `acc_awake_bell` counters it.
  - Holy is its only weakness.
  - Its barrier must be burst down.
  - Phase 2 has 3 actions: save ultimates and use `sk_iron_wall` / `sk_sanctuary`.

Boss rigs:
- `forest_guardian`, `frost_kraken` and `flame_sphinx` are new art (T18). Their archetype is `body_only` until the rigs exist.
- `boss` keeps its current rig.

---

## 8. Floors B1–B12
- Maps are 15×15 (T13 authors the layouts; FOE coordinates are T13's choice following the behavior column).
- Tilesets and backdrops are per biome and reuse the existing values of the biome's first floor (`fog_color`, `ambient_particle_tint`, `overlay`, `battle_backdrop`).
- Keys open `L` doors on the same floor.
- Encounter checks happen per step after `min_encounter_steps` steps without battle; the counter resets after every battle.

### 8.0 Canonical paths and ids (binding shared contract R8)
Paths below are relative to the repo root; resource paths prepend `res://`. **Keep the four existing filenames at indices 0, 3, 6 and 9** even though their old filename prefixes no longer match the current floor label. Neither filenames nor ids may be inferred from the label.

| index | floor | id | file |
|---|---|---|---|
| 0 | B1F | verdant_ruins | data/dungeon/b1_verdant_ruins.tres |
| 1 | B2F | verdant_ruins_b2 | data/dungeon/floor02_verdant_ruins_b2.tres |
| 2 | B3F | verdant_ruins_b3 | data/dungeon/floor03_verdant_ruins_b3.tres |
| 3 | B4F | frost_grotto | data/dungeon/b2_frost_grotto.tres |
| 4 | B5F | frost_grotto_b5 | data/dungeon/floor05_frost_grotto_b5.tres |
| 5 | B6F | frost_grotto_b6 | data/dungeon/floor06_frost_grotto_b6.tres |
| 6 | B7F | ember_caverns | data/dungeon/b3_ember_caverns.tres |
| 7 | B8F | ember_caverns_b8 | data/dungeon/floor08_ember_caverns_b8.tres |
| 8 | B9F | ember_caverns_b9 | data/dungeon/floor09_ember_caverns_b9.tres |
| 9 | B10F | haunted_crypt | data/dungeon/b4_haunted_crypt.tres |
| 10 | B11F | haunted_crypt_b11 | data/dungeon/floor11_haunted_crypt_b11.tres |
| 11 | B12F | haunted_crypt_b12 | data/dungeon/floor12_haunted_crypt_b12.tres |

### 8.1 Overview
| # | floor id | label | 이름 | 한 줄 설명 | tileset | rate | grace | chests | lore | traps X | doors L/K | spring H | warp W | FOEs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | verdant_ruins | B1F | 이끼 낀 숲의 유적 | 이끼 덮인 돌기둥 사이로 오래된 통로가 이어지고 있다. | verdant_ruins | 0.06 | 8 | 4 | 2 | 0 | 0 | 0 | — | 0 |
| 1 | verdant_ruins_b2 | B2F | 덩굴 회랑 | 검게 물든 덩굴이 회랑의 기둥을 칭칭 감고 있다. | verdant_ruins | 0.07 | 6 | 5 | 2 | 2 | 1 | 0 | — | 1 |
| 2 | verdant_ruins_b3 | B3F | 고목의 성소 | 거대한 고목의 뿌리가 성소의 바닥을 들어 올렸다. | verdant_ruins | 0.07 | 6 | 5 | 2 | 3 | 1 | 1 (before boss) | — | 2 |
| 3 | frost_grotto | B4F | 얼어붙은 해식 동굴 | 바닷물이 얼어붙은 동굴에 차가운 바람이 스며들고 있다. | frost_grotto | 0.07 | 6 | 5 | 2 | 2 | 0 | 0 | ✔ | 1 |
| 4 | frost_grotto_b5 | B5F | 빙결의 수로 | 얼음 아래로 검은 바닷물이 소리 없이 흐른다. | frost_grotto | 0.075 | 5 | 6 | 2 | 4 | 1 | 0 | — | 2 |
| 5 | frost_grotto_b6 | B6F | 여왕의 빙해 | 얼어붙은 바다 한가운데, 여왕의 노랫소리가 울린다. | frost_grotto | 0.075 | 5 | 5 | 3 | 3 | 1 | 1 (before boss) | — | 2 |
| 6 | ember_caverns | B7F | 불타는 사막 동굴 | 모래 섞인 열기가 갈라진 바위틈에서 피어오르고 있다. | ember_caverns | 0.075 | 5 | 5 | 2 | 4 | 0 | 0 | ✔ | 1 |
| 7 | ember_caverns_b8 | B8F | 용암 협곡 | 붉은 용암이 협곡 아래를 강처럼 흐른다. | ember_caverns | 0.08 | 5 | 6 | 2 | 5 | 1 | 0 | — | 2 |
| 8 | ember_caverns_b9 | B9F | 태양의 제단 | 무너진 태양 신전, 제단 위에서 불꽃이 눈을 뜬다. | ember_caverns | 0.08 | 5 | 6 | 3 | 4 | 1 | 1 (before boss) | — | 2 |
| 9 | haunted_crypt | B10F | 망자의 지하 묘소 | 잠들지 못한 망자들의 기척이 묘소 깊은 곳에서 느껴진다. | haunted_crypt | 0.08 | 5 | 6 | 2 | 4 | 1 | 0 | ✔ | 1 |
| 10 | haunted_crypt_b11 | B11F | 통곡의 납골당 | 벽마다 이름 모를 유골이 잠들어 흐느낀다. | haunted_crypt | 0.085 | 4 | 7 | 3 | 5 | 1 | 0 | — | 2 |
| 11 | haunted_crypt_b12 | B12F | 심연의 옥좌 | 대현자의 무덤 아래, 심연으로 이어지는 옥좌가 있다. | haunted_crypt | 0.085 | 4 | 6 | 3 | 5 | 1 | 1 (before boss) | — | 2 |

Key names (`key_name`) by floor:

| Floor | Key name |
|---|---|
| B2 | 덩굴 문 열쇠 |
| B3 | 고목 성소 열쇠 |
| B5 | 얼음 수문 열쇠 |
| B6 | 산호 문 열쇠 |
| B8 | 협곡 문 열쇠 |
| B9 | 태양 문 열쇠 |
| B10 | 묘지기의 열쇠 |
| B11 | 납골당 열쇠 |
| B12 | 옥좌의 열쇠 |

The pickup message is "<key_name>를 얻었다." When a locked door is touched without the key, the message is "굳게 잠긴 문이다. 열쇠가 필요하다."

### 8.2 Encounters
- Random groups are picked uniformly.
- `E` = a one-time event battle using `showcase_group`, which cannot be fled.
- Bosses stand on the `B` cell.

| floor | encounter groups | showcase_group (E) | boss group (B) |
|---|---|---|---|
| verdant_ruins | [slime, slime] · [slime, sprout] · [sprout, slime, slime] · [sprout, sprout] | [slime, sprout, slime] | — |
| verdant_ruins_b2 | [mushroom, mushroom, slime] · [bat, sprout, sprout] · [mushroom, sprout, slime, slime] · [bat, bat] · [bat, mushroom, sprout] | [mushroom, mushroom, bat] | — |
| verdant_ruins_b3 | [bat, bat, mushroom, mushroom] · [mushroom, mushroom, mushroom, sprout] · [bat, bat, bat] · [bat, mushroom, mushroom, slime] · [bat, bat, sprout, sprout] | [bat, bat, mushroom, mushroom, sprout] | [forest_guardian] |
| frost_grotto | [jellyfish, jellyfish, coral_crab] · [jellyfish, penguin_mage] · [coral_crab, jellyfish, jellyfish, jellyfish] · [penguin_mage, coral_crab] · [jellyfish, jellyfish, penguin_mage] | [coral_crab, jellyfish, jellyfish, penguin_mage] | — |
| frost_grotto_b5 | [ice_wolf, ice_wolf, jellyfish] · [penguin_mage, penguin_mage, coral_crab] · [ice_wolf, penguin_mage, jellyfish, jellyfish] · [coral_crab, coral_crab, ice_wolf] · [ice_wolf, ice_wolf, ice_wolf] | [ice_wolf, ice_wolf, ice_wolf, penguin_mage] | — |
| frost_grotto_b6 | [ice_wolf, ice_wolf, penguin_mage, jellyfish] · [coral_crab, coral_crab, penguin_mage, penguin_mage] · [ice_wolf, ice_wolf, coral_crab, penguin_mage] · [jellyfish, jellyfish, jellyfish, penguin_mage, penguin_mage] | [coral_crab, coral_crab, penguin_mage, penguin_mage, jellyfish] | [frost_kraken] |
| ember_caverns | [magma_slime, magma_slime, magma_slime] · [magma_slime, sand_golem] · [magma_slime, magma_slime, phoenix] · [sand_golem, magma_slime, magma_slime] · [phoenix, magma_slime, sand_golem] | [magma_slime, magma_slime, sand_golem, phoenix] | — |
| ember_caverns_b8 | [fire_drake, magma_slime, magma_slime] · [sand_golem, phoenix, magma_slime] · [fire_drake, phoenix] · [sand_golem, sand_golem, magma_slime] · [phoenix, phoenix, magma_slime, magma_slime] | [fire_drake, phoenix, phoenix, magma_slime] | — |
| ember_caverns_b9 | [fire_drake, fire_drake, phoenix] · [sand_golem, fire_drake, magma_slime, magma_slime] · [phoenix, phoenix, fire_drake] · [sand_golem, sand_golem, phoenix] | [sand_golem, fire_drake, fire_drake, phoenix] | [flame_sphinx] |
| haunted_crypt | [skeleton, skeleton, grave_bat] · [skeleton, skeleton, skeleton] · [grave_bat, grave_bat, skeleton] · [skeleton, skeleton, grave_bat, grave_bat] · [scarecrow, skeleton] | [skeleton, skeleton, skeleton, grave_bat, grave_bat] | — |
| haunted_crypt_b11 | [scarecrow, skeleton, grave_bat] · [wisp, skeleton, skeleton] · [scarecrow, scarecrow, grave_bat] · [wisp, grave_bat, grave_bat] · [skeleton, skeleton, scarecrow, grave_bat] | [scarecrow, wisp, wisp, skeleton] | — |
| haunted_crypt_b12 | [wisp, wisp, scarecrow] · [scarecrow, skeleton, wisp, grave_bat] · [wisp, skeleton, skeleton, skeleton] · [scarecrow, scarecrow, wisp] · [grave_bat, grave_bat, wisp, wisp] | [scarecrow, scarecrow, wisp, wisp, grave_bat] | [boss] |

### 8.3 FOEs
Defeated FOEs stay dead until the party rests at the inn. `power` (T28, optional key in each `foes` Dictionary of `data/dungeon/*.tres`, default 1.0) multiplies max HP, ATK and MAG of every enemy in that FOE battle, summons included, and its XP/gold rewards by (1 + power) / 2 (all rounded, after the difficulty scale). Random, event and boss battles ignore it. Values target 35–65 % wins at the floor-arrival level (fresh party, general stock, no smoke bomb) and at least 85 % at +4 levels; see `BALANCE_REPORT.md`.

| floor | foe id | group | power | behavior (patrol + chase_range) |
|---|---|---|---|---|
| B2 | foe_b2_1 | [elite_mushroom, mushroom] | 2.05 | 8-cell loop around a central pillar block in the main hall; chase 0 (never chases; teaches the rhythm safely). |
| B3 | foe_b3_1 | [elite_bat, bat, bat] | 2.1 | Back-and-forth along the long east corridor; chase 3. |
| B3 | foe_b3_2 | [elite_mushroom, mushroom] | 2.45 | 2-cell sway guarding a dead end with a chest; chase 0. |
| B4 | foe_b4_1 | [elite_ice_wolf, ice_wolf] | 1.6 | Loop around the frozen pool room; chase 4. |
| B5 | foe_b5_1 | [elite_coral_crab, jellyfish, jellyfish] | 1.95 | 2-cell sway blocking a shortcut corridor (go around or fight); chase 0. |
| B5 | foe_b5_2 | [elite_ice_wolf, ice_wolf] | 2.0 | Long loop through the canal; chase 4. |
| B6 | foe_b6_1 | [elite_coral_crab, jellyfish, jellyfish] | 2.05 | 2-cell sway (11,9) ↔ (9,9) guarding the spring; chase 1. |
| B6 | foe_b6_2 | [elite_ice_wolf, ice_wolf] | 2.15 | Loop crossing the route to the boss; chase 4. |
| B7 | foe_b7_1 | [elite_fire_drake] | 2.3 | Big loop around the central sand pit; chase 3. |
| B8 | foe_b8_1 | [elite_sand_golem, magma_slime] | 2.2 | 2-cell sway (8,9) ↔ (7,9) on the bridge approach; chase 1. |
| B8 | foe_b8_2 | [elite_fire_drake] | 2.55 | Loop in the west canyon; chase 3. |
| B9 | foe_b9_1 | [elite_sand_golem, magma_slime] | 2.4 | 2-cell sway (5,11) ↔ (3,11) beside the key; chase 1. |
| B9 | foe_b9_2 | [elite_fire_drake] | 2.7 | Loop around the inner sanctum; chase 4. |
| B10 | foe_b10_1 | [elite_skeleton, skeleton] | 2.35 | Patrol around the locked door; chase 3. |
| B11 | foe_b11_1 | [elite_scarecrow, wisp] | 1.95 | Long loop through the ossuary halls; chase 5 (a hunter). |
| B11 | foe_b11_2 | [elite_skeleton, skeleton] | 2.55 | 8-cell ring around the key room; chase 2 (wait to pass). |
| B12 | foe_b12_1 | [elite_scarecrow, wisp] | 2.1 | Loop on the throne approach; chase 4. |
| B12 | foe_b12_2 | [elite_skeleton, skeleton] | 2.7 | 8-cell ring around the key room, including the spring; chase 2 (wait to pass). |

### 8.4 Treasures (`T` cells, in order of authoring)
Format: `gold N` / `item id ×n` / `equip id`.

| floor | chests |
|---|---|
| B1 | gold 50 · healing_potion ×2 · acc_lucky_charm · remedy ×1 |
| B2 | gold 120 · ether ×1 · equip bow_hunter · healing_potion ×3 · return_stone ×1 |
| B3 | gold 200 · equip acc_power_band · equip robe_silk · phoenix_feather ×1 · ether ×2 |
| B4 | gold 400 · hi_potion ×2 · equip acc_frost_amulet · equip sword_knight · remedy ×3 |
| B5 | gold 600 · hi_potion ×2 · ether ×2 · equip acc_awake_bell · equip garb_shadow · phoenix_feather ×1 |
| B6 | gold 800 · hi_ether ×1 · equip acc_sage_pendant · return_stone ×2 · bomb ×3 |
| B7 | gold 1200 · hi_potion ×3 · equip acc_flame_amulet · equip mace_saint · big_bomb ×1 |
| B8 | gold 1500 · mega_potion ×2 · hi_ether ×1 · equip acc_wind_boots · equip armor_dragon · phoenix_feather ×2 |
| B9 | gold 2000 · mega_potion ×2 · equip acc_eagle_eye · equip staff_ruby · hi_ether ×2 · ember_crystal ×1 |
| B10 | gold 2500 · mega_potion ×2 · equip acc_shadow_amulet · old_bone ×3 · hi_ether ×2 · phoenix_feather ×2 |
| B11 | gold 3000 · elixir ×1 · equip acc_clarity_earring · abyss_crystal ×1 · mega_potion ×3 · ghost_essence ×2 · equip bow_star |
| B12 | gold 4000 · elixir ×1 · equip acc_guardian_ring · mega_potion ×3 · hi_ether ×3 · abyss_crystal ×1 |

Each biome has one "next-tier" equipment chest (bow_hunter, sword_knight, mace_saint/armor_dragon, bow_star), placed off the main path behind a trap row or a FOE.

### 8.5 Lore stones (`N`, `lore_stones` text fields in order)
| floor | texts |
|---|---|
| B1 | ① 여명의 마을 아래, 대현자 루멘은 '심연'을 가두었다. 네 개의 봉인이 그 문을 지킨다. ② 숲의 봉인은 고목에게 맡긴다. 뿌리가 땅을 붙드는 한, 심연은 오르지 못하리라. — 루멘 |
| B2 | ① 제자 모르데인이 오늘도 봉인을 살폈다. 그는 스승보다 오래 살 방법을 자주 묻곤 했다. ② 덩굴이 검게 물들고 있다. 고목의 노래가 더는 들리지 않는다. |
| B3 | ① 고목 수호자여, 그대의 뿌리에 숲의 봉인을 묶는다. 잠들지 말고 지켜라. ② 누군가 고목의 뿌리에 검은 결정을 박아 넣었다. 심연의 냄새가 난다. |
| B4 | ① 바다가 이 동굴까지 밀려왔던 시절, 크라켄 여왕은 두 번째 봉인을 품었다. ② 얼음 속에 갇힌 일지 조각: "스승님은 틀렸다. 심연은 재앙이 아니라 힘이다." — 모르데인 |
| B5 | ① 펭귄들이 얼음 위에 이상한 문양을 그린다. 누군가에게 배운 주문이다. ② 여왕의 노래는 원래 성난 바다를 잠재우는 자장가였다고 한다. |
| B6 | ① 일지: "여왕은 쉽게 꺾였다. 고독한 자일수록 속삭임에 약하다." ② 빙해 깊은 곳에서 진주가 빛난다. 봉인의 심장이다. ③ 루멘의 각인: "봉인이 셋 무너지면, 마지막 종은 울리지 않으리라." |
| B7 | ① 이 사막은 한때 태양의 신전이었다. 스핑크스는 지혜를 시험하는 문지기였다. ② 일지: "불은 정직하다. 모든 것을 태워 진실만 남긴다." |
| B8 | ① 용암 아래 묻힌 비석: "지혜 없는 힘은 스스로를 태운다." ② 드레이크들이 신전을 둥지로 삼았다. 수호자는 더 이상 그들을 막지 않는다. |
| B9 | ① 스핑크스의 수수께끼: "밤이 가장 깊을 때 오는 것은?" 바닥에 답이 긁혀 있다 — "여명". ② 일지: "스승님은 끝까지 나를 믿었다. 그래서 더 미웠다." ③ 세 번째 봉인 앞에 꺼진 등불 하나. 루멘의 것이다. |
| B10 | ① 망자의 묘소는 루멘이 잠든 곳. 마지막 봉인은 그의 무덤 그 자체다. ② 해골 병사들은 본래 묘소를 지키던 기사들이다. 지금은 누구의 명령을 듣는가. |
| B11 | ① 일지 마지막 장: "영원히 살 수 있다면, 스승님을 다시 만날 수 있을까." ② 납골당 벽의 이름들 사이, 모르데인의 이름만 긁혀 지워져 있다. ③ 혼불들이 속삭인다. "종을… 울려 줘…" |
| B12 | ① 루멘의 무덤이 열려 있다. 안은 비어 있다. ② 옥좌 앞 비문: "심연은 빼앗지 않는다. 잃은 것을 되찾게 해 주겠다고 속삭일 뿐." ③ 여명의 종을 울리는 줄이 이곳까지 내려와 있다. 그 끝은 옥좌에 묶여 있다. |

### 8.6 Boss dialogue (`boss_pre_text` before the fight, `boss_post_text` after the win)
Join each cell's quoted beats with newline characters, omitting the surrounding quotation marks and `/` separators.
| floor | intro | outro |
|---|---|---|
| B3 고목 수호자 | "…침입자인가." / "숲의 봉인을 노리는 자는 모두 뿌리 아래 잠들게 하리라." | "검은 결정이… 부서졌군. 고맙다, 여명의 아이들아." / "그자는… 바다로 내려갔다. 서둘러라." |
| B6 크라켄 여왕 | "쉿… 노래를 멈추지 마." / "그 아이가 말했어. 노래를 그치면 다시는 외롭지 않을 거라고." | "…아, 이제야 내 노래가 들려." / "모르데인… 그 아이는 울고 있었어. 태양의 신전으로 가렴." |
| B9 불꽃 스핑크스 | "답하라, 필멸자여." / "영원을 원하는 자에게 끝내 남는 것은 무엇인가?" | "…답은 '아무것도 없다'." / "그는 끝내 그 답을 듣지 않았다. 묘소로 가라. 마지막 봉인이 기다린다." |
| B12 심연의 망령술사 | "루멘의 종지기들인가. 늦었다." / "봉인 셋은 무너졌고, 마지막은 내 손 안에 있다." / "스승님도 막지 못한 것을, 너희가 막겠다고?" | "…스승님… 따뜻하군요." / "저는 그저… 다시 만나고 싶었을 뿐입니다." / "종을… 울려 주시오." |

---

## 9. Quests (`QuestData`, 12)
- `kind`: kill (count kills of `target_id`), collect (items in the bag are removed on claim), foe (defeat an elite with `target_id`), boss, explore (arrive on floor `target_id`).
- `unlock_floor` = deepest floor index required for the quest to appear at the Guild.

| id | title | description | kind | target_id | count | reward_gold | reward_items | unlock |
|---|---|---|---|---|---|---|---|---|
| q_slime_cull | 슬라임 소탕 | 유적 입구의 슬라임이 늘고 있어요. 8마리만 정리해 주세요. | kill | slime | 8 | 150 | healing_potion 3 | 0 |
| q_forest_fiber | 덩굴 섬유 납품 | 대장간에서 질긴 덩굴 섬유 4개가 필요하대요. | collect | forest_fiber | 4 | 250 | remedy 2 | 0 |
| q_toxic_king | 독왕 버섯 토벌 | 회랑을 떠도는 거대한 독버섯을 쓰러뜨려 주세요. | foe | elite_mushroom | 1 | 600 | acc_antidote_ring 1 | 1 |
| q_frost_survey | 빙결 수로 조사 | B5F 빙결의 수로까지 내려가 길을 확인해 주세요. | explore | frost_grotto_b5 | 1 | 400 | ether 3 | 3 |
| q_wolf_hunt | 서리 늑대 사냥 | 서리 늑대 10마리를 사냥해 주세요. 털가죽은 가지셔도 돼요. | kill | ice_wolf | 10 | 900 | hi_potion 3 | 4 |
| q_crab_king | 거대 집게 토벌 | 수로를 막고 있는 거대 산호 집게를 치워 주세요. | foe | elite_coral_crab | 1 | 1500 | phoenix_feather 2 | 4 |
| q_drake_scales | 드레이크 비늘 납품 | 내열 갑옷 연구에 드레이크 비늘 5장이 필요합니다. | collect | drake_scale | 5 | 2500 | mega_potion 2 | 6 |
| q_golem_breaker | 사막의 거상 토벌 | 협곡의 다리를 지키는 거상을 무너뜨려 주세요. | foe | elite_sand_golem | 1 | 4000 | ember_crystal 1 | 7 |
| q_sphinx | 태양의 수수께끼 | 태양의 제단의 스핑크스를 진정시켜 주세요. | boss | flame_sphinx | 1 | 3000 | hi_ether 3 | 8 |
| q_bone_collector | 뼈 수집가 | 묘소 기사들의 오래된 뼈 6개를 모아 주세요. 정중히 안치하겠습니다. | collect | old_bone | 6 | 3000 | elixir 1 | 9 |
| q_general | 해골 장군 토벌 | 묘소를 순찰하는 해골 장군을 쉬게 해 주세요. | foe | elite_skeleton | 1 | 4000 | abyss_crystal 1 | 9 |
| q_lament | 통곡의 납골당 정화 | 도깨비불 8개를 잠재워 납골당의 통곡을 멈춰 주세요. | kill | wisp | 8 | 4000 | abyss_crystal 1, elixir 1 | 10 |

`reward_items` may include equipment ids (only `acc_antidote_ring` does); they go to `equipment_bag`.

---

## 10. Town, shops and economy

### 10.1 Town services
- **Inn** costs `10 + 4 × average party level`, rounded. That is 14 at Lv1, 50 at Lv10, 90 at Lv20 and 154 at Lv36. Resting restores HP and MP fully, revives KO'd members, respawns FOEs and saves the game.
- **Shop tiers** unlock by deepest biome reached: tier 1 at the start, tier 2 on reaching B4, tier 3 on reaching B7, tier 4 on reaching B10. The shop sells every item and equipment with `1 ≤ shop_tier ≤ unlocked` (§5, §6). Selling is always allowed at 50 %.
- **Smithy (crafting)** offers 7 tier-5 equipment pieces plus 6 accessories (acc_antidote_ring, acc_frost_amulet, acc_flame_amulet, acc_shadow_amulet, acc_guardian_ring, acc_hero_emblem). A recipe appears once any of its materials has been owned.

| shop_tier | consumables | equipment |
|---|---|---|
| 1 | healing_potion, ether, remedy, return_stone, smoke_bomb, bomb | all T1 + T2 gear (sword_iron, staff_crystal, bow_hunter, mace_silver, armor_scale, garb_ranger, robe_silk), acc_lucky_charm, acc_antidote_ring |
| 2 | + hi_potion, phoenix_feather, power_tonic, guard_tonic | + T3 gear, acc_power_band, acc_sage_pendant, acc_awake_bell, acc_frost_amulet |
| 3 | + mega_potion, hi_ether, big_bomb | + T4 gear, acc_wind_boots, acc_flame_amulet, acc_eagle_eye |
| 4 | + elixir | + acc_clarity_earring, acc_shadow_amulet |

### 10.2 Economy math (normal difficulty, expected play)
Assumptions behind the table:
- "Battle gold" = expected random battles × average gold per group from §8.2.
- "Other" = chests + FOEs fought once on their home floor + boss + quests.
- Material sales add roughly another 5–10 % that the table does not count.

| biome | battle gold | other | total in | must-buy (×4 heroes) | buffer for consumables/accessories |
|---|---|---|---|---|---|
| Verdant (B1–B3) | ~1,800 | ~2,200 | ~4,000 | T2 weapons+armor ≈ 2,300 | ~1,600 (potions, remedies, return stones) |
| Frost (B4–B6) | ~7,200 | ~7,100 | ~14,300 | T3 set ≈ 8,260 | ~5,000 (hi_potions, frost amulets ×2–3) |
| Ember (B7–B9) | ~15,300 | ~19,600 | ~34,900 | T4 set ≈ 19,450 | ~15,000 (flame amulets ×4 = 8,000, mega_potions) |
| Crypt (B10–B12) | ~20,300 | ~24,100 (final boss gold excluded) | ~44,400 | T5 crafts ≈ 18,400 + 8 abyss crystals | ~26,000 (elixirs, shadow amulets, hero emblem) |

Why the curve works:
- Each biome's income covers its tier upgrade only after most of the biome is explored. Gear therefore lands right before each boss, so buying is a choice between gear and consumables, not an automatic purchase.
- Selling the previous tier refunds 50 %, which softens the T3 and T4 jumps.
- Losing 50 % of gold on defeat is felt but not crippling, because gear is never lost.

---

## 11. Story and text

### 11.1 Title / prologue
- Title: **심연의 미궁** (font-rendered). Subtitle: "여명의 종이 다시 울릴 때까지".
- Prologue (one line per page):
  1. 해가 뜨지 않는 날이 일곱 번째로 이어졌다.
  2. 삼백 년 동안 아침을 알려 온 '여명의 종'이 더는 울리지 않는다.
  3. 마을 아래에는 대현자 루멘이 '심연'을 가둔 미궁이 잠들어 있다.
  4. 네 개의 봉인이 흔들리고, 밤은 점점 길어지고 있다.
  5. 촌장은 마지막 희망으로 네 명의 모험가를 불러 모았다.
  6. 검을 든 검사, 원소를 다루는 마법사, 바람을 읽는 궁수, 빛을 믿는 성직자.
  7. "종이 침묵하는 이유는 저 아래에 있을 것이오. 부디… 여명을 되찾아 주시오."
  8. 횃불 하나에 의지해, 네 사람은 미궁의 첫 계단을 내려간다.

### 11.2 Town "여명의 마을" NPCs
| service | name | greeting |
|---|---|---|
| 여관 Inn | 마사 | "어서 와요. 따뜻한 수프와 침대가 있어요. 오늘 밤은 푹 쉬어요." |
| 상점 Shop | 피핀 | "미궁에 들어가기 전엔 회복약! 이건 상식이라고요." |
| 대장간 Smithy | 브론 | "재료만 가져와. 쇳덩이에 혼을 불어넣는 건 내 몫이니." |
| 길드 Guild | 리나 | "의뢰 게시판이 갱신됐어요. 보상은 확실하답니다!" |
| 촌장 Elder | 에드윈 | "종이 다시 울릴 그날까지, 이 마을은 그대들을 믿겠소." |

The elder's line after each boss (shown on the town hub once):
- After B3: "숲의 봉인이 되살아났다니! 아직 셋이 남았소."
- After B6: "바다의 노래가 들리는구려. 그대들 덕이오."
- After B9: "태양이 잠시 비쳤소. 이제 마지막 봉인뿐이오."

### 11.3 Biome intro texts (area header on the first visit to each biome's first floor)
| Biome | Header text |
|---|---|
| verdant | 제1층역 · 신록의 유적 — 이끼와 덩굴이 고대 석조를 삼켜 버린 숲의 미궁. |
| frost | 제2층역 · 빙해의 동굴 — 바다가 얼어붙은 채 시간이 멈춘 동굴. |
| ember | 제3층역 · 홍염의 사막 — 태양 신전의 잔해가 용암 속에 잠겨 있다. |
| crypt | 제4층역 · 망자의 묘소 — 대현자가 잠든 곳, 그리고 마지막 봉인. |

### 11.4 Ending (text scroll, one line per beat)
1. 망령술사의 몸이 빛 속으로 흩어졌다.
2. 옥좌에 묶여 있던 종의 줄이 스르르 풀려 하늘로 올라간다.
3. 미궁 깊은 곳에서, 네 개의 봉인이 동시에 맑은 소리를 냈다.
4. 그리고 — 삼백 년 만에, 가장 크게.
5. 여명의 종이 울렸다.
6. 마을 사람들은 지붕 위로 올라가 동쪽 하늘을 바라보았다.
7. 길고 길었던 밤의 끝에서, 해가 떠올랐다.
8. 고목은 다시 노래하고, 바다는 자장가를 되찾았으며, 태양의 제단엔 불이 켜졌다.
9. 묘소에는 이름 하나가 다시 새겨졌다. "모르데인 — 스승의 곁에 잠들다."
10. 네 모험가는 마사의 여관에서 오랜만에 늦잠을 잤다.
11. 미궁은 여전히 마을 아래에 있다. 하지만 이제, 그 문을 지키는 것은 사람들이다.
12. 심연의 미궁 — 끝.

### 11.5 Credits
| 역할 | 이름 |
|---|---|
| 게임 디자인 & 엔지니어링 | Claude |
| 아트 | ChatGPT image generation (directed) |
| 음악 · 효과음 | 절차적 생성 (Python audio generator) |
| 엔진 · 도구 | Godot 4.7 |
| 기획 감독 | 플레이어 여러분과 함께 |
| — | 플레이해 주셔서 감사합니다. |

### 11.6 One-shot tips (flags `tip_<key>`)
| key | trigger | text |
|---|---|---|
| first_battle | first battle starts | 적 이름표의 속성 아이콘을 확인하세요. 약점을 찌르면 1.5배 피해와 함께 실드가 깎이고, 실드가 0이 되면 BREAK! 적은 한 턴을 쉬고 받는 피해가 1.5배가 됩니다. |
| first_tp_full | any hero reaches 100 TP | TP가 가득 찼습니다! '오의' 명령으로 강력한 기술을 쓸 수 있어요. TP는 전투가 끝나면 사라집니다. |
| first_foe | first FOE in view | 주황색 표식은 강력한 FOE입니다. 한 걸음 움직일 때마다 그들도 움직여요. 지금은 피하는 것도 전략입니다. |
| first_trap | first trap stepped on | 함정을 밟았습니다! 파티 전원이 피해를 입고 중독될 수 있어요. 한 번 밟은 함정은 지도에 표시됩니다. |
| first_town | first arrival in town | 여관에서 쉬면 HP·MP가 회복되고 쓰러진 FOE가 되살아납니다. 상점·대장간·길드도 들러 보세요. |

---

## 12. Expected progression (normal; the sim target is D7)
| floor | arrival Lv | Lv at stairs/boss | gear tier | random battles | other battles | cumulative gold earned | typical purchases |
|---|---|---|---|---|---|---|---|
| B1 | 1 | 4 | T1 | ~14 | E | ~330 | healing_potion, remedy |
| B2 | 4 | 7 | T1 → T2 weapons | ~13 | E, FOE (opt.) | ~1,400 | T2 weapons, ether |
| B3 | 7 | **10** (boss) | T2 | ~15 | E, 2 FOE (opt.), boss | ~4,000 | T2 armor, phoenix_feather |
| B4 | 11 | 14 | T2 → T3 weapons | ~14 | E, FOE | ~6,600 | T3 weapons |
| B5 | 14 | 17 | T3 | ~14 | E, 2 FOE | ~11,500 | T3 armor, hi_potion |
| B6 | 17 | **19** (boss) | T3 + frost amulets | ~9 | E, 2 FOE, boss | ~18,300 | acc_frost_amulet, remedy stock |
| B7 | 20 | 23 | T3 → T4 weapons | ~13 | E, FOE | ~24,500 | T4 weapons |
| B8 | 23 | 26 | T4 | ~14 | E, 2 FOE | ~35,000 | T4 armor, mega_potion |
| B9 | 26 | **28** (boss) | T4 + flame amulets | ~9 | E, 2 FOE, boss | ~53,000 | acc_flame_amulet ×4 |
| B10 | 29 | 32 | T4 → T5 weapons (craft) | ~14 | E, FOE | ~65,000 | T5 weapons, shadow amulets |
| B11 | 32 | 34 | T5 weapons + T4/T5 armor | ~9 | E, 2 FOE | ~83,000 | T5 armor, elixir |
| B12 | 34 | **36** (boss) | T5 | ~9 | E, 2 FOE, boss | ~97,000 | acc_hero_emblem, elixirs |

- About 147 random battles, 12 event battles, about 10 FOE fights and 4 bosses, roughly 175 fights in total. At about 1 min per fight plus 15–20 min of exploring per floor, a run takes **≈ 6.5–8.5 h**.
- HP and MP drain per floor targets 40–60 % of the party's pools without springs. The biome's first and second floors are each expected to cost one `return_stone` trip, and the boss floor's pre-boss spring makes the boss attempt fair.
- Phase 4b B3 targets supersede the old D7 <20% rule: normal bosses at the expected level 60–85% wins / 8–14 rounds / at least 40% net MP pool spent; −3 levels 25–55%; previous progression-tier gear at most 35%; hard expected-level bosses 35–60%. Random encounters at floor-arrival level: at least 97% wins / 3–6 rounds. FOEs: 35–65% at floor-arrival level, at least 85% at +4. Campaign (10 fixed seeds, normal): at least 7 clear B3 and 5 clear B6; boss arrival levels within ±2 of 10/19/28/36. See `BALANCE_REPORT.md` for measured misses, not assumed compliance.

### 12.1 Phase 4b T27 numeric revision
- Hero skills, growth and learnsets, difficulty multipliers, equipment, enemy HP, phases, shields and encounter rates are unchanged.
- Boss ATK/MAG: forest_guardian 86/83 → 101/97; flame_sphinx 120/115 → 138/132; boss 156/166 → 203/216. Frost kraken remains 137/130.
- Verdant normal XP/gold: slime 9/8 → 12/13; sprout 12/10 → 16/16; mushroom 38/18 → 49/29; bat 50/20 → 65/32. Verdant elite XP/gold: elite_mushroom 300/150 → 390/225; elite_bat 450/220 → 585/330.
- Ember normal XP: magma_slime 240 → 312; sand_golem 310 → 403; phoenix 320 → 416; fire_drake 370 → 481.
- Crypt XP: skeleton 400 → 240; grave_bat 410 → 246; scarecrow 470 → 282; wisp 520 → 312; elite_skeleton 4000 → 2400; elite_scarecrow 5000 → 3000.
- The tables in §7 are authoritative; generators regenerate `data/enemies/` and `tests/t17c/expected_units.json` from them. Normal HP and elite-strength trial overrides were not shipped: priority is campaign progression. Hard-boss, under-level, random-duration and FOE targets remain measured open items.

### 12.2 Phase 4b T28 numeric revision
- Targets revised by main (T28 D1): random encounters at the floor-arrival level average **2.0–4.0 rounds per biome** (no biome below 1.8) with at least 97 % wins; this replaces the 3–6 rounds of §12. FOE (D2) and hard-boss (D3) targets are unchanged.
- Normal-enemy HP per biome (the D1 lever; ATK/MAG unchanged, rounded to 5): verdant ×1.8 (slime 50 → 90, sprout 60 → 110, mushroom 90 → 160, bat 80 → 145); frost ×1.6 (jellyfish 130 → 210, coral_crab 140 → 225, penguin_mage 150 → 240, ice_wolf 165 → 265); ember ×2.0 (magma_slime 190 → 380, sand_golem 255 → 510, phoenix 215 → 430, fire_drake 270 → 540); crypt ×2.4 (skeleton 260 → 625, grave_bat 240 → 575, scarecrow 340 → 815, wisp 300 → 720).
- `boss` HP 7225 → 5600: its phase summons are skeletons and wisps, whose ×2.4 HP had cut the B12 normal win rate to 44 %.
- Verdant normal gold ×1.5 (slime 13 → 20, sprout 16 → 24, mushroom 29 → 44, bat 32 → 48): with FOEs no longer free gold, the campaign reached B3 with too few potions and armour pieces.
- FOE `power` per FOE (§8.3) and the hard boss overrides (§1.5) are new. Elite base stats are unchanged (elites also appear elsewhere).
- Measured results and remaining misses are in `BALANCE_REPORT.md`.

## Implementation notes
- **T17: main has approved §0's additive schema fields and §1's formulas**, and has sent their implementation to T11/T12/T13. Treat these as approved contracts, not requests for further design. Preserve existing resource fields and numeric enum values.
- Shared-contract R8 paths and ids are binding; use §8.0 verbatim. T13 owns dungeon resources, so T17 consumes their ids without renaming or overwriting those files.
- `MANA_SHIELD` and `INVINCIBLE` exist after `SPEED_UP` in the status enum (shared-contract R6), but **have no status resources or skill references in this phase's content**.
- Author exactly **48 equipment resources**: 20 weapons + 15 armors + 13 accessories. Names are literal strings in §6.1–6.3; descriptions are literal strings in §6.3–6.4. Author status names/descriptions verbatim from §4–4.1 and skill names/descriptions verbatim from §3.1–3.2. Do not invent renamed or numerically altered variants.
- These corrections clarify authoring, copy and shared-contract names only; all combat, economy, progression and content numbers remain unchanged.
