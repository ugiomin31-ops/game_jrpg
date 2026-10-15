# Package consistency — report56 반영

- 요청 모델/effort: gpt-6-astra / high, Fast/priority 요청. 실제 실행 모델·effort·tier는 독립 확인할 런타임 메타데이터가 없어 검증된 값으로 주장하지 않는다.
- 브랜치 codex/astra-enrichment-20261015, 확인한 HEAD efdc1517f48ac8887e1fcf6843b6df44df6ebc3c.

## 정확한 변경

- Packages/manifest.json:40 — com.unity.nuget.newtonsoft-json: 3.2.1 → 3.2.2.
- Packages/packages-lock.json:75 — 같은 항목의 depth: 1 → 0. 잠금 버전 3.2.2, source registry, 빈 dependencies, Unity registry URL은 그대로다.

## 호환성 판단 범위

- 이미 체크인된 lock이 선택한 3.2.2에 직접 선언을 맞췄다. 잠금 버전이나 패키지 바이너리를 새 버전으로 교체하지 않았다. 설치된 실제 패키지 버전이 검증됐다는 뜻은 아니다.
- 유일한 간접 요구는 com.unity.pipeline의 Newtonsoft 3.0.2이며, 선택된 동일 major의 3.2.2는 이 요구보다 높다. 해당 간접 요구 문자열은 보존했다. Newtonsoft 자체 잠금 항목은 추가 의존성이 없다. 기존 잠금 그래프에서 새 버전 충돌을 추가하지 않는 정적 일관성 수정이다.
- ProjectSettings/ProjectVersion.txt의 Editor 핀은 6000.3.25f1이다. SaveCodec.cs:6-9,43-50과 GameData.cs:6-8은 기존 Newtonsoft.Json API를 사용하며 이 작업은 소스/API를 바꾸지 않는다.
- 정확한 로컬 경로 Library/PackageCache/com.unity.nuget.newtonsoft-json@3.2.2/package.json 및 Library/PackageManager/PackageInfo.json에는 읽을 메타데이터가 없었다. Library 검색, 다운로드, 설치를 수행하지 않았다. 패키지 최소 Editor 버전, 실제 Editor import/API 호환성은 이번 작업에서 독립 증명하지 않았으며 부모의 정상 resolve/검증 대상이다.

## 보존 확인

- JSON 파싱 및 전후 값 대조: 위 두 필드만 변경됐다. 다른 모든 패키지 선언/잠금 항목/의존성 간선은 동일하다.
- 수정 후 직접 의존성 43개 모두 lock의 동일 버전·depth 0과 일치한다. 불일치 0개.
- 바이트 치환만 사용했다. 역치환 결과가 원본과 정확히 같아 다른 바이트, 서식, 줄바꿈, BOM/마지막 줄바꿈이 보존됨을 확인했다. 저장 후 바이트 재읽기도 일치했다.

| 파일 | 수정 전 SHA-256 | 수정 후 SHA-256 |
|---|---|---|
| Packages/manifest.json | c32e25689ade4055b1947a2a05d614e728628a1a37495f3b93fd952f6806b5b0 | 7c5448e248ca53e5c987d1388840c9823401943ede0b67ea1785b51919a4ea79 |
| Packages/packages-lock.json | b0a79fffc33df42dd4bc21e986d68470b209da6038a48e444486fb97b4fce4b2 | bf849eaf9a38040648f636ea2d6cb739a06cbabef8cb2e0d378ac54e20c32ef9 |

패키지 설치·resolve·Unity·빌드·테스트·브라우저·네트워크·커밋은 실행하지 않았다. 전역/사용자 설정도 변경하지 않았다. 실제 resolve와 런타임 검증은 부모 조정자가 수행한다.
