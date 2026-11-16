"""Deterministic 1080p lecture frames. Fonts are resolved locally, never bundled."""
from __future__ import annotations
import hashlib, math, shutil, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
W,H=1920,1080
BG,INK,MUTED,LINE,SOFT='#ffffff','#17212b','#55616b','#dce2e6','#f4f6f7'
BLUE,RED,BLUE_SOFT,RED_SOFT='#245a75','#7a4048','#edf3f6','#f8f0f1'
FONT_PATH=BOLD_PATH=None
ERRORS=[]
_cache={}

def font(size,bold=False):
    key=(size,bold)
    if key in _cache:return _cache[key]
    path=BOLD_PATH if bold else FONT_PATH
    if not path:
        path='/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc'
    if not Path(path).is_file():
        if not shutil.which('fc-match'):raise RuntimeError('Install fonts-noto-cjk or provide a Japanese font path.')
        family='Noto Sans CJK JP'+(':style=Bold' if bold else '')
        path=subprocess.check_output(['fc-match','-f','%{file}',family],text=True).strip()
    _cache[key]=ImageFont.truetype(path,size,index=0,layout_engine=ImageFont.Layout.BASIC)
    return _cache[key]

def text(d,xy,s,size=36,fill=INK,bold=False,anchor='lt'):
    d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)

def wrap(s,size,width,bold=False):
    f=font(size,bold);out=[]
    for para in s.split('\n'):
        line=''
        for ch in para:
            if line and f.getlength(line+ch)>width:
                if ch in '、。，．！？：；）」』】〕〉》' and len(line)>1:
                    out.append(line[:-1]);line=line[-1]+ch
                else:out.append(line);line=ch
            else:line+=ch
        if line:out.append(line)
    return out or ['']

def paragraph(d,xy,s,size=34,width=1700,gap=13,fill=INK,bold=False,max_lines=None):
    lines=wrap(s,size,width,bold)
    if max_lines and len(lines)>max_lines:ERRORS.append(f'Too many lines: {s}')
    x,y=xy
    for line in lines:
        text(d,(x,y),line,size,fill,bold)
        if font(size,bold).getlength(line)>width+1:ERRORS.append(f'Text overflow: {line}')
        y+=size+gap
    return y

def box(d,rect,fill=SOFT):d.rounded_rectangle(rect,radius=12,fill=fill)
def rule(d,y,x1=80,x2=1840):d.line((x1,y,x2,y),fill=LINE,width=2)
def arrow(d,start,end,both=False):
    x1,y1=start;x2,y2=end;d.line((x1,y1,x2,y2),fill=BLUE,width=5)
    a=math.atan2(y2-y1,x2-x1)
    def head(x,y,a):
        d.polygon([(x,y),(x-18*math.cos(a-.4),y-18*math.sin(a-.4)),(x-18*math.cos(a+.4),y-18*math.sin(a+.4))],fill=BLUE)
    head(x2,y2,a)
    if both:head(x1,y1,a+math.pi)

def formula_path(tex):return ROOT/'assets/formulas'/(hashlib.sha256(tex.encode()).hexdigest()[:20]+'.png')
def ensure_formula(tex):
    dest=formula_path(tex)
    if dest.is_file():return dest
    if not shutil.which('latex') or not shutil.which('dvipng'):
        raise RuntimeError('New formulas need latex and dvipng. Existing formula images are bundled.')
    document=(r'\documentclass[12pt]{article}'+'\n'+r'\usepackage{amsmath,amssymb,bm}'+'\n'+r'\pagestyle{empty}'+'\n'+
              r'\begin{document}'+'\n'+r'\(\displaystyle '+tex+r'\)'+'\n'+r'\end{document}'+'\n')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='langlands_tex_') as td:
        p=Path(td);(p/'formula.tex').write_text(document,encoding='utf-8')
        for cmd in ([ 'latex','-interaction=nonstopmode','-halt-on-error','-no-shell-escape','formula.tex'],
                    ['dvipng','-q','-D','300','-T','tight','-bg','Transparent','-o','formula.png','formula.dvi']):
            r=subprocess.run(cmd,cwd=p,capture_output=True,text=True)
            if r.returncode:raise RuntimeError((r.stdout+r.stderr)[-5000:])
        shutil.copyfile(p/'formula.png',dest)
    dest.with_suffix('.tex').write_text(document,encoding='utf-8')
    return dest

