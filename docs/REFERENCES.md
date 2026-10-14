# 참고 자료와 무료 에셋 출처 (2026-10-07 조사)

몬스터·캐릭터·스킬 연출을 개선할 때 확인한 자료입니다. **라이선스는 각 페이지에서 다시 확인**한 뒤 사용하고,
가져온 파일은 `Blender/third_party/<출처>/`에 원본 라이선스 파일과 README(출처 URL, 사용처)를 함께 둡니다.

## 1. 실제로 쓸 수 있는 무료 에셋 (상업 이용 가능)

| 출처 | 내용 | 라이선스 | 이 프로젝트에서의 판단 |
|---|---|---|---|
| [Quaternius — Ultimate Monsters](https://quaternius.com/packs/ultimatemonsters.html) | 리깅·애니메이션된 몬스터 50종 (FBX/OBJ/Blend/glTF) | CC0 | 이미 일부(`Blender/third_party/quaternius_ultimate_monsters/`) 보유. 둥근 몸에 큰 눈이 붙은 스타일이라 **현재 아트 방향(영웅과 같은 입체감, 자연스러운 눈)과 맞지 않아** 몬스터 본체로는 쓰지 않음 |
| [Quaternius — Textured Cute Monster Pack (OpenGameArt)](https://opengameart.org/content/textured-cute-monster-pack) | 텍스처·애니메이션 몬스터 21종 | CC0 | 같은 이유로 보류 |
| [OpenGameArt — 3D Wolf](https://opengameart.org/content/3d-wolf) | 리깅된 늑대 (FBX/Blend, 애니메이션 없음) | CC0 | 비율 참고용. 애니메이션이 없어 직접 사용 이득 적음 |
| [Kenney — Particle Pack](https://kenney.nl/assets/particle-pack) | 파티클 텍스처 80장 | CC0 | 스킬 이펙트 보조 텍스처 후보. 단, 우리 VFX 셰이더(`Tools/vfx/gen_textures.py`)는 알파를 3단 플래토로 해석하므로 그대로 넣으면 셀 셰이딩이 깨짐 → 알파를 플래토로 재가공해야 함 |
| [Brackeys VFX Bundle](https://brackeysgames.itch.io/brackeys-vfx-bundle) | Kenney·Picster·Thomas Iché·CodeManu의 파티클·플립북·스프라이트시트 모음 | CC0 | 플립북(폭발·연기·전격) 참고/가공 후보. 위와 같은 알파 재가공 필요 |
| [PVFX Foundry Thirteen](https://nerijs.itch.io/pvfx-foundry-thirteen) | 96×96 2D 전투 이펙트(참격·충격·냉기 등) | CC0 | 3D 전투에는 해상도가 낮음. 아이콘/UI 연출 참고용 |
| [Poly Haven](https://polyhaven.com), [ambientCG](https://ambientcg.com) | HDRI·재질 텍스처 | CC0 | 마을/미궁 환경 재질 개선 때 후보 |

### 사용자가 Unity에서 직접 받을 수 있는 공식 무료 에셋
- Unity Asset Store의 **Dungeon Mason "RPG Monster" 시리즈** 중 무료로 공개된 팩(예: *RPG Monster Duo PBR Polyart*)은
  JRPG풍 몬스터 품질의 좋은 기준입니다. Asset Store 계정이 필요하므로 이 저장소의 자동 제작 파이프라인에서는 받지 않았습니다.
  Unity 에디터의 Package Manager → My Assets에서 직접 추가해야 하며, Asset Store EULA상 원본 파일을 저장소에 재배포하지 않도록 주의합니다.
- 검색 결과에 섞여 나오는 유료 에셋 "무료 다운로드" 사이트(예: unityassetcollection 류)는 **불법 배포**이므로 사용하지 않습니다.

## 2. 렌더링·셰이더 참고 (GitHub)

| 저장소 | 라이선스 | 참고할 점 |
|---|---|---|
| [UniToon](https://github.com/WondermSwift/UniToon) | MIT | VRM 아바타용 범용 툰 셰이더. 그림자 색·림라이트 설정을 `Assets/_Game/Shaders/AbyssToon.shader`와 비교 |
| [UnityURPToonLitShaderExample](https://github.com/ZorroYanBo/UnityURPToonLitShaderExample) | MIT | 짧고 읽기 쉬운 URP 툰 셰이더 예제 (외곽선, 램프) |
| [BotW-ToonShader](https://github.com/ciro-unity/BotW-ToonShader) | (저장소 확인) | Shader Graph 기반 셀 셰이딩 레퍼런스 |
| Unity-Chan Toon Shader (UTS) | Unity-Chan 라이선스 | 애니메 캐릭터용 다단 그림자·하이라이트. 라이선스 조건이 따로 있으므로 코드 복사 대신 개념만 참고 |

## 3. 디자인 참고 (게임)

- **세계수의 미궁(Etrian Odyssey)**: 1인칭 격자 미궁 + FOE + 클래스별 스킬 트리. 스킬 포인트가 부족해 선택이 강제되는 구조,
  서브클래스, 스킬 재분배(레벨 페널티)가 이 게임의 미궁·FOE 구조와 가장 가까운 레퍼런스입니다
  ([GiantBomb](https://www.giantbomb.com/games/3030-14350/), [RPGamer EO3 리뷰](https://rpgamer.com/review/etrian-odyssey-iii-the-drowned-city-review/)).
- **옥토패스 트래블러**: 약점 공격 → 실드 → 브레이크 구조(이미 채택). 브레이크 순간의 연출(정지·화면 플래시·숫자 강조)이 참고 포인트.
- 몬스터 디자인은 "영웅과 같은 재질감"이 원칙: 한 덩어리로 이어진 몸, 종에 맞는 해부 구조(가슴·허리·관절), 작고 자연스러운 눈,
  털·깃털은 덩어리(클럼프)로 조형. 자세한 규칙은 [Blender 안내](../Blender/README.md)의 아트 디렉션.

## 4. 결론 (이번 작업에서 택한 방법)

무료 CC0 몬스터 중 영웅과 톤이 맞는 고품질 리깅 모델은 찾지 못했습니다. 그래서 몬스터는 **조각식 제작 키트**
(`Blender/enemies_d/sculpt_kit.py`)로 다시 만들었습니다. 여러 덩어리를 하나의 연속된 표면으로 융합하고, 부드러운 스킨 웨이트,
Cycles로 구운 앰비언트 오클루전, 소켓에 박힌 실제 안구를 사용합니다. 위의 CC0 파티클/VFX 자료는 스킬 연출 개선 때
알파 재가공을 거쳐 쓰는 것을 다음 단계로 남깁니다.
