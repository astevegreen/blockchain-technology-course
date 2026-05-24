#!/usr/bin/env python3
import json, pathlib, random, numpy as np
DATA = pathlib.Path(__file__).resolve().parents[1]/"data"
ngos=json.load(open(DATA/"ngos.json"))
ends=json.load(open(DATA/"endorsements.json")) if (DATA/"endorsements.json").exists() else []
N=len(ngos)
id2idx={n["id"]:i for i,n in enumerate(ngos)}
M=np.zeros((N,N))
for e in ends:
    if e["src"] in id2idx and e["dst"] in id2idx:
        M[id2idx[e["dst"]], id2idx[e["src"]]]=1
for j in range(N):
    s=M[:,j].sum()
    if s>0: M[:,j]/=s
t=np.ones(N)/N
for _ in range(20): t=M@t; t/=t.sum()
cred=M.sum(axis=1); peer=np.ones(N)+cred; peer/=peer.sum()
print("Top 10 NGOs by EigenTrust:")
for i in np.argsort(-t)[:10]:
    print(f"{ngos[i]['name']:15s}  score={t[i]:.4f}")
print("\nTop 10 by PeerTrust:")
for i in np.argsort(-peer)[:10]:
    print(f"{ngos[i]['name']:15s}  score={peer[i]:.4f}")