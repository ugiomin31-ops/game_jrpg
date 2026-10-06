"""Original 3D/Pillow ABYSS store-art production. No network or paid tools.
python Tools/store/generate.py [--compose-only] [--blender PATH]
Native Blender scenes, original vector title, and editable OpenRaster layer stacks
are retained in Store/source. Outputs are illustrations, not game screenshots.
"""
import argparse
import io
import json
from pathlib import Path
import random
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / 'Store'
SOURCE = STORE / 'source'
OUTPUTS = (
    ('abyss-main-1232x706', 1232, 706, 'landscape'),
    ('abyss-header-920x430', 920, 430, 'wide'),
    ('abyss-small-462x174', 462, 174, 'small'),
    ('abyss-vertical-748x896', 748, 896, 'portrait'),
    ('abyss-library-600x900', 600, 900, 'portrait'),
    ('abyss-key-art-3840x2160', 3840, 2160, 'landscape'),
)
# Original vector letterforms, not a downloaded logo or font. Coordinates are
# deliberately retained as editable polygons in the generated SVG master.
GLYPHS = {
    'A': (151, [[(0,160),(0,150),(15,148),(67,0),(85,0),(139,148),(151,150),(151,160),(92,160),(92,150),(103,146),(92,114),(45,114),(35,146),(51,150),(51,160)],
                [(54,91),(83,91),(68,47)]]),
    'B': (140, [[(0,0),(85,0),(115,12),(128,32),(128,54),(111,75),(128,87),(140,109),(137,137),(120,153),(85,160),(0,160),(0,150),(17,147),(17,13),(0,10)],
                [(47,23),(79,23),(96,31),(99,51),(88,64),(47,64)],
                [(47,87),(86,87),(106,99),(108,122),(95,135),(47,137)]]),
    'Y': (155, [[(0,0),(66,0),(66,10),(51,14),(81,66),(111,14),(96,10),(96,0),(155,0),(155,10),(139,15),(97,88),(97,146),(116,150),(116,160),(43,160),(43,150),(64,146),(64,88),(19,15),(0,10)]]),
    'S': (126, [[(113,0),(113,50),(103,50),(93,30),(80,21),(52,21),(36,31),(36,47),(47,57),(88,75),(112,94),(121,117),(117,136),(102,152),(81,160),(40,160),(17,151),(6,160),(0,160),(0,107),(10,107),(22,129),(41,139),(72,139),(88,131),(89,114),(76,103),(36,86),(12,70),(3,48),(5,28),(18,11),(41,0),(82,0),(102,9),(108,0)]]),
}
TITLE_WIDTH = sum(GLYPHS[c][0] for c in 'ABYSS') + 20 * 4


def vector_title():
    rows = []
    x = 0
    for char in 'ABYSS':
        width, polygons = GLYPHS[char]
        commands = []
        for polygon in polygons:
            commands.append('M' + ' L'.join(f'{px+x},{py}' for px, py in polygon) + ' Z')
        rows.append('<path fill-rule="evenodd" d="' + ' '.join(commands) + '"/>')
        x += width + 20
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{TITLE_WIDTH}" height="160" viewBox="0 0 {TITLE_WIDTH} 160"><g fill="#e6c477">' + ''.join(rows) + '</g></svg>\n'
    (SOURCE / 'abyss-title.svg').write_text(svg, encoding='utf-8')


def title_mask(width):
    height = round(width * 160 / TITLE_WIDTH)
    scale = width / TITLE_WIDTH
    mask = Image.new('L', (width, height))
    draw = ImageDraw.Draw(mask)
    x = 0
    for char in 'ABYSS':
        advance, polygons = GLYPHS[char]
        for index, polygon in enumerate(polygons):
            draw.polygon([((px+x)*scale, py*scale) for px, py in polygon], fill=255 if index == 0 else 0)
        x += advance + 20
    return mask


