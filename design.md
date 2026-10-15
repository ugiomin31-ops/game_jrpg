# 심연의 게이트: 헌터 길드 경험

2026-10-09. Visual contract for PR #6 improvements. Native Unity UI, existing UGUI kit.

## Intent
Help Korean-speaking players understand where to go, whether their party is ready, and what a battle command will do. Preserve the 20 hunters, four active slots, reserve, 12 zones plus red gate, and existing 3D art. The world should remain the dominant visual region.

## Hierarchy and layout
- Title: game identity, one clear primary start/continue action, subordinate settings and credits. Retain dusk urban background.
- Guild: current objective and zone top-left; compact departure readiness and primary dispatch action; supporting facilities to the right; four party members in a slim lower region. Avoid covering the central scene with a dashboard.
- Roster: selected hunter identity and role, outgoing/incoming level and effective HP/MP/equipment comparison; selection persists when returning from details. Only town permits roster mutation.
- Battle: turn context at top, battle arena middle, party status below, command menu right. Persistent action name/cost/element during targeting. Unknown enemy weaknesses remain unknown. First target pointer click previews; explicit subsequent confirmation commits once. Keyboard focus/confirm behavior must remain coherent.
- Every change maps parent RectTransforms, anchors, reserved heights, safe area and children together. Dynamic paragraphs scroll within bounded panels rather than overflow over controls.

## Tokens and art direction
- Surfaces: slate/navy #101C28 and #192B38; selected #244551; foreground #EDF5F6; secondary #B6C8CF; primary cyan #59D6CC; warning amber #F4BB68; negative #F47D85; positive #7DDFB1.
- Preserve semantic HP/MP/TP, element and rarity distinctions. Existing Gold-named legacy accent slots may be mapped to cyan consistently; rarity gold must remain gold. No blanket material/3D lighting changes.
- Existing Korean body/title fonts remain authoritative. Title hierarchy 64-88 canvas units, section headings 28-34, body 23-27, minor text >=20 where practical. Existing kit font choices and TMP fallback retained.
- Spacing scale: 8, 12, 16, 24, 32, 48; maintain authored 1920x1080 and compact 1600x900 reference canvas. Reuse existing component tokens.
- Restrained flat fills and one accent rule; limited panel ornament. Do not introduce generic web cards or fabricated player metrics.
- Existing icon/portrait artwork used for every hunter and action. Bitmap composition reference is a mockup, not proof of implemented visuals.

## States and accessibility
Selected, hovered, pressed, disabled and keyboard focus must remain distinct with text reasons where disabled. Empty reserve/scout and unavailable save states are explicit. Readiness is advisory, never an unexplained progression lock. Dead/low-resource hunters show text, not color alone. Confirmation can be cancelled without changing game state or RNG. Reduced-motion preferences remain effective.

## Responsive/native verification
Supported landscape: 1280x720, 1920x1080, 1024x768, 1440-wide and compact 915x412. User default browser widths 390/768/1280/1440 apply to browser work; for this native landscape game 390/768 height equivalents are checked where feasible. Portrait support must not be falsely claimed. Check panel bounds and overlap, long Korean names, long item/skill names, big currency values, safe areas, focus and readable text.

## Proof
Capture baseline and after title/guild/roster/battle at matching resolutions. Exercise real input and resource changes; inspect actual Unity console/player log. Regression tests prove logic only. A generated reference, successful compile or old screenshot cannot satisfy visual acceptance.

## Final targeting header constraints (2026-10-10)
The command header reserves 88 canvas units (previous54 plus34). Menu parent height and row top inset increase by the same34, so command row capacity and bottom navigation remain unchanged. Noncompact keyboard hints move down34 with the rows. Targeting uses action/cost on the first line and target rule on the next. Header autosizes between20 and existing29/30; bounded ellipsis handles extreme names, while the scrollable description retains full action/cost/element text. This local change applies only to BattleHUD. Facility panel uses the existing compact500-unit width at every supported landscape size, preserving224-unit icon buttons and central scene space.

Compact battle refinement (2026-10-10): three visible choices per page reserve the top auto/speed controls, two-line action heading and lower party strip while preserving >=44-screen-pixel touch targets. All choices remain accessible through explicit paging; larger landscape canvases retain four touch or six desktop rows.

## Map marker contrast (2026-10-15)
In the full map and HUD minimap, `W/H/R/B/E/X` tiles use the existing `UITheme.SurfaceRaised` (#192B38) fill so their existing bright semantic symbols remain distinct and match the legend. Keep symbol geometry, legend, layout, player/FOE rendering and fog/spent-marker rules unchanged. Compare actual before/after map captures at 1280x720 and 915x412 before visual acceptance.
