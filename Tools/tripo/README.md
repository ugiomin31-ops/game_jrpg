# Tripo 자산 파이프라인

마을 오브젝트·미궁 맵 오브젝트·스킬 이펙트 메시를 Tripo로 만들어 이 프로젝트의 정적 에셋 규약([Blender/README.md](../../Blender/README.md))에 맞춰 넣는 도구다.

```
assets.json ──candidates──▶ 후보 이미지 4장 ──pick──▶ 1장 선택 ──model──▶ model.glb ──convert.py──▶ FBX (Assets/_Game/Resources/Art/...)
```

## 준비

- Tripo API 키(`tsk_`로 시작)를 환경 변수 `TRIPO_API_KEY`로 둔다. 키는 저장소나 채팅에 남기지 않는다.
- API 주소는 `https://openapi.tripo3d.ai/v3`(Tripo 공식 Python SDK `tripo3d` 1.0.0 기준). 다르면 `TRIPO_BASE_URL`로 바꾼다.
- 클라우드 세션에서 돌릴 때는 네트워크 허용 목록에 `openapi.tripo3d.ai`와 결과 파일 저장소 호스트가 있어야 한다.
- 스크립트는 표준 라이브러리만 쓴다. 변환은 Blender(4.2 이상, 5.0에서 시험)로 한다.

## 실행

```
python Tools/tripo/tripo_run.py candidates --all            # 자산마다 후보 4장 (text-to-image)
python Tools/tripo/tripo_run.py pick town_fountain 3 --why "실루엣이 가장 선명"
python Tools/tripo/tripo_run.py model --all                 # 고른 이미지로 image-to-model
python Tools/tripo/tripo_run.py status
blender -b --factory-startup -P Blender/tripo/convert.py    # GLB → 규약 FBX + 미리보기
```

- 후보 이미지를 다른 도구로 만들었다면 `model <id> --image 경로`로 그 이미지를 바로 쓴다.
- image-to-model 버전은 `--model-version`(기본 `v3.1-20260211`, 환경 변수 `TRIPO_MODEL_VERSION`)으로 바꾼다. 서버가 거부하면 오류 메시지에 나온 유효 버전으로 다시 실행한다.
- 결과는 `Blender/tripo/source/<id>/`에 남는다: `candidates/cand_1..4`, `model.glb`, Tripo 렌더, `state.json`(프롬프트·task id·선택 이유·변환 보고).

## 변환 규칙 (`Blender/tripo/convert.py`)

| 항목 | 처리 |
|---|---|
| 메시 | 가져온 메시를 하나로 합치고 이름을 자산 id로. 아마추어·Empty 제거 |
| 폴리곤 | UV 이음매로 갈라진 정점을 붙인 뒤 `tri_budget`까지 collapse decimate |
| 색 | 베이스 컬러 텍스처를 면마다 샘플링해 `Col`(sRGB, 면 코너)에 면 하나 한 색으로 굽고 UV·이미지·glTF 머티리얼 제거 |
| 머티리얼 | `M_Toon`/`M_Emit`/`M_Clear`만. 자산의 `emit_material`(기본 M_Toon)을 쓰고, `emit_hint`가 있으면 밝고 채도 높은 면을 `M_Emit`으로 |
| 크기·방향 | 높이를 `height_m`으로 맞추고 원점은 바닥 중앙(z=0). 정면 -Y. Tripo가 다른 방향을 보면 자산에 `rot_z_deg`를 넣는다 |
| 출력 | `Assets/_Game/Resources/Art/<out>`, `Blender/preview/tripo_<id>.png`, `Blender/blend/tripo_<id>.blend` |

## 자산 목록

`assets.json`에 14종: 마을 6(분수·노점·대장간·의뢰 게시판·가로등·통/상자), 바이옴 맵 오브젝트 4, 스킬 이펙트 메시 4. 각 자산은 서로 다른 디자인 방향의 후보 프롬프트 4개와 그룹 공통 스타일 문구를 가진다.

출력 경로는 기존 절차적 에셋을 덮어쓰지 않는 새 경로다. 마을 배치(`Blender/town/town.py`), 미궁 장식 슬롯, 스킬 이펙트(`Resources/Vfx/effects.json`, 현재 메시 레이어 없음)에 연결하는 일은 모델을 검수한 뒤 따로 한다.
