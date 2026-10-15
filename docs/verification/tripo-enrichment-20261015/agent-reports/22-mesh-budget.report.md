읽기 전용 점검 결과, **현재 설치 FBX의 삼각형 예산 준수를 확정할 증거가 부족합니다.** 파일 크기로 삼각형 수를 추정하지 않았습니다.

1. **P1 — 기존 삼각형 보고서가 현재 설치 파일을 충분히 증명하지 못합니다.**  
   [asset-audit.json](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/docs/verification/asset-audit.json:1)은 적 **51/87개**, Props **106/141개**만 경로가 대응합니다. 적 36개·Props 35개는 이 보고서에 없습니다. 보고서에는 파일 해시·측정 시각 필드도 없어, 대응하는 행 역시 현재 바이너리의 측정값이라고 확정할 수 없습니다.

2. **P1 — 예산 초과 기록은 재측정 우선 대상입니다. 현재 초과로 단정하지 않습니다.**

   | 설치 FBX | 현재 크기(bytes) | 기존 보고서 삼각형 수 | 적용 상한 |
   |---|---:|---:|---:|
   | forest_guardian | 8,546,236 | 26,316 | 20,000 |
   | frost_kraken | 3,973,132 | 23,724 | 20,000 |
   | boss | 2,511,116 | 27,530 | 20,000 |
   | flame_sphinx | 2,606,684 | 28,504 | 20,000 |
   | Props/Equipment/armor_chain | 244,908 | 13,220 | 6,000 |
   | Props/Equipment/armor_dragon | 140,492 | 7,016 | 6,000 |
   | Props/Equipment/armor_scale | 119,164 | 6,108 | 6,000 |

   보고서 근거: [적 기록](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/docs/verification/asset-audit.json:62) 및 같은 파일 1390·1527·1654행, [프롭 기록](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/docs/verification/asset-audit.json:44) 및 803·1479행.  
   특히 forest_guardian은 [Tripo 기록 16행](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/enemies/forest_guardian/candidates/prompts.md:16)에 Triangle **19,270 faces**라고 적혀 있어 보고서와 다릅니다. 서로 다른 버전일 가능성을 현재 증거로 해소할 수 없습니다.

3. **P2 — 최신 소품의 Quad 면 수는 삼각형 예산 검증값이 아닙니다.**  
   [aid_kit](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/props/aid_kit/tripo/SOURCE.md:9)은 **Quad 3,420 faces**, [gate_keycard](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/props/gate_keycard/tripo/SOURCE.md:9)는 **Quad 1,777 faces**만 기록되어 있습니다. 설치 후 삼각형 수와 필수 Triangle Retopo 완료 증거가 필요합니다. [riot_shield](/C:/Users/User/Desktop/GAME_JRPG/game_jrpg-pr9/ArtSource/props/riot_shield/tripo/SOURCE.md:10)는 Triangle Retopo **3,674 faces** 기록이 있지만 설치 파일과의 연결 검증은 별도입니다. 현재 `Vfx/Meshes`의 aid_kit은 **218,044 bytes**, riot_shield는 **124,156 bytes**입니다.

크기 집계는 `Assets/_Game/Resources/Art/Enemies` **87개 / 149,613,140 bytes**, `Art/Props` **141개 / 4,890,604 bytes**입니다. 환경·무기 전체는 범위에 포함하지 않았습니다.

**정확한 다음 조치:** 부모가 별도 검증 단계에서 위 초과 기록 7개와 소품 3개의 현재 설치 메시를 먼저 측정하고, `경로·SHA-256·측정 시각·실제 삼각형 수·분류별 상한`을 함께 기록해야 합니다. 이어 기존 보고서 미포함 71개를 보완하면 됩니다. 원본 Tripo 수치와 설치 후 수치는 구분해야 합니다.

체크리스트: 파일 크기 확인·보고서 대응 비교·증거 공백 식별 완료. 파일 변경, 자식 실행, Blender·Unity·테스트·브라우저 실행은 하지 않았으며 새 런타임 검증을 주장하지 않습니다.