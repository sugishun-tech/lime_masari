"""Use the project's original raster character sprites (no external character pack).

The four transparent cells for each character are split from the generated source
sheet. Only facial regions change between frames; hair and clothing remain fixed.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/characters'
NAMES=('lime','masari')


def _region_mask(boxes):
    mask=Image.new('L',(640,640),0)
    d=ImageDraw.Draw(mask)
    for box in boxes:d.rounded_rectangle(box,radius=6,fill=255)
    return mask.filter(ImageFilter.GaussianBlur(2.0))


def build_assets():
    for who in NAMES:
        base=Image.open(OUT/f'{who}_raw_0_0.png').convert('RGBA')
        speaking=Image.open(OUT/f'{who}_raw_0_1.png').convert('RGBA')
        blinking=Image.open(OUT/f'{who}_raw_1_0.png').convert('RGBA')
        if who=='lime':
            eyes=[(188,285,310,370),(368,280,493,369)]
            mouth=[(299,398,389,457)]
        else:
            eyes=[(177,269,291,351),(354,268,466,351)]
            mouth=[(275,362,381,434)]
        emask=_region_mask(eyes);mmask=_region_mask(mouth)
        for blink in (False,True):
            for talking in (False,True):
                sprite=base.copy()
                if blink:sprite=Image.composite(blinking,sprite,emask)
                if talking:sprite=Image.composite(speaking,sprite,mmask)
                sprite.save(OUT/f'{who}_{int(talking)}_{int(blink)}.png')


@lru_cache(maxsize=64)
def _load(who,talking,blink,size):
    if who not in NAMES:raise ValueError(f'Unknown character: {who}')
    p=OUT/f'{who}_{int(talking)}_{int(blink)}.png'
    return Image.open(p).convert('RGBA').resize((size,size),Image.Resampling.LANCZOS)


def image(who,mood='normal',mouth=0,blink=False,size=430):
    # Two mouth poses, chosen from measured amplitude; low-amplitude frames close.
    return _load(who,mouth>=2,bool(blink),size)


if __name__=='__main__':
    build_assets()
    sheet=Image.new('RGB',(1280,1280),'#fbfaf7')
    for row,who in enumerate(NAMES):
        for col,(mouth,blink) in enumerate([(0,False),(3,False),(0,True),(3,True)]):
            sprite=image(who,mouth=mouth,blink=blink,size=320)
            sheet.paste(sprite,(col*320,row*640),sprite)
    sheet.crop((0,0,1280,960)).save(ROOT/'checks/character_states.jpg',quality=94)
