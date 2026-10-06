"""50 distinct procedural foley, magic, status, combat and interface designs.
All excitation/noise is generated here; no commercial samples or melodies used.
"""
import numpy as np
from abyss_audio import dsp
from abyss_audio.instruments import INSTRUMENTS

IDS = [
    "ui_move","ui_confirm","ui_cancel","ui_error","ui_open","ui_close","ui_buy",
    "footstep","door","chest","stairs","encounter","item","save","warp",
    "fire","ice","lightning","water","wind","earth","light","dark",
    "sword","axe","spear","bow","dagger","staff","hit","critical","guard","miss",
    "heal","buff","debuff","poison","burn","freeze","shock","sleep","silence","stun","regen","revive","death",
    "ultimate_warrior","ultimate_mage","ultimate_ranger","ultimate_cleric",
]


class Design:
    def __init__(self,name,length):
        self.name=name
        self.rng=dsp.seeded_rng(name)
        self.buf=np.zeros((dsp.ns(length),2))

    def add(self,x,start=0,gain=1,pan=0):
        dsp.mix_into(self.buf,dsp.balance(dsp.stereo(x),pan)*gain,dsp.ns(start) if start else 0)

    def voice(self,inst,pitch,start=0,duration=.25,gain=.6,pan=0):
        self.add(INSTRUMENTS[inst](float(dsp.mtof(pitch)),duration,.75,self.rng),start,gain,pan)

    def noise(self,start,length,low,high,gain=.5,attack=.003,decay=None,pan=0):
        n=dsp.ns(length)
        x=dsp.bp(self.rng.standard_normal(n),low,high)
        e=dsp.perc(n,attack,decay or length*.8)
        self.add(x*e,start,gain,pan)

    def sweep(self,start,length,f0,f1,gain=.5,attack=.005,shape="sine",pan=0):
        n=dsp.ns(length)
        f=np.geomspace(f0,f1,n)
        x=getattr(dsp,shape)(f,n)
        self.add(x*dsp.perc(n,attack,length*.9),start,gain,pan)

    def arpeggio(self,notes,start=0,step=.08,inst="celesta",gain=.4):
        for i,m in enumerate(notes):
            self.voice(inst,m,start+i*step,.2,gain,(-.3 if i%2 else .3))

    def finish(self,room=.12):
        x=dsp.hp(self.buf,35)
        if room:
            x+=dsp.convolve(x,dsp.make_ir(.65,.009,.6),len(x))*room
        return dsp.fade(x,.002,.025)


