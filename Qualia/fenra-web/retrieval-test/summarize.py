import json
res=json.load(open("results.json"))
for r in res:
    print("=====",r["label"],"| dim",r["dim"],"| embed s",r["embed_seconds"])
    for v,rows in r["variants"].items():
        rel=[x for x in rows if x["expected"]]
        d0=sum(1 for x in rel if any(d==0 for d in x["found_depth"].values() if d is not None))
        allfound=[(e,d) for x in rel for e,d in x["found_depth"].items()]
        n=len(allfound)
        by=lambda m:sum(1 for e,d in allfound if d is not None and d<=m)
        print(f"-- {v}: Qs with >=1 expected in top3: {d0}/{len(rel)}; expected memories found d0 {by(0)}/{n}, d<=1 {by(1)}/{n}, d<=2 {by(2)}/{n}; avg set size {sum(x['total'] for x in rows)/len(rows):.1f}")
        for x in rows:
            print(f"  {x['q'][:55]:55} top1={x['top1_sim']} found={x['found_depth']} ranks={list(x['rank_of_expected'].values())} d0w={x['weaves_d0']}")
