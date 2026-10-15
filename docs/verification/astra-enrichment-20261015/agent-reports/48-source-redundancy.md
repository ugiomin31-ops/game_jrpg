# 48-source-redundancy

- 작업: Tools / Blender / ArtSource의 레거시 생성기와 제작 출처를 구분하는 제한적 읽기 전용 감사.
- 확인한 브랜치: `codex/astra-enrichment-20261015`.
- 확인한 HEAD: `efdc1517f48ac8887e1fcf6843b6df44df6ebc3c` (요청 base 일치).
- 요청 모델/effort: `gpt-6-astra` / `high`. 요청 서비스: Fast/priority. 실제 모델·effort·서비스 tier를 독립 검증할 실행 메타데이터는 제공되지 않았으므로 요청값을 관측값으로 주장하지 않는다. 모델/설정 변경 및 하위 에이전트 생성 없음.

## 결과

**확정 발견 0건. 근거가 충분한 삭제 후보 없음.** 이는 전체 저장소의 무결성 또는 모든 파일의 필요성을 보증하는 결론이 아니라, 아래 범위에서 삭제를 정당화할 증거가 없다는 뜻이다.

## 보존 판정 근거

| 범위 | 확인한 근거 | 판정 |
|---|---|---|
| Blender의 구형 적 생성기·공용 도구 | `Blender/README.md:3-4`는 생성기 자체를 제작 원본으로 기록한다. `Blender/enemies_a/generate_all.py:21,39,46,50,54`는 v2~v5 레시피를 통합하고 `:122`에서 선택된 원본 스크립트를 찾는다. `Blender/lib/abyss_bpy.py:492`, `Blender/hunters_tripo/common.py:172`는 공통 Tripo 덮어쓰기 보호를 사용한다. | 버전명이나 새 Tripo 모델의 존재만으로 이전 폴더 및 공용 코드를 미사용으로 분류할 수 없다. 현재 생성 허용 정책과 과거 제작 원본의 보존 가치는 구분해야 한다. |
| Tools의 이미지 제작 스크립트와 출처 | `Tools/vfx/gen_textures.py:31,34`는 painted 원본 폴더와 `asset_import`를 참조한다. `:222-223,352`는 ChatGPT 원본을 변환하는 경로와 기존 절차 방식의 대체 경로를 함께 보존한다. `Tools/vfx/painted/SOURCE.md:3-5`도 변환 역할을 명시한다. `Tools/ui/gen_ui_sprites.py:11-15`는 공용 importer와 UI 출력·border manifest 경로를 갖고, `Blender/README.md:51`에 제작 진입점으로 기록되어 있다. | 스크립트 전체를 단순 폐기 대상 생성기로 판정할 수 없다. 실제 사용 여부의 전면 검증 없이 삭제 후보로 제시하지 않는다. 이 감사에서 생성기를 실행하지 않았다. |
| ArtSource 원본·후보·sidecar·보관 기록 | `ArtSource/_handoff_pr8_20261014/README.md:3,14`는 출처 보존 목적과 다운로드·텍스처·이미지 후보·motion archive·sidecar를 포함한 보관 범위를 기록한다. `:34`는 다운로드 원본 보존을 명시한다. | 런타임에 직접 로드되지 않아도 제작 출처이므로 삭제 후보에서 제외한다. 문서에 적힌 외부 백업 존재·복구 가능성을 이번 감사에서 검증한 것은 아니다. |

Tools 전체가 불필요하다는 주장도 성립하지 않는다. `.github/workflows/phone-build.yml:125`는 `Tools/web/patch_index.py`, `.github/workflows/logic-check.yml:18`은 `Tools/logic_test.py`를 호출한다. 호출 관계만 확인했으며 실행하지 않았다.

## 수락 체크

- [x] 지정 checkout 및 base 확인.
- [x] 지정 디렉터리 파일 목록과 관련 문서·생성기·직접 호출 관계만 확인; Library 및 광범위 저장소 내용 검색 없음.
- [x] 테스트·빌드·Unity·브라우저·네트워크·인증정보 접근·게임 소스 수정 없음.
- [x] 삭제 후보는 근거 부족으로 0건; 이 보고서만 작성. 통합 및 후속 변경은 주 조정자 소관.
