"""Compose the labelled v2 monster sheet from contact_sheet.py cells (system Python + Pillow).

  python3 Blender/enemies_c/compose_sheet.py CELL_DIR OUT.png [--report Blender/blend/enemy_v2_production_all.json]
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roster import ROSTER  # noqa: E402

FONT_B = '/usr/share/fonts/truetype/nanum/NanumSquareRoundB.ttf'
FONT_R = '/usr/share/fonts/truetype/nanum/NanumSquareRoundR.ttf'
BIOMES = [('verdant_ruins', '신록의 유적', (52, 92, 58), (24, 44, 30)),
          ('frost_grotto', '빙해의 동굴', (52, 86, 120), (22, 38, 60)),
          ('ember_caverns', '홍염의 사막', (120, 64, 40), (54, 26, 20)),
          ('haunted_crypt', '망자의 묘소', (70, 52, 98), (30, 22, 46))]


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cells')
    ap.add_argument('out')
    ap.add_argument('--report', default=os.path.join(os.path.dirname(__file__), '..', 'blend', 'enemy_v2_production_all.json'))
    ap.add_argument('--cell', type=int, default=330)
    o = ap.parse_args()
    tris = {}
    if os.path.isfile(o.report):
        tris = {r['id']: r['triangles'] for r in json.load(open(o.report, encoding='utf-8'))['reports']}
    cols = max(sum(1 for r in ROSTER.values() if r[2] == b[0]) for b in BIOMES)
    C, label_h, band, head = o.cell, 78, 46, 92
    W = cols * C + 40
    H = head + len(BIOMES) * (band + C + label_h + 14) + 20
    sheet = Image.new('RGB', (W, H), (17, 15, 24))
    d = ImageDraw.Draw(sheet)
    d.text((22, 18), '심연의 미궁 · 신규 몬스터 v2', font=font(FONT_B, 38), fill=(255, 236, 190))
    d.text((24, 64), f'{len(ROSTER)}종 (일반 {sum(not k.startswith("elite_") for k in ROSTER)} · 엘리트/FOE {sum(k.startswith("elite_") for k in ROSTER)}) · '
           '절차 생성 치비 모델 · FBX 재임포트 Idle 0프레임 · Workbench 미리보기', font=font(FONT_R, 17), fill=(190, 184, 210))
    y = head
    for biome, ko, light, dark in BIOMES:
        ids = [k for k, r in ROSTER.items() if r[2] == biome]
        d.rounded_rectangle((16, y, W - 16, y + band - 6), 10, fill=dark)
        d.text((30, y + 8), f'{ko}  ·  {biome}', font=font(FONT_B, 24), fill=(250, 244, 230))
        y += band
        for i, eid in enumerate(ids):
            x = 20 + i * C
            tile = Image.new('RGB', (C - 10, C + label_h - 6), dark)
            td = ImageDraw.Draw(tile)
            for yy in range(C - 10):
                t = yy / (C - 10)
                col = tuple(int(light[k] * (1 - t) * .9 + dark[k] * t) for k in range(3))
                td.line((0, yy, C - 10, yy), fill=col)
            cell = os.path.join(o.cells, eid + '.png')
            if os.path.isfile(cell):
                im = Image.open(cell).convert('RGBA').resize((C - 26, C - 26), Image.LANCZOS)
                tile.paste(im, (8, 6), im)
            elite = eid.startswith('elite_')
            name = ROSTER[eid][1]
            td.text((12, C - 2), name, font=font(FONT_B, 25), fill=(255, 214, 120) if elite else (255, 255, 255))
            sub = f"{'엘리트·FOE' if elite else '일반'} · {ROSTER[eid][3]} · {tris.get(eid, 0):,} tris"
            td.text((12, C + 30), sub, font=font(FONT_R, 15), fill=(214, 208, 226))
            td.text((12, C + 50), eid, font=font(FONT_R, 13), fill=(160, 154, 176))
            mask = Image.new('L', tile.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, tile.size[0] - 1, tile.size[1] - 1), 14, fill=255)
            sheet.paste(tile, (x, y), mask)
            if elite:
                d.rounded_rectangle((x, y, x + tile.size[0] - 1, y + tile.size[1] - 1), 14, outline=(232, 182, 72), width=3)
        y += C + label_h + 14
    os.makedirs(os.path.dirname(os.path.abspath(o.out)), exist_ok=True)
    sheet.save(o.out)
    print('SHEET', o.out, sheet.size)


if __name__ == '__main__':
    main()
