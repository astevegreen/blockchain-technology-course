#!/usr/bin/env python3
import random, argparse

def choose(stakes):
    total=sum(stakes.values())
    r=random.uniform(0,total)
    s=0
    for k,v in stakes.items():
        s+=v
        if s>=r: return k

def simulate(rounds):
    stakes={c:random.randint(10,50) for c in "ABCDE"}
    for r in range(1,rounds+1):
        proposer=choose(stakes)
        stakes[proposer]+=0.02*stakes[proposer]
        print(f"Round {r} proposer {proposer}, stakes {stakes}")
    print("Final",stakes)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--rounds",type=int,default=15)
    args=ap.parse_args()
    simulate(args.rounds)