def formula(im,tex,cy,height=82,max_width=1720,cx=960):
    src=Image.open(ensure_formula(tex)).convert('RGBA')
    scale=min(height/src.height,max_width/src.width)
    out=src.resize((max(1,round(src.width*scale)),max(1,round(src.height*scale))),Image.Resampling.LANCZOS)
    x,y=round(cx-out.width/2),round(cy-out.height/2)
    if x<60 or y<160 or x+out.width>W-60 or y+out.height>775:ERRORS.append(f'Formula overflow: {tex}')
    im.paste(out,(x,y),out)

def notes(d,lines,y,size=33,spacing=69,x=130,width=1660):
    for i,line in enumerate(lines):paragraph(d,(x,y+i*spacing),line,size,width,max_lines=2)

def table(d,headers,rows,y,row_h=66,x=200,width=1520,step=2):
    cw=width/len(headers);box(d,(x,y,x+width,y+row_h),INK)
    for i,h in enumerate(headers):text(d,(x+(i+.5)*cw,y+row_h/2),h,29,BG,True,'mm')
    for j,row in enumerate(rows):
        yy=y+(j+1)*row_h;hi=j in (1,4) and step>=2
        d.rectangle((x,yy,x+width,yy+row_h),fill=BLUE_SOFT if hi else (SOFT if j%2==0 else BG))
        for i,v in enumerate(row):text(d,(x+(i+.5)*cw,yy+row_h/2),v,34,BLUE if hi else INK,hi,'mm')
        d.line((x,yy+row_h,x+width,yy+row_h),fill=LINE,width=1)

