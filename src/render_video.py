"""Render the delivered WAVs, mathematical plates, and animated character sprites.
No server and no speech service are required for this render path.
"""
from __future__ import annotations
import hashlib,json,math,subprocess,wave,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
import characters
import math_board as mb
ROOT=Path(__file__).resolve().parents[1]
W,H=1920,1080
AFPS=15
VFPS=30
SR=48000
BG='#fbfaf7';INK='#332f39';R='#267f83';M='#88415f'
NAMES={'lime':'ライム','masari':'マサリ'}
COLORS={'lime':R,'masari':M}

def text(d,xy,t,size=32,color=INK,bold=False,anchor='lt'):
    d.text(xy,t,font=mb.font(size,bold),fill=color,anchor=anchor)

def setup_timeline():
    cues=json.loads((ROOT/'data/cues.json').read_text());project=json.loads((ROOT/'data/scenes.json').read_text())
    scenes={s['id']:s for s in project['scenes']}
    out=wave.open(str(ROOT/'audio/narration.wav'),'wb');out.setnchannels(1);out.setsampwidth(2);out.setframerate(SR)
    start=0
    for cue in cues:
        with wave.open(str(ROOT/'audio'/(cue['id']+'.wav')),'rb') as f:
            assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,SR)
            raw=f.readframes(f.getnframes())
        samples=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768
        # Short leading breath and a longer reading hold on dense equations.
        lead=round(.12*SR)
        extra=.85 if scenes[cue['scene']]['layout'] in ('formula','match','theorem','grid') else .65
        frames=math.ceil((len(samples)/SR+.12+extra)*AFPS)
        total=frames*(SR//AFPS)
        padded=np.pad(samples,(lead,total-lead-len(samples)))
        out.writeframesraw((padded*32767).astype('<i2').tobytes())
        cue['start_frame']=start;cue['frame_count']=frames;cue['start']=start/AFPS;cue['end']=(start+frames)/AFPS;cue['duration']=frames/AFPS
        rms=np.sqrt(np.mean(padded.reshape(frames,SR//AFPS)**2,axis=1))
        top=max(float(np.percentile(rms[rms>.002],80)),.02)
        mouth=np.where(rms<.012,0,np.where(rms<.32*top,1,np.where(rms<.70*top,2,3)))
        cue['mouth_frames']=mouth.tolist();cue['speech_start']=cue['start']+.12;cue['speech_end']=cue['speech_start']+len(samples)/SR
        cue['chapter']=scenes[cue['scene']]['chapter'];cue['title']=scenes[cue['scene']]['title']
        start+=frames
    out.close()
    meta={'width':W,'height':H,'fps':VFPS,'animation_fps':AFPS,'duration':start/AFPS,'frames':start*2,'audio_sample_rate':SR,'speech_engine':'eSpeak 1.48.15, authored kana-to-phoneme front-end, custom two-voice formant settings','traditional_yukkuri_voice':False,'cues':cues}
    (ROOT/'data/timeline.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
    srt=[]
    def ts(t):
        msec=round(t*1000);hh,msec=divmod(msec,3600000);mm,msec=divmod(msec,60000);ss,ms=divmod(msec,1000);return f'{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}'
    for i,c in enumerate(cues,1):srt += [str(i),f"{ts(c['start'])} --> {ts(c['end'])}",NAMES[c['speaker']]+'：'+c['subtitle'],'']
    (ROOT/'subtitles.srt').write_text('\n'.join(srt))
    chapters=[';FFMETADATA1','title=ライムとマサリのゆったり解説｜ラングランズ・プログラム','comment=新規制作キャラクター：ライム、マサリ。音声は独自調整したeSpeak合成音声。']
    starts=[]
    for c in cues:
        if not starts or starts[-1]['scene']!=c['scene']:starts.append(c)
    for i,c in enumerate(starts):
        end=starts[i+1]['start'] if i+1<len(starts) else meta['duration']
        chapters += ['[CHAPTER]','TIMEBASE=1/1000',f"START={round(c['start']*1000)}",f"END={round(end*1000)}",'title='+c['title']]
    (ROOT/'data/chapters.ffmeta').write_text('\n'.join(chapters))
    return project,scenes,cues,meta

def background(scene,cue,i,total):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    # Header is separate from the smaller, dense math plate.
    text(d,(78,26),'ライムとマサリのゆったり解説',26,'#746c72',True)
    text(d,(1840,27),f"{int(scene['id']):02d} / 28  ·  {scene['chapter']}",24,'#746c72',False,'rt')
    title=scene['title'];sz=49
    while mb.font(sz,True).getlength(title)>1760:sz-=1
    text(d,(78,72),title,sz,INK,True)
    # Relevant equations and diagrams stay above the character heads.
    plate=mb.board(scene,2,'voiced',{})
    content=plate.crop((70,185,1850,765)).resize((1400,456),Image.Resampling.LANCZOS)
    d.rounded_rectangle((245,135,1675,607),radius=20,fill='white',outline='#e3dfda',width=2)
    im.paste(content,(260,143))
    d=ImageDraw.Draw(im)
    note=scene['content'].get('bottom','')
    lines=mb.wrap(note,21,1260)
    for j,line in enumerate(lines[:3]):text(d,(330,622+j*28),line,21,'#6f6970')
    # Nameplates remain specific names, never anonymous presenter roles.
    for who,x,y in [('lime',225,637),('masari',1695,637)]:
        col=COLORS[who]
        d.rounded_rectangle((x-78,y-22,x+78,y+22),radius=18,fill=col)
        text(d,(x,y),NAMES[who],28,'white',True,'mm')
    col=COLORS[cue['speaker']]
    d.rounded_rectangle((430,726,1490,1025),radius=25,fill='white',outline=col,width=4)
    if cue['speaker']=='lime':
        d.polygon([(431,828),(397,848),(431,870)],fill='white');d.line([(431,828),(397,848),(431,870)],fill=col,width=4)
    else:
        d.polygon([(1489,828),(1523,848),(1489,870)],fill='white');d.line([(1489,828),(1523,848),(1489,870)],fill=col,width=4)
    text(d,(468,749),NAMES[cue['speaker']],31,col,True)
    size=38;lines=mb.wrap(cue['subtitle'],size,980)
    if len(lines)>1 and len(lines[-1])<len(lines[-2])*.45:
        balanced=min(980,max(600,mb.font(size).getlength(cue['subtitle'])/len(lines)+size))
        lines=mb.wrap(cue['subtitle'],size,balanced)
    while len(lines)>4:size-=1;lines=mb.wrap(cue['subtitle'],size,980)
    gap=14;bodyh=len(lines)*(size+gap)-gap
    y=805+(195-bodyh)/2
    for j,line in enumerate(lines):text(d,(468,round(y+j*(size+gap))),line,size,INK)
    text(d,(70,1053),'出典 '+', '.join(scene['refs']),19,'#776f76')
    text(d,(1845,1053),'LIME × MASARI',19,'#776f76',False,'rt')
    d.rectangle((0,1075,W,1079),fill='#e4dfd8');d.rectangle((0,1075,round(W*(i+1)/total),1079),fill=col)
    return im

def composite(base,cue,mouth,blink_active,blink_other,bob):
    im=base.copy()
    for who,x,y,size in [('lime',25,648,400),('masari',1495,648,400)]:
        active=who==cue['speaker']
        mood=cue['mood'] if active else ('skeptical' if cue['mood']=='serious' and who=='lime' else 'normal')
        sprite=characters.image(who,mood,mouth if active else 0,blink_active if active else blink_other,size)
        im.paste(sprite,(x,y+(bob if active else 0)),sprite)
    return im

def render(preview_only=False):
    project,scenes,cues,meta=setup_timeline()
    # Preview snapshots represent the actual compositing geometry.
    for idx in [0,1,25,40,55,77,83]:
        cue=cues[idx];base=background(scenes[cue['scene']],cue,idx,len(cues))
        composite(base,cue,2,False,False,0).save(ROOT/'checks'/f'frame_{idx:03d}.jpg',quality=92)
    if preview_only:return
    out=ROOT.parent/'langlands_lime_masari_voiced.mp4'
    cmd=['ffmpeg','-hide_banner','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(AFPS),'-i','pipe:0','-i',str(ROOT/'audio/narration.wav'),'-i',str(ROOT/'data/chapters.ffmeta'),'-i',str(ROOT/'subtitles.srt'),'-map','0:v:0','-map','1:a:0','-map','3:0','-c:s','mov_text','-metadata:s:s:0','language=jpn','-map_metadata','2','-map_chapters','2','-c:v','libx264','-preset','veryfast','-tune','animation','-crf','23','-threads','4','-pix_fmt','yuv420p','-r',str(VFPS),'-c:a','aac','-b:a','128k','-ar','48000','-af',f'loudnorm=I=-18:TP=-2:LRA=8,atrim=duration={meta["duration"]:.9f}','-t',f'{meta["duration"]:.9f}','-disposition:s:0','0','-movflags','+faststart',str(out)]
    t0=time.time()
    with (ROOT/'checks/ffmpeg.log').open('w') as err:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=err)
        try:
            for i,c in enumerate(cues):
                base=background(scenes[c['scene']],c,i,len(cues));cache={}
                for frame in range(c['frame_count']):
                    t=c['start']+frame/AFPS
                    mouth=c['mouth_frames'][frame]
                    ba=(t+(0 if c['speaker']=='lime' else 1.3))%4.7<.13
                    bo=(t+(1.7 if c['speaker']=='lime' else .2))%5.1<.13
                    bob=(3 if math.sin(t*4)>0.55 else -3 if math.sin(t*4)<-.55 else 0) if mouth else 0
                    key=(int(mouth>=2)*3,ba,bo,bob)
                    if key not in cache:cache[key]=composite(base,c,key[0],ba,bo,bob).tobytes()
                    proc.stdin.write(cache[key])
                print(f"Rendered {i+1}/{len(cues)} | {c['id']} | position {c['end']:.1f}s | elapsed {time.time()-t0:.1f}s",flush=True)
        finally:
            proc.stdin.close()
        ret=proc.wait()
        if ret:raise RuntimeError(f'ffmpeg exited {ret}; see checks/ffmpeg.log')
    print('COMPLETE',out,meta['duration'],flush=True)

if __name__=='__main__':
    import sys
    render('--preview-only' in sys.argv)