def title_layer(size, rect):
    w, h = size
    x, y, width = rect
    x, y, width = round(x*w), round(y*h), round(width*w)
    mask = title_mask(width)
    th = mask.height
    layer = Image.new('RGBA', size)
    shadow = Image.new('RGBA', size)
    black = Image.new('RGBA', mask.size, (0, 5, 10, 255))
    shadow.paste(black, (x + max(1,w//500), y + max(2,h//150)), mask)
    layer.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(max(1,w/650))))
    # Fine beveled top edge and a warm metal face, never low-contrast outline text.
    edge = mask.filter(ImageFilter.MaxFilter(3))
    layer.paste((73, 62, 35, 255), (x, y, x+width, y+th), edge)
    fill = Image.new('RGBA', mask.size)
    fd = ImageDraw.Draw(fill)
    stops = [(255,240,191), (226,190,108), (243,213,144)]
    for row in range(th):
        t = row / max(1, th-1)
        a,b,u = (stops[0],stops[1],t/.68) if t < .68 else (stops[1],stops[2],(t-.68)/.32)
        color = tuple(round(aa+(bb-aa)*u) for aa,bb in zip(a,b))
        fd.line((0,row,width,row), fill=color+(255,))
    layer.paste(fill, (x,y), mask)
    draw = ImageDraw.Draw(layer)
    # Dawn-diamond mark and ruled baseline are purely original ornament.
    cx = x + width*.5
    gap = width*.075
    baseline = y + th + width*.042
    lw = max(1,round(w/1000))
    draw.line((x+width*.12,baseline,cx-gap,baseline),fill=(151,122,66,230),width=lw)
    draw.line((cx+gap,baseline,x+width*.88,baseline),fill=(151,122,66,230),width=lw)
    r = width*.012
    draw.polygon([(cx,baseline-r),(cx+r,baseline),(cx,baseline+r),(cx-r,baseline)],fill=(237,202,128,255))
    return layer


def background(size, portrait):
    w,h = size
    base = Image.new('RGBA', size, (3,13,19,255))
    d = ImageDraw.Draw(base)
    for row in range(h):
        t=row/max(1,h-1)
        d.line((0,row,w,row), fill=(round(5+4*t),round(20+5*t),round(27+7*t),255))
    glow = Image.new('RGBA', size)
    gd = ImageDraw.Draw(glow)
    cx,cy = (w*.5,h*.39) if portrait else (w*.77,h*.40)
    gd.ellipse((cx-w*.4,cy-h*.5,cx+w*.4,cy+h*.5),fill=(18,114,122,105))
    gd.ellipse((w*.21,h*.74,w*.99,h*1.2),fill=(158,105,45,34))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(w*.095)))
    return base


def fit_plate(name, size, center, height, tint=None, opacity=1):
    image = Image.open(SOURCE / (name+'.png')).convert('RGBA')
    bbox = image.getbbox()
    if bbox is None:
        raise ValueError('Empty rendered production plate: '+name)
    image=image.crop(bbox)
    target_height=round(height*size[1])
    image=image.resize((round(image.width*target_height/image.height),target_height),Image.Resampling.LANCZOS)
    if tint:
        alpha=image.getchannel('A')
        gray=ImageOps.grayscale(image)
        duotone=ImageOps.colorize(gray,tint[0],tint[1]).convert('RGBA')
        image=Image.blend(duotone,image,.28)
        image.putalpha(alpha)
    if opacity != 1:
        image.putalpha(image.getchannel('A').point(lambda value: round(value*opacity)))
    layer=Image.new('RGBA',size)
    x=round(center[0]*size[0]-image.width/2)
    y=round(center[1]*size[1]-image.height/2)
    layer.alpha_composite(image,(x,y))
    return layer


def atmosphere(size, portrait):
    w,h=size
    layer=Image.new('RGBA',size)
    d=ImageDraw.Draw(layer)
    cx,cy=(w*.5,h*.42) if portrait else (w*.76,h*.43)
    r=w*.37 if portrait else h*.48
    # Fragmented gold astronomical rings emphasize the abyss silhouette.
    for factor,start,end in ((1,195,318),(1,12,155),(1.045,235,340),(.88,205,290)):
        rr=r*factor
        d.arc((cx-rr,cy-rr,cx+rr,cy+rr),start,end,fill=(161,139,81,65),width=max(1,round(w/1200)))
    rng=random.Random(128)
    for _ in range(105 if w>1000 else 45):
        x,y=rng.uniform(w*.36,w*.98),rng.uniform(h*.12,h*.94)
        radius=rng.choice((.5,.8,1.2))*max(1,w/1400)
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=(236,203,131,rng.randint(55,140)))
    return layer


def world_layer(size, portrait):
    image=Image.open(SOURCE/'crypt-world.png').convert('RGBA')
    image=ImageOps.fit(image,size,Image.Resampling.LANCZOS,centering=(.55,.60))
    alpha=image.getchannel('A')
    image=ImageOps.colorize(ImageOps.grayscale(image),(2,15,23),(52,96,99)).convert('RGBA')
    # Environmental foothold is visible, but editorial darkness protects the title.
    mask=Image.new('L',size)
    d=ImageDraw.Draw(mask)
    w,h=size
    for row in range(h):
        amount=max(0,(row/h-.40)/.60)
        d.line((0,row,w,row),fill=round(150*amount))
    image.putalpha(ImageChops.multiply(alpha,mask))
    return image


def openraster(path, size, layers, merged):
    root=ET.Element('image',{'w':str(size[0]),'h':str(size[1]),'name':'ABYSS original 3D promotional illustration','version':'0.0.3'})
    stack=ET.SubElement(root,'stack')
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
        for index,(name,image) in enumerate(reversed(layers)):
            src=f'data/layer{index:02}.png'
            buffer=io.BytesIO();image.save(buffer,format='PNG')
            archive.writestr(src,buffer.getvalue())
            ET.SubElement(stack,'layer',{'name':name,'src':src,'opacity':'1.0','visibility':'visible','composite-op':'svg:src-over','x':'0','y':'0'})
        archive.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True))
        buffer=io.BytesIO();merged.save(buffer,format='PNG');archive.writestr('mergedimage.png',buffer.getvalue())
        thumb=merged.copy();thumb.thumbnail((256,256));buffer=io.BytesIO();thumb.save(buffer,format='PNG');archive.writestr('Thumbnails/thumbnail.png',buffer.getvalue())


def compose(name,w,h,layout):
    # Supersample store-sized images to keep fine lettering and outlines clean.
    factor=2 if w<1500 else 1
    size=(w*factor,h*factor)
    portrait=layout=='portrait'
    layers=[('Dark teal editorial ground',background(size,portrait)),('Authored haunted crypt environment',world_layer(size,portrait)),('Original dawn rings and motes',atmosphere(size,portrait))]
    if portrait:
        layers.append(('Giant abyss sorcerer',fit_plate('abyss-antagonist',size,(.50,.43),.65,tint=('#0b1623','#5c7984'),opacity=.93)))
        positions=[('mage',(.20,.78),.38),('cleric',(.82,.80),.35),('archer',(.64,.82),.38),('warrior',(.44,.80),.45)]
        title=(.075,.085,.85)
    elif layout=='small':
        layers.append(('Giant abyss sorcerer',fit_plate('abyss-antagonist',size,(.82,.52),1.05,tint=('#0c1826','#6e8e96'),opacity=.95)))
        positions=[('mage',(.68,.77),.70),('warrior',(.85,.85),.82)]
        title=(.055,.33,.48)
    elif layout=='wide':
        layers.append(('Giant abyss sorcerer',fit_plate('abyss-antagonist',size,(.78,.54),1.02,tint=('#0b1623','#68848e'),opacity=.95)))
        positions=[('cleric',(.89,.83),.55),('mage',(.54,.81),.57),('archer',(.79,.87),.57),('warrior',(.69,.85),.68)]
        title=(.055,.31,.46)
    else:
        layers.append(('Giant abyss sorcerer',fit_plate('abyss-antagonist',size,(.76,.48),.94,tint=('#0b1623','#68848e'),opacity=.96)))
        positions=[('cleric',(.88,.81),.46),('mage',(.51,.77),.53),('archer',(.79,.82),.50),('warrior',(.67,.81),.62)]
        title=(.055,.32,.44)
    # Hero faces retain the authored colors. Layers overlap at costume/feet only.
    for ident,center,height in positions:
        layers.append(('Authored '+ident+' with original equipped weapon',fit_plate(ident,size,center,height)))
    vignette=Image.new('RGBA',size)
    vd=ImageDraw.Draw(vignette)
    for row in range(size[1]):
        t=row/size[1]
        alpha=round(max(0,(t-.90)/.10)*80)
        if alpha: vd.line((0,row,size[0],row),fill=(2,10,15,alpha))
    layers.append(('Lower edge editorial shade',vignette))
    layers.append(('Original ABYSS vector title',title_layer(size,title)))
    merged=Image.new('RGBA',size)
    for _,image in layers:merged.alpha_composite(image)
    if factor!=1:
        layers=[(label,image.resize((w,h),Image.Resampling.LANCZOS)) for label,image in layers]
        merged=merged.resize((w,h),Image.Resampling.LANCZOS)
    destination=STORE/('key-art' if name.startswith('abyss-key-art') else 'capsules')/(name+'.png')
    destination.parent.mkdir(parents=True,exist_ok=True)
    merged.convert('RGB').save(destination,optimize=True)
    openraster(SOURCE/(name+'.ora'),(w,h),layers,merged)
    print('STORE_ART '+name,flush=True)
    return {'file':destination.relative_to(ROOT).as_posix(),'dimensions':[w,h],'native_layers':'Store/source/'+name+'.ora','kind':'original promotional illustration; not gameplay'}


