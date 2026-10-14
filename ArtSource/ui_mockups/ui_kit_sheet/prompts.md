# ui_kit_sheet — ChatGPT web mock-up

Model check (before prompt): model menu `GPT-6` aria-checked=true; reasoning slider aria-valuenow=3, max=4 (Extra High). New chat.
Chat URL: https://chatgpt.com/c/6acc4264-4218-83ee-92e2-7d2c1eedbabc
Source: ArtSource/_briefs/floor1_polish.md, W3 "Mock-ups first" (common lead + screen 8 `ui_kit_sheet`).

## Exact prompt (one request, 4 images)

Generate FOUR separate standalone images… Original game UI mock-up for a modern Korean urban-fantasy hunter RPG on a landscape phone (20:9). Stylish, high-contrast, kinetic layout inspired by modern JRPG menu design principles (asymmetric diagonal composition, bold parallelogram plates, strong typography, motion implied by slants) — but an ORIGINAL look: palette deep navy, ink black, cyan and violet with one coral-red accent; no Persona or Metaphor logos, characters, fonts, icons or red-black colour scheme; Korean UI text; clean 3D toon battle scene behind the UI. Screen: ui_kit_sheet — component sheet: plates (idle/focus/disabled), pills, bars, chips, icons frame, buttons — flat on navy.

## Images (saved as candidate_A..D.png; viewer images 1..4)

- candidate_A.png: labelled large and small plates (기본 / 선택 / 비활성), menu tabs, round pills, ON/OFF toggle, HP/MP/TP status bars, progress bars, status chips, element and weakness icons, icon containers, action buttons (확인/취소/장착), labels. Flat navy with only a thin city strip in the header. Complete and legible. Best match for "flat on navy".
- candidate_B.png: complete set (plates, bars, chips, WEAK badge, icon containers, buttons, tooltip, character mini frame) with city art inside the plates and a header image. Dense but legible; less flat.
- candidate_C.png: plates with character and city art inside, big pseudo-English titles (QUEST / CHARACTER / SHOP), full component set. Rich, but the plates are not flat and the title text competes with the sheet.
- candidate_D.png: labelled plates, bars, chips, icon containers, buttons, tooltip; flat navy with a header strip. Some small text in the bars and chips is hard to read at phone size.

## Suggested pick

candidate_A.png. Reason: it is the only sheet that is flat on navy as the brief asks, shows every requested component state (idle, focus, disabled) with readable Korean labels, and has the cleanest spacing. Note for main session: these are references for the kit geometry (W3-T2), not textures; the actual plate skew is built in UISkew, not copied from the image.

Status: 4/4 images usable as references; no follow-up request used.
Tripo: not used. Credits: 0.