def board(scene,step,mode,project):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im);c=scene['content'];kind=scene['layout']
    text(d,(80,30),f"LANGLANDS  /  {scene['chapter']}",23,MUTED)
    text(d,(80,82),scene['title'],53,INK,True)
    badge=scene['tag'];bw=round(font(25,True).getlength(badge))+42
    box(d,(1840-bw,27,1840,69),BLUE_SOFT);text(d,(1840-bw/2,48),badge,25,BLUE,True,'mm');rule(d,163)
    if kind=='hero':
        paragraph(d,(110,225),c['subtitle'],46,1700,bold=True)
        for x,label in ((150,c['left']),(1110,c['right'])):
            box(d,(x,385,x+650,615));text(d,(x+325,500),label,64,INK,True,'mm')
        arrow(d,(840,500),(1070,500),both=True);text(d,(960,687),'局所データを保つ対応',36,BLUE,True,'mm')
    elif kind=='three':
        for i,(heading,a,b) in enumerate(c['cards']):
            x=90+i*600;box(d,(x,240,x+540,680),BLUE_SOFT if step>=2 and i==2 else SOFT)
            text(d,(x+30,273),f'0{i+1}',25,BLUE,True)
            paragraph(d,(x+30,325),heading,35,480,bold=True,max_lines=2)
            paragraph(d,(x+30,430),a,31,480,max_lines=3)
            paragraph(d,(x+30,550),b,28,480,fill=MUTED,max_lines=3)
    elif kind=='formula':
        fs=c['formulas'];n=len(fs)
        ys={1:[330],2:[280,445],3:[242,377,514]}[n]
        hs={1:[102],2:[90,86],3:[76,76,82]}[n]
        for t,y,h in zip(fs,ys,hs):formula(im,t,y,h)
        notes(d,c.get('notes',[]),{1:490,2:568,3:615}[n],size=32,spacing=65 if n<3 else 61)
    elif kind=='grid':
        formula(im,c['formulas'][0],245,77,880,555)
        notes(d,c['notes'],365,size=32,x=100,width=880,spacing=110)
        if step>=2:formula(im,c['result'],650,75,900,560)
        left,top,sp=1220,270,86
        for k in range(5):
            xx=left+k*sp;yy=top+k*sp
            d.line((xx,top,xx,top+4*sp),fill=LINE,width=2);d.line((left,yy,left+4*sp,yy),fill=LINE,width=2)
            text(d,(xx,top+4*sp+37),str(k),27,MUTED,anchor='mm');text(d,(left-38,top+(4-k)*sp),str(k),27,MUTED,anchor='mm')
        for x in range(5):
            for y in range(5):
                xx,yy=left+x*sp,top+(4-y)*sp;valid=(y*y-x*x*x+x)%5==0;r=14 if valid else 4
                d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=BLUE if valid else '#c9d1d7')
        text(d,(left+4*sp+40,top+4*sp),'x',30,MUTED,anchor='mm');text(d,(left,top-39),'y',30,MUTED,anchor='mm')
        text(d,(1415,700),'7 points   +   O',30,BLUE,True,'mm')
    elif kind=='ap_table':formula(im,c['formulas'][0],235,74);table(d,c['headers'],c['rows'],310,61,step=step)
    elif kind=='match':table(d,c['headers'],c['rows'],212,62,step=step);formula(im,c['formulas'][0],710,67)
    elif kind=='theorem':
        box(d,(90,205,1830,315),BLUE_SOFT);paragraph(d,(125,235),c['headline'],36,1670,bold=True,max_lines=2)
        formula(im,c['formulas'][0],415,82);formula(im,c['formulas'][1],548,68);notes(d,c['notes'],628,29,56)
    elif kind=='galois':
        for t,y,h in zip(c['formulas'],[240,385,540],[72,95,78]):formula(im,t,y,h)
        notes(d,c['notes'],630,32,58)
    elif kind=='flow':
        for x,j in ((120,0),(1080,1)):
            box(d,(x,202,x+720,299));text(d,(x+360,250),c['top'][j],41,INK,True,'mm');arrow(d,(x+360,318),(x+360,365))
            box(d,(x,385,x+720,483));text(d,(x+360,434),c['middle'][j],29,INK,False,'mm');arrow(d,(x+360,502),(x+360,549))
            box(d,(x,568,x+720,655),BLUE_SOFT);text(d,(x+360,610),c['bottom_labels'][j],36,BLUE,True,'mm')
        arrow(d,(880,610),(1040,610),both=True);formula(im,c['formulas'][0],724,66)
    elif kind=='reciprocity':
        text(d,(480,242),c['left'],41,INK,True,'mm');text(d,(1440,242),c['right'],41,INK,True,'mm')
        formula(im,c['formulas'][0],362,102);formula(im,c['formulas'][1],501,68);notes(d,c['notes'],601,31,69)
    elif kind=='local_global':
        formula(im,c['formulas'][0],279,82);formula(im,c['formulas'][1],444,90);notes(d,c['notes'],579,32,80)
    elif kind=='functoriality':
        text(d,(210,238),'パラメータ側',29,MUTED);formula(im,c['formulas'][0],298,94);arrow(d,(960,369),(960,429))
        text(d,(210,435),'保型側',29,MUTED);formula(im,c['formulas'][1],492,86);notes(d,c['notes'],611,32,69)
    elif kind=='results':
        for i,(a,b) in enumerate(c['rows']):
            y=240+i*155;box(d,(100,y,1820,y+120),BLUE_SOFT if i==1 and step>=2 else SOFT)
            paragraph(d,(135,y+35),a,32,1000,bold=True,max_lines=2);paragraph(d,(1210,y+38),b,30,550,max_lines=2)
    else:raise ValueError(f'Unknown layout: {kind}')
    paragraph(d,(80,775),c.get('bottom',''),24,1760,7,fill=MUTED,max_lines=2)
    return im
