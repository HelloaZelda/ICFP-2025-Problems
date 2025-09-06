# ICFP 2025 problem
# AUTHORS: kiwi;lucas
#已测试通过
#解题模式:
#   solver.py --solve --problem <problem> --n <room number> --no-conformance
import argparse, dataclasses, os, pickle, random, requests
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Set

BASE_URL = "https://31pwr5t6ij.execute-api.eu-west-2.amazonaws.com"
SIGMA = ["0","1","2","3","4","5"]
DEBUG = False  # 需要时开

noop = lambda *a, **k: None  # 留着占位

def dbg(*a):
    if DEBUG: print(*a)

# def http_post(url, json, timeout):
#     return requests.post(url, json=json, timeout=timeout)
# 直接requ

# http
class Api:
    def __init__(self, tid: Optional[str]=None, s: Optional[requests.Session]=None):
        self.id = tid; self.s = s or requests.Session()
    def reg(self, name: str, pl: str, email: str) -> str:
        r = self.s.post(f"{BASE_URL}/register", json={"name":name,"pl":pl,"email":email}, timeout=30)
        r.raise_for_status(); self.id = r.json().get("id")
        try:
            with open("team_id.txt","w",encoding="utf-8") as f: f.write(self.id)
        except Exception as _e:  #忽略失败
            pass
        return self.id
    def sel(self, prob: str) -> str:
        assert self.id, "no team id"
        r = self.s.post(f"{BASE_URL}/select", json={"id":self.id,"problemName":prob}, timeout=30)
        r.raise_for_status(); return r.json()["problemName"]
    def exp(self, plans: List[str]):
        assert self.id, "no team id"
        r = self.s.post(f"{BASE_URL}/explore", json={"id":self.id,"plans":plans}, timeout=60)
        r.raise_for_status(); j=r.json(); return j.get("results",[]), j.get("queryCount",0)
    def gss(self, rooms: List[int], start: int, conns: List[Dict]) -> bool:
        assert self.id, "no team id"
        payload = {"id":self.id, "map":{"rooms":rooms,"startingRoom":start,"connections":conns}}
        r = self.s.post(f"{BASE_URL}/guess", json=payload, timeout=60)
        r.raise_for_status(); return bool(r.json().get("correct", False))
@dataclasses.dataclass
class Cfg:
    n: int; f: int=18; keep: bool=False; path: str="cache.pkl"

class Oracle:
    def __init__(self, api: Api, cfg: Cfg):
        self.api=api; self.cfg=cfg
        self.last: Dict[str,int]={}; self.seq: Dict[str,List[int]]={}
        if cfg.keep and os.path.exists(cfg.path):
            try:
                with open(cfg.path,"rb") as fh:
                    d=pickle.load(fh)
                self.last=d.get("last",{}); self.seq=d.get("seq",{})
            except Exception as e:
                dbg("cache load fail:", e)
    def _save(self):
        if self.cfg.keep:
            try:
                with open(self.cfg.path,"wb") as fh:
                    pickle.dump({"last":self.last,"seq":self.seq}, fh)
            except Exception as e:
                dbg("cache save fail:", e)
    def many(self, words: List[str]) -> List[int]:
        uniq, seen = [], set()
        #循环；
        for w in words:
            if w not in seen: uniq.append(w); seen.add(w)
        need=[w for w in uniq if w not in self.last]
        if need: self._exp(need)
        return [self.last[w] for w in words]
    def one(self, w: str) -> int:
        if w not in self.last: self._exp([w])
        return self.last[w]
    def _exp(self, words: List[str]):
        cap=self.cfg.f*self.cfg.n; i=0; k=0
        while i<len(words):
            total=0; batch=[]
            while i<len(words):
                w=words[i]; L=len(w)
                if L==0: batch.append(w); i+=1; continue
                if total+L<=cap or not batch:
                    batch.append(w); total+=L; i+=1
                else: break
            k+=1; res,qc=self.api.exp(batch)
            print(f"/explore[{k}] p={len(batch)} s={total} q={qc}")  
            for w,seq in zip(batch,res):
                # 稳妥 for
                self.seq[w]=seq; self.last[w]=seq[-1]
        self._save()

