#!/usr/bin/env python3
import argparse, random


def make_graph(n=10, deg=3):
    if deg >= n:
        raise ValueError("degree must be smaller than node count")
    neighbors = {i: set() for i in range(n)}
    for i in range(n):
        while len(neighbors[i]) < deg:
            j = random.randrange(n)
            if j != i:
                neighbors[i].add(j)
                neighbors[j].add(i)
    return neighbors


def lookup(neighbors, start, target):
    visited = {start}
    hops = 0
    cur = start
    while True:
        if cur == target:
            print(f"Found file at node {target} in {hops} hops.")
            return
        print(f"File isn't on node {cur}.")
        print(f"Node {cur} knows: {sorted(neighbors[cur])}")
        try:
            nxt = int(input("Choose next node to query: ").strip())
        except ValueError:
            print("Invalid node ID. Try again.")
            continue
        if nxt not in neighbors[cur]:
            print("Not a neighbor. Try again.")
            continue
        if nxt in visited:
            print("WARNING: Already visited.")
        visited.add(nxt)
        hops += 1
        cur = nxt
        if hops > 20:
            print("Search failed.")
            break


def broadcast(neighbors, fanout=3):
    start = random.randrange(len(neighbors))
    informed = {start}
    steps = 0
    messages = 0
    print(f"Broadcast starts at node {start}.")
    while len(informed) < len(neighbors):
        new = set()
        for u in list(informed):
            targets = random.sample(
                sorted(neighbors[u]),
                min(fanout, len(neighbors[u])),
            )
            for v in targets:
                messages += 1
                if v not in informed:
                    new.add(v)
        informed |= new
        steps += 1
        print(f"Round {steps}: reached {len(informed)}/{len(neighbors)} nodes")
        if steps > 20:
            break
    print(f"Broadcast complete in {steps} rounds, {messages} messages.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["lookup", "broadcast"], required=True)
    ap.add_argument("--seed", type=int, help="Set a random seed for replaying a run")
    args = ap.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    neighbors = make_graph(20, deg=4)
    if args.mode == "lookup":
        start = random.randrange(20)
        target = random.randrange(20)
        while target == start:
            target = random.randrange(20)
        print(
            f"Start from node {start} to find target file by searching across different nodes."
        )
        lookup(neighbors, start, target)
    else:
        broadcast(neighbors, fanout=3)


if __name__ == "__main__":
    main()
