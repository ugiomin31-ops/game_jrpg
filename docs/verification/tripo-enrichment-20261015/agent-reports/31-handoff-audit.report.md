**읽기 전용 감사 완료. 현재 상태는 새 브랜치로 인계 가능하지만, `elite_mushroom` 새 원본은 아직 로컬에 없습니다.** 스테이징·커밋·푸시·파일 수정·Unity 실행은 하지 않았습니다.

| 경로 | Git 추적 파일 / 바이트 | 추가로 필요한 파일 |
|---|---:|---|
| Assets | 5,271 / 1,083,029,659 | `.meta` 27개 / 545,487바이트 |
| Packages | 2 / 14,816 | 없음 |
| ProjectSettings | 25 / 60,785 | 기존 변경 2개 포함 필요 |
| Blender | 2,073 / 686,282,895 | 없음 |
| Tools | 94 / 1,666,530 | 28개 / 274,246바이트 |

- **런타임 FBX:** Assets의 670개 모두 추적됨. 무시되거나 미추적된 FBX는 **0개**. 추가할 메타는 `Characters/*/*_moves.fbx.meta` 15개와 `HumanoidAnimations/*.fbx.meta` 12개입니다.
- **메타 검사:** Assets 내 실제 누락 `.meta` 0개, 본체 없는 `.meta` 0개. 검사 대상 경로의 추적 파일 중 디스크에서 사라진 파일도 0개.
- **100MiB 초과:** 검사한 8개 경로에서 0개. 이번 추가 파일 때문에 대용량 분할이나 LFS를 도입할 필요는 없습니다.
- **패키지:** manifest와 lock 모두 추적됨. `file:` 의존성 및 절대경로 로컬 패키지 의존성 0개. Unity 버전은 **6000.3.25f1**.

**반드시 강제 포함할 연속 작업 자료**

| 경로 | 현재 파일 수 / 용량 | 상태 |
|---|---:|---|
| `ArtSource/enemies/elite_mushroom/` | 9 / 6,340,029바이트 | 후보 4장·설정·기록만 존재 |
| `ArtSource/hunters/_anim_library/tripo_spell_20261015/` | 10 / 4,061,093바이트 | ZIP·원본 FBX·검증 결과·거절 사유 존재 |

`elite_mushroom/enrichment_20261015/SOURCE.md`는 **Studio 리깅 완료, export/Blender 검증 대기** 상태입니다. 기존 런타임 `elite_mushroom.fbx`는 있지만, 이것을 새 결과로 간주하면 안 됩니다. 부모 세션에서 새 export를 받으면 같은 ArtSource 아래 원본 그대로 추가하고 다시 확인해야 합니다.

**제외 규칙과 불필요한 파일**

- `.gitignore:116`의 `/ArtSource/**`가 Markdown 외 자료를 제외합니다. 다만 **이미 추적된 ArtSource 246개는 계속 포함**됩니다.
- `core.excludesfile` 명시 설정 없음. 기본 전역 파일 `C:\Users\User\.config\git\ignore`에는 `**/.claude/settings.local.json`만 있습니다. `.git/info/exclude`는 주석뿐입니다.
- Tools에서 제외된 10개, 320,551바이트는 모두 Python 캐시입니다.
- Library·Temp·빌드 결과·로그·UserSettings는 재생성/개인 상태입니다. **Logs 6개와 UserSettings 4개가 이미 추적 중**이므로 `git add -A`는 변경된 개인 상태까지 담습니다. 이번 인계에서는 해당 변경을 제외하고, 추적 해제 작업으로 범위를 넓히지 마세요.
- 별도 제외 자료로 `ArtSource/hunter-bosses/crystal_cave_lord/`의 이미지 5개, 12,617,906바이트가 있습니다. 이번 필수 범위 밖이며 기존 릴리스에 들어 있는지는 미검증입니다.

부모 세션용 명령입니다. **아래 명령은 실행하지 않았습니다.**

```powershell
git switch -c handoff/pr9-20261015

git add -- Assets Packages ProjectSettings Blender Tools
git add -- docs/verification/floor1 docs/verification/pr9_review docs/verification/tripo-motion-20261015
git add -- plan/2026-10-15-tripo-enrichment.md plan/2026-10-15-tripo-motion-vfx.md

git add -f -- ArtSource/enemies/elite_mushroom
git add -f -- ArtSource/hunters/_anim_library/tripo_spell_20261015

git diff --cached --stat
git diff --cached --name-only -- Logs UserSettings Library Temp
git ls-files --others --exclude-standard -- Assets Packages ProjectSettings Blender Tools
git ls-files --others --ignored --exclude-standard -- ArtSource/enemies/elite_mushroom ArtSource/hunters/_anim_library/tripo_spell_20261015
```

마지막 세 검사 출력은 비어야 합니다. Tools의 painted 텍스처 7장과 `SOURCE.md`, 새 테스트·검증 스크립트도 위 명령에 포함됩니다.

다른 PC에서는 Unity 6000.3.25f1과 Python을 준비하세요. `Tools/logic_test.py:16`의 Unity 경로는 `ABYSS_UNITY_DATA`로 변경할 수 있고 .NET SDK 8+ 대체 경로도 있습니다. Blender 실행 경로와 구형 smoke/save-sandbox 스크립트의 사용자 절대경로는 재실행 전 조정해야 합니다.

과거 전체 백업은 `TRANSFER_BACKUP.md`에 `full-folder-snapshot-20261006`으로 기록돼 있습니다. 메모리에도 검증 이력이 있지만 **현재 원격 상태와 이번 ArtSource 포함 여부는 확인하지 않았으므로 최신 작업의 대체 백업으로 간주하지 마세요.**