def proof_sheet(records):
    sheet=Image.new('RGB',(1600,1900),(5,17,23))
    slots=[(30,945,750,430),(820,945,750,350),(1070,1480,462,174),(30,1430,360,432),(450,1430,300,450),(30,30,1540,866)]
    for record,(x,y,w,h) in zip(records,slots):
        image=Image.open(ROOT/record['file']).convert('RGB')
        image.thumbnail((w,h),Image.Resampling.LANCZOS)
        sheet.paste(image,(x+(w-image.width)//2,y+(h-image.height)//2))
    sheet.save(STORE/'artwork-proof-sheet.png',optimize=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compose-only',action='store_true',help='Reuse the retained rendered production plates')
    parser.add_argument('--blender',default='C:/Users/User/Tools/Blender/blender.exe')
    args=parser.parse_args()
    SOURCE.mkdir(parents=True,exist_ok=True)
    if not args.compose_only:
        subprocess.run([args.blender,'--background','--factory-startup','--python',str(Path(__file__).with_name('render_art.py'))],cwd=ROOT,check=True)
    vector_title()
    records=[compose(*row) for row in OUTPUTS]
    sources=json.loads((SOURCE/'asset-sources.json').read_text(encoding='utf-8'))
    manifest={'title':'ABYSS','generator':'Tools/store/generate.py','renderer':'Tools/store/render_art.py','reproduce':'python Tools/store/generate.py','blender_source':'Store/source/abyss-key-art.blend','title_source':'Store/source/abyss-title.svg','outputs':records,'original_asset_sources':sources,'source_generators':['Blender/heroes/generate.py','Blender/lib_humanoid/','Blender/bosses/boss.py','Blender/weapons/generate_all.py','Blender/environment/haunted_crypt/kit.py','Blender/environment/_arenas_a.py'],'visual_language_reference':['Assets/_Game/Scripts/UI/Kit/UITheme.cs','Assets/_Game/Scripts/UI/Screens/GameTitleScreen.cs'],'palette':{'ink':'#030d13','teal':'#12727a','gold':'#e6c477','bright_gold':'#fbe7b0'},'disclosures':['Original authored game geometry, custom original vector title, procedural editorial ornament.','Illustrations are not screenshots and do not represent a captured gameplay scene.','No stock imagery, image-generation service, badges, feature claims, or gameplay labels.','Working requested dimensions only: Steam/platform acceptance has not been asserted or researched.','Original asset authorship does not establish commercial or third-party IP clearance.']}
    (STORE/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    proof_sheet(records)
    print('STORE_ARTWORK_COMPLETE 6',flush=True)


if __name__=='__main__':
    main()