def build(name):
    length=4.0 if name.startswith("ultimate") else 2.8 if name in ("warp","revive","death","save") else 1.8
    d=Design(name,length)
    if name.startswith("ui_"):
        designs={"ui_move":([79,86],.028,"kalimba"),"ui_confirm":([74,78,81],.045,"celesta"),
                 "ui_cancel":([76,69],.06,"music_box"),"ui_error":([54,55,54],.055,"pulse_arp"),
                 "ui_open":([62,69,74,78],.033,"harp"),"ui_close":([78,74,69,62],.035,"harp"),
                 "ui_buy":([86,90,93,98],.04,"glock")}
        notes,step,inst=designs[name]
        d.arpeggio(notes,step=step,inst=inst,gain=.35)
        d.noise(0,.035,2500,9000,.08)
        return d.finish(.025)
    if name=="footstep":
        d.noise(0,.13,150,1800,.55); d.noise(.028,.1,1500,6500,.14); d.sweep(0,.09,120,65,.3)
    elif name=="door":
        d.sweep(0,.7,230,90,.2,shape="saw"); d.noise(.08,.7,300,1900,.16,attack=.2); d.voice("tom",42,.65,gain=.6); d.noise(.67,.13,800,4000,.35)
    elif name=="chest":
        d.noise(0,.1,1000,7000,.45); d.sweep(.05,.45,140,360,.18,shape="triangle"); d.arpeggio([74,81,86,90],.22,.07,"glock",.35)
    elif name=="stairs":
        for i in range(5):
            d.noise(i*.17,.1,150+i*50,1800+i*300,.45-i*.055); d.sweep(i*.17,.08,135+i*8,70,.2)
    elif name=="encounter":
        d.sweep(0,.45,180,1200,.25,shape="saw"); d.voice("brass",48,.35,.4,.7); d.voice("brass",55,.35,.4,.5); d.voice("taiko",36,.35,gain=.65)
    elif name=="item":
        d.arpeggio([72,76,79,84],step=.065,inst="music_box"); d.noise(0,.1,3000,11000,.12)
    elif name=="save":
        d.arpeggio([62,66,69,74,78,81,86],step=.11,inst="bell",gain=.22); d.voice("warm_pad",62,.1,1,.3)
    elif name=="warp":
        d.sweep(0,1.1,100,1800,.3,attack=.2,shape="triangle"); d.voice("air_pad",62,0,.7,.45); d.arpeggio([62,69,74,81,86,93],.25,.12,"glass_harmonica",.4); d.noise(.8,1,1500,10000,.2,attack=.25)
    elif name=="fire":
        d.noise(0,.35,150,1400,.65,attack=.025); d.sweep(.12,.5,180,42,.6); d.noise(.16,.8,800,10000,.35)
        for i in range(9): d.noise(.24+i*.065,.035,2200,12000,.2)
    elif name=="ice":
        d.arpeggio([91,98,103],step=.025,inst="glock",gain=.35); d.noise(.12,.4,3000,15000,.35); d.voice("glass_pad",79,.04,.35,.25)
    elif name=="lightning":
        for i in range(5): d.noise(i*.045,.075,400,16000,.9-i*.1)
        d.sweep(.12,.45,90,30,.65); d.voice("crash",60,.17,gain=.3)
    elif name=="water":
        d.noise(0,.8,250,4500,.3,attack=.1)
        for i in range(7): d.sweep(.03+i*.08,.16,900+i*70,130+i*25,.16,pan=(i%3-1)*.4)
    elif name=="wind":
        d.voice("wind",70,0,.7,.9); d.sweep(.1,.7,430,1200,.12,attack=.15); d.noise(.05,.65,800,9000,.2,attack=.15)
    elif name=="earth":
        d.voice("taiko",30,0,gain=.75); d.noise(.08,.8,50,700,.65)
        for i in range(6): d.voice("tom",42-i,.08+i*.07,gain=.3)
    elif name=="light":
        d.arpeggio([74,78,81,86,90],step=.065,inst="bell",gain=.25); d.voice("choir",74,.08,.5,.35); d.noise(.2,.45,5000,13000,.08,attack=.2)
    elif name=="dark":
        d.voice("dark_drone",36,0,.6,.65); d.sweep(.1,.65,380,55,.5,shape="saw"); d.voice("choir",49,.15,.45,.25); d.noise(.4,.5,300,2200,.2)
    elif name in ("sword","axe","spear","dagger"):
        cfg={"sword":(.17,900,11000,81),"axe":(.29,150,3200,55),"spear":(.2,1700,14000,88),"dagger":(.11,2800,16000,98)}
        dur,lo,hi,p=cfg[name]
        d.noise(0,dur,lo,hi,.45,attack=dur*.3); d.voice("glock",p,dur*.65,gain=.13); d.noise(dur*.7,.09,400,7000,.45)
        d.sweep(dur*.7,.13,170 if name=="axe" else 340,70,.35)
    elif name=="bow":
        d.voice("pizz",67,0,.1,.55); d.sweep(.02,.25,1400,180,.15,shape="triangle"); d.noise(.04,.24,3500,15000,.2,attack=.015)
    elif name=="staff":
        d.voice("frame_drum",60,0,gain=.5); d.arpeggio([62,69,74],.08,.06,"glass_harmonica",.5); d.noise(0,.1,200,3000,.25)
    elif name=="hit":
        d.voice("tom",43,0,gain=.65); d.noise(0,.16,200,6500,.6)
    elif name=="critical":
        d.voice("taiko",34,0,gain=.6); d.noise(0,.25,300,14000,.6); d.voice("glock",94,.03,gain=.18); d.sweep(.05,.3,230,40,.4)
    elif name=="guard":
        d.voice("bell",54,0,gain=.2); d.voice("glock",70,0,gain=.25); d.noise(0,.07,1600,8000,.35)
    elif name=="miss":
        d.noise(0,.28,1800,10000,.3,attack=.07); d.sweep(.02,.2,800,240,.08)
    elif name in ("heal","buff","regen","revive"):
        notes={"heal":[72,76,79,84],"buff":[62,69,74,81],"regen":[79,76,72,76,79],"revive":[60,67,72,76,79,84,88]}[name]
        d.arpeggio(notes,step=.14 if name=="revive" else .09,inst="harp",gain=.4)
        d.voice("choir" if name=="revive" else "warm_pad",notes[0],.05,.8 if name=="revive" else .35,.35)
        d.noise(.12,.5,4500,13000,.06,attack=.15)
    elif name=="debuff":
        d.arpeggio([73,67,61,55],step=.09,inst="glass_harmonica",gain=.5); d.sweep(0,.5,260,75,.2,shape="saw")
    elif name=="poison":
        for i in range(6): d.sweep(i*.11,.18,380+i*25,95+i*10,.22)
        d.noise(.05,.8,150,1100,.3); d.voice("clarinet",49,.1,.35,.3)
    elif name=="burn":
        for i in range(8): d.noise(i*.085,.11,1000,10000,.25+(i%2)*.15)
        d.sweep(0,.55,110,55,.25)
    elif name=="freeze":
        d.voice("glass_harmonica",90,0,.5,.45); d.voice("sleigh",60,.03,gain=.5); d.noise(.05,.55,4000,16000,.2,attack=.05)
    elif name=="shock":
        for i in range(7):
            d.noise(i*.065,.045,1000,14000,.4); d.sweep(i*.065,.045,1600,500,.2,shape="square")
    elif name=="sleep":
        d.arpeggio([79,76,72,67],step=.18,inst="music_box",gain=.3); d.voice("air_pad",67,0,.65,.3)
    elif name=="silence":
        d.noise(0,.38,200,2500,.3,attack=.04); d.sweep(0,.35,780,180,.25,shape="triangle"); d.voice("glass_harmonica",61,.1,.25,.25)
    elif name=="stun":
        d.voice("rim",60,0,gain=.55); d.arpeggio([83,78,85,80,87],.06,.08,"glock",.18)
    elif name=="death":
        d.voice("cello",48,0,.8,.55); d.sweep(.08,1.3,240,38,.3,shape="saw"); d.noise(.2,1,150,1800,.22)
    elif name.startswith("ultimate_"):
        role=name.split("_")[1]
        d.voice("riser",55,0,.8,.45)
        if role=="warrior":
            for i in range(4):
                d.noise(.75+i*.19,.25,300,12000,.5); d.voice("taiko",32+i*2,.75+i*.19,gain=.65)
            d.voice("brass",50,1.35,.65,.6); d.voice("brass",57,1.35,.65,.45); d.voice("crash",60,1.35,gain=.5)
        elif role=="mage":
            d.arpeggio([60,63,67,72,75,79,84,87],.25,.075,"glass_harmonica",.4)
            d.voice("choir",60,.8,.8,.6); d.voice("taiko",28,.9,gain=.55); d.noise(.9,.9,100,8000,.6); d.sweep(.9,.9,1800,65,.3,shape="saw")
        elif role=="ranger":
            for i in range(8):
                d.voice("pizz",74+i%3*2,.6+i*.1,gain=.35); d.noise(.62+i*.1,.13,2600,15000,.35,pan=(i%3-1)*.6)
            d.voice("glock",96,1.4,gain=.2); d.voice("tom",45,1.4,gain=.65)
        else:
            d.arpeggio([62,66,69,74,78,81,86,90],.2,.09,"bell",.22)
            for pitch in (62,66,69,74): d.voice("choir",pitch,.8,1,.3)
            d.voice("crash",60,.9,gain=.2); d.noise(.9,.8,5000,15000,.12,attack=.2)
    else:
        raise ValueError(name)
    return d.finish(.18 if name.startswith("ultimate") else .1)
