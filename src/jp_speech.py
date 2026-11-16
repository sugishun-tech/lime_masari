"""Render authored Japanese kana as phonemes using local eSpeak formant synthesis.
This is NOT VOICEVOX, AquesTalk, or an imitation of a real speaker.
The pronunciation front-end is intentionally closed-vocabulary: only manually
reviewed kana are accepted. Mathematical notation never enters the synthesizer.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, wave
from pathlib import Path
import numpy as np
from scipy.signal import resample_poly

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=Path(os.environ.get('XDG_CACHE_HOME',str(Path.home()/'.cache')))/'langlands-phoneme-espeak'
VOICE={
 'lime':'''name LimeFormant
language eo
gender female
pitch 190 225
formant 0 100 80 100
formant 1 112 90 120
formant 2 118 90 120
formant 3 112 90 120
formant 4 110 85 120
formant 5 110 85 120
stressLength 160 160 160 160 160 160 160 160
stressAmp 20 20 20 20 20 20 20 20
intonation 3
roughness 0
flutter 0
consonants 115 110
''',
 'masari':'''name MasariFormant
language eo
gender female
pitch 145 183
formant 0 100 90 100
formant 1 106 95 120
formant 2 110 90 120
formant 3 106 90 120
formant 4 104 90 120
formant 5 104 90 120
stressLength 160 160 160 160 160 160 160 160
stressAmp 20 20 20 20 20 20 20 20
intonation 3
roughness 0
flutter 0
consonants 115 110
'''}

BASE={}
for row,cons in [('あいうえお',''),('かきくけこ','k'),('がぎぐげご','g'),('さしすせそ','s'),('ざじずぜぞ','z'),('たちつてと','t'),('だぢづでど','d'),('なにぬねの','n'),('はひふへほ','h'),('ばびぶべぼ','b'),('ぱぴぷぺぽ','p'),('まみむめも','m'),('らりるれろ','*')]:
    for ch,v in zip(row,'aiueo'):BASE[ch]=cons+v
BASE.update({'し':'Si','じ':'dZi','ぢ':'dZi','ち':'tSi','つ':'tsu','づ':'zu','ふ':'fu','ひ':'Ci','や':'ja','ゆ':'ju','よ':'jo','わ':'wa','を':'o','ん':'N','ゔ':'vu','ぁ':'a','ぃ':'i','ぅ':'u','ぇ':'e','ぉ':'o'})
DIG={}
for ch,cons in [('き','kj'),('ぎ','gj'),('し','S'),('じ','dZ'),('ち','tS'),('に','nj'),('ひ','C'),('び','bj'),('ぴ','pj'),('み','mj'),('り','*j')]:
    for y,v in [('ゃ','a'),('ゅ','u'),('ょ','o')]:DIG[ch+y]=cons+v
DIG.update({'ふぁ':'fa','ふぃ':'fi','ふぇ':'fe','ふぉ':'fo','てぃ':'ti','でぃ':'di','とぅ':'tu','どぅ':'du','しぇ':'Se','じぇ':'dZe','ちぇ':'tSe','うぃ':'wi','うぇ':'we','うぉ':'wo','つぁ':'tsa','つぃ':'tsi','つぇ':'tse','つぉ':'tso','ゔぁ':'va','ゔぃ':'vi','ゔぇ':'ve','ゔぉ':'vo'})

def phonemes(token:str)->str:
    units=[];i=0;gem=False
    while i<len(token):
        ch=token[i]
        if ch=='っ':gem=True;i+=1;continue
        if ch=='ー':
            if not units or not re.search('[aeiou]$',units[-1]):raise ValueError('Invalid long vowel '+token)
            units[-1]+=':';i+=1;continue
        if token[i:i+2] in DIG:u=DIG[token[i:i+2]];i+=2
        elif ch in BASE:u=BASE[ch];i+=1
        else:raise ValueError(f'Unreviewed pronunciation character {ch!r} in {token}')
        if gem:
            # Prolong fricatives; use a brief closure before plosives/affricates.
            units.append('s' if u.startswith('s') else 'S' if u.startswith('S') else '_:')
            gem=False
        # Japanese long vowels within one authored word group.
        if u in 'aiueo' and units:
            if units[-1].endswith(u) or (u=='u' and units[-1].endswith('o')) or (u=='i' and units[-1].endswith('e')):
                units[-1]+=':';continue
        units.append(u)
    if gem:units.append('_:')
    s=''.join(units)
    s=re.sub(r'N(?=[bpm])','m',s)
    s=re.sub(r'N(?=[tdnzsS])','n',s)
    # One explicit, low-contrast stress anchor per Japanese word group.
    s=re.sub(r'([aeiou])',r"'\1",s,count=1)
    return s

def phonetic_text(kana:str)->str:
    if re.search(r'[^ぁ-ゖー 、。！？!?\n]',kana):raise ValueError('Kana-only speech input required: '+kana)
    out=[]
    for chunk in re.split(r'([、。！？!?])',kana):
        if chunk in ['、','。','！','？','!','?']:
            out.append({'、':',','。':'.','！':'!','？':'?'}.get(chunk,chunk));continue
        words=chunk.strip().split()
        if words:out.append('[['+' '.join(phonemes(w) for w in words)+']]')
    return ' '.join(out)

def setup():
    data=RUNTIME/'espeak-data'
    if not data.exists():
        original=Path('/usr/lib/x86_64-linux-gnu/espeak-data')
        if not original.exists():raise RuntimeError('Local eSpeak data missing')
        shutil.copytree(original,data)
    for who,config in VOICE.items():
        (data/'voices'/who).write_text(config)
        (ROOT/'data'/(who+'_formant.voice')).write_text(config)

def dialogue():
    counters={};cues=[]
    for raw in (ROOT/'data/dialogue.tsv').read_text().splitlines():
        scene,speaker,mood,subtitle,kana=raw.split('|')
        counters[scene]=counters.get(scene,0)+1
        cue={'id':f'{scene}_{counters[scene]:02d}','scene':scene,'speaker':speaker,'mood':mood,'subtitle':subtitle,'kana':kana}
        cue['phonemes']=phonetic_text(kana)
        cues.append(cue)
    return cues

def synthesize(cue):
    wav=ROOT/'audio'/(cue['id']+'.wav')
    if wav.exists():return wav
    raw=ROOT/'audio'/(cue['id']+'_raw.wav')
    subprocess.run(['espeak',f'--path={RUNTIME}','-v',cue['speaker'],'-s','148','-a','145','-w',str(raw),'--stdin'],input=cue['phonemes'],text=True,check=True,capture_output=True)
    with wave.open(str(raw),'rb') as f:
        sr=f.getframerate();a=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(np.float32)/32768
    # Remove excessive engine end padding; retain phrase-end breath space.
    nz=np.flatnonzero(np.abs(a)>.004)
    if not len(nz):raise ValueError('Silent generated audio '+cue['id'])
    a=a[max(0,nz[0]-int(.055*sr)):min(len(a),nz[-1]+int(.16*sr))]
    # Gentle peak normalization, same headroom for both voices.
    a*=0.78/max(float(np.max(np.abs(a))),.1)
    a=resample_poly(a,320,147) if sr==22050 else resample_poly(a,48000,sr)
    a=np.clip(a,-.98,.98)
    with wave.open(str(wav),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes((a*32767).astype('<i2').tobytes())
    raw.unlink()
    return wav

if __name__=='__main__':
    setup();cues=dialogue();total=0
    for i,c in enumerate(cues):
        p=synthesize(c)
        with wave.open(str(p),'rb') as f:c['audio_duration']=f.getnframes()/f.getframerate()
        total+=c['audio_duration']
        print(i+1,c['id'],c['speaker'],round(c['audio_duration'],2),flush=True)
    (ROOT/'data/cues.json').write_text(json.dumps(cues,ensure_ascii=False,indent=2))
    print('total audio',total,'seconds',flush=True)
