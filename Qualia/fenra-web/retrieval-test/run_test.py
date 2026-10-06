import json, math, time, urllib.request, collections, sys
from test_data import MEMORIES, QUESTIONS
MODEL="embeddinggemma"
def embed(texts):
    req=urllib.request.Request("http://localhost:11434/api/embed",
        data=json.dumps({"model":MODEL,"input":texts,"keep_alive":"2m"}).encode(),
        headers={"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(req,timeout=300))["embeddings"]
def norm(v):
    n=math.sqrt(sum(x*x for x in v)); return [x/n for x in v]
def cos(a,b): return sum(x*y for x,y in zip(a,b))
ids=[m[0] for m in MEMORIES]; weave={m[0]:m[1] for m in MEMORIES}; text={m[0]:m[2] for m in MEMORIES}
size=collections.Counter(weave.values()); mean=sum(size.values())/len(size)
DEPTH_W=[1.0,0.75,0.25]
def walk(r, mv, key=lambda i,s:s, k=3):
    sims={i:cos(r,mv[i]) for i in ids}
    score=lambda i: key(i,sims[i])
    level0=sorted(ids,key=lambda i:-score(i))[:k]
    seen={i:0 for i in level0}; frontier=level0
    for d in (1,2):
        new=[]
        for h in frontier:
            nb=sorted([i for i in ids if i!=h and i not in seen],key=lambda i:-key(i,cos(mv[h],mv[i])))[:k]
            for i in nb:
                if i not in seen: seen[i]=d; new.append(i)
        frontier=new
    return sims,seen
def run(label,qpre,dpre):
    t=time.time()
    mv=dict(zip(ids,map(norm,embed([dpre+text[i] for i in ids]))))
    qv=[norm(v) for v in embed([qpre+q[0] for q in QUESTIONS])]
    out={"label":label,"embed_seconds":round(time.time()-t,2),"dim":len(qv[0]),"questions":[]}
    for variant,key in (("plain",lambda i,s:s),("weave-size-weighted",lambda i,s:s*(mean/size[weave[i]]))):
        rows=[]
        for (q,exp,note),r in zip(QUESTIONS,qv):
            sims,seen=walk(r,mv,key)
            ranked=sorted(ids,key=lambda i:-key(i,sims[i]))
            d0=[i for i,d in seen.items() if d==0]
            found={e:(seen.get(e,None)) for e in exp}
            rows.append(dict(q=q,note=note,expected=exp,found_depth=found,
              rank_of_expected={e:ranked.index(e)+1 for e in exp},
              top3=[(i,round(sims[i],3),weave[i]) for i in d0],
              top1_sim=round(max(sims.values()),3),total=len(seen),
              weaves_d0=dict(collections.Counter(weave[i] for i in d0)),
              weaves_all=dict(collections.Counter(weave[i] for i in seen))))
        out.setdefault("variants",{})[variant]=rows
    return out
res=[run("plain (no task prefix)","",""),
     run("with embeddinggemma task prefixes","task: search result | query: ","title: none | text: ")]
json.dump(res,open("results.json","w"),indent=1)
print("done")