# learner
class LStar:
    def __init__(self, O: Oracle, sigma: List[str]=SIGMA):
        self.O=O; self.S=[""]; self.E=[""]
        self.T: Dict[Tuple[str,str],int]={}; self.sigma=list(sigma)
    def _cell(self,p,e):
        if (p,e) not in self.T:
            self.T[(p,e)]=self.O.one(p+e)
    def _row(self,p):
        for e in self.E: self._cell(p,e)
        return tuple(self.T[(p,e)] for e in self.E)
    def _sdot(self):
        out=[]
        for p in self.S:
            for a in self.sigma: out.append(p+a)
        return out
    def _addE(self,e):
        if e not in self.E:
            self.E.append(e)
            #先补 S，再补 S·Σ
            for p in self.S: self._cell(p,e)
            for p in self._sdot(): self._cell(p,e)
    def learn(self):
        # init
        for p in self.S+self._sdot(): self._row(p)
        # loop
        while True:
            ch=False
            # closure
            add=True
            while add:
                add=False; rows=[self._row(p) for p in self.S]
                for q in self._sdot():
                    if self._row(q) not in rows:
                        self.S.append(q); ch=True; add=True
            # consistency
            M=defaultdict(list)
            for p in self.S: M[self._row(p)].append(p)
            br=False
            for ps in M.values():
                if len(ps)<=1: continue
                for i in range(len(ps)):
                    for j in range(i+1,len(ps)):
                        p,q=ps[i],ps[j]
                        for a in self.sigma:
                            if self._row(p+a)!=self._row(q+a):
                                for e in self.E:
                                    if self.T[(p+a,e)]!=self.T[(q+a,e)]:
                                        self._addE(a+e); ch=True; br=True; break
                                break
                        if br: break
                    if br: break
                if br: break
            if not ch: break
        return self._build()
    @dataclasses.dataclass
    class M:
        outs: List[int]; trans: List[List[int]]; reps: List[str]; sigma: List[str]
        def run_last(self,w:str)->int:
            s=0
            for ch in w: s=self.trans[s][ord(ch)-48]
            return self.outs[s]
    def _build(self)->"LStar.M":
        rows: Dict[Tuple[int,...],int]={}; reps: List[str]=[]; outs: List[int]=[]
        for p in sorted(self.S,key=len):
            r=self._row(p)
            if r not in rows:
                rows[r]=len(rows); reps.append(p); outs.append(self.T[(p,"")])
        n=len(rows); trans=[[0]*len(self.sigma) for _ in range(n)]
        for p in reps:
            s=rows[self._row(p)]
            for a in self.sigma:
                t=rows[self._row(p+a)]; trans[s][ord(a)-48]=t
        return LStar.M(outs,trans,reps,self.sigma)

# check
def check(m: LStar.M, O: Oracle, depth=3, samples=200)->bool:
    ws=["".join(random.choice(SIGMA) for _ in range(random.randint(0,depth))) for _ in range(samples)]
    O.many(ws)
    return all(m.run_last(w)==O.last[w] for w in ws)

# guess
def build_guess(m: LStar.M):
    rooms=m.outs[:]; start=0; seen:Set[Tuple[int,int,int,int]]=set(); conns:List[Dict]=[]
    for s in range(len(m.outs)):
        for ai,_ in enumerate(m.sigma):
            t=m.trans[s][ai]
            back=next((j for j in range(6) if m.trans[t][j]==s),0)
            key=(min(s,t), ai if s<=t else back, max(s,t), back if s<=t else ai)
            if key in seen: continue
            seen.add(key); conns.append({"from":{"room":s,"door":ai},"to":{"room":t,"door":back}})
    return rooms,start,conns

# util
def tid_from(cli: Optional[str])->Optional[str]:
    if cli: return cli
    env=os.getenv("TEAM_ID") or os.getenv("TEAMID")
    if env: return env
    try:
        t=open("team_id.txt","r",encoding="utf-8").read().strip()
        if t: return t
    except Exception as e:
        dbg("tid file fail:", e)
    return None

def mask(tid:str)->str:
    if not tid: return "<none>"
    if " " in tid:
        u,t=tid.split(" ",1); return f"{u} {t[:4]}…{t[-4:]}"
    return tid[:4]+"…"+tid[-4:]

# cli
def main():
    ap=argparse.ArgumentParser(description="ICFP 2025 oneshot")
    ap.add_argument("--name"); ap.add_argument("--email"); ap.add_argument("--pl",default="python")
    ap.add_argument("--register",action="store_true"); ap.add_argument("--id")
    ap.add_argument("--problem"); ap.add_argument("--n",type=int,default=6)
    ap.add_argument("--learn",action="store_true"); ap.add_argument("--guess",action="store_true")
    ap.add_argument("--solve",action="store_true")
    ap.add_argument("--persist-cache",action="store_true")
    ap.add_argument("--depth",type=int,default=3); ap.add_argument("--samples",type=int,default=200)
    ap.add_argument("--no-conformance",action="store_true") #解题模式
    ap.add_argument("--debug",action="store_true") 
    args=ap.parse_args(); globals()["DEBUG"]=bool(args.debug)

    api=Api(tid_from(args.id))
    if not api.id and args.register:
        print("Reg:", api.reg(args.name,args.pl,args.email))
    elif not api.id:
        raise SystemExit("no team id: --id / TEAM_ID / team_id.txt / --register")
    print("Team:", mask(api.id))

    def run(sel: bool, do_g: bool):
        if sel: print("Sel:", api.sel(args.problem))
        O=Oracle(api, Cfg(args.n, keep=args.persist_cache))
        M=LStar(O).learn(); print(f"Model: {len(M.outs)} states")
        if do_g:
            if not args.no_conformance:
                ok=check(M,O,args.depth,args.samples); print("Chk:", "PASS" if ok else "FAIL/SKIP")
            r,s,c=build_guess(M); print("Guess:", api.gss(r,s,c))

    if args.solve:
        if not args.problem: raise SystemExit("--solve needs --problem")
        run(True,True); return
    if args.problem and (args.learn or args.guess): run(True,args.guess); return
    if args.learn or args.guess: run(False,args.guess); return
    if args.problem and not (args.learn or args.guess or args.solve): print("Sel:", api.sel(args.problem)); return
if __name__=="__main__":
    main()
# GoodJob!
