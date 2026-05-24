#!/usr/bin/env python3
import argparse
import bisect
import math
import random


def print_ring(ids, cur, fingers, target, radius=20):
    """
    ASCII circular diagram with:
      C  = current node
      T  = target
      f# = finger entries (f1, f2, ...)
    Zero ID is anchored at the TOP of the ring.
    """

    # Grid will be double-width (for two-character labels)
    size = radius * 2 + 1
    grid = [[" " for _ in range(size * 2)] for _ in range(size)]

    # Angle mapping: 0 at top, clockwise positive
    def angle(x):
        a = (2 * math.pi) * ((x % (2**16)) / (2**16))
        return a - math.pi / 2  # rotate so 0 is at top

    # Draw circular outline
    for deg in range(360):
        rad = math.radians(deg)
        x = int(radius + radius * math.cos(rad))
        y = int(radius + radius * math.sin(rad))
        gx = x * 2
        if 0 <= y < size and 0 <= gx < size * 2:
            if grid[y][gx] == " ":
                grid[y][gx] = "."

    # Prepare labels
    items = []
    # Fingers first
    for i, fid in enumerate(fingers.get(cur, [])):
        items.append((f"f{i+1}", fid))
    # Target second
    items.append(("T", target))
    # Current node LAST so it overwrites others
    items.append(("C", cur))

    # Draw labeled points
    for label, node_id in items:
        a = angle(node_id)
        x = int(radius + radius * math.cos(a))
        y = int(radius + radius * math.sin(a))
        gx = x * 2
        # Place label safely inside bounds
        for i, ch in enumerate(label):
            if 0 <= y < size and 0 <= gx + i < size * 2:
                grid[y][gx + i] = ch

    # Print diagram
    print("\n      DHT Ring View")
    for row in grid:
        print("".join(row))

    # Numeric legend
    print("\nLabels:")
    print(f"  C  = {cur}")
    for i, fid in enumerate(fingers.get(cur, [])):
        print(f"  f{i+1} = {fid}")
    print(f"  T  = {target}")
    print()


def make_ring(n=100, bits=16):
    ids = sorted(random.sample(range(2**bits), n))
    return ids, bits


def build_fingers(ids, bits, min_f=5, max_f=8):
    # each node has 5-8 random successors within 1/2 ring distance
    n = len(ids)
    fingers = {}

    for idx, idv in enumerate(ids):
        fingers[idv] = []
        succs = set()
        seen = set()

        for i in range(bits):
            offset = 2**i
            target = (idv + offset) % (2**bits)
            if target > ids[-1]:
                target = -1
            bisect_idx = bisect.bisect_right(ids, target)
            if bisect_idx >= len(ids):
                bisect_idx = 0
            f_idx = ids[bisect_idx]
            if f_idx in seen:
                continue
            seen.add(f_idx)
            fingers[idv].append(f_idx)

    return fingers


def successor(ids, key):
    for i, idv in enumerate(ids):
        if idv >= key:
            return idv
    return ids[0]


def ring_distance(start, end, bits):
    return (end - start) % (2**bits)


def greedy_route(ids, fingers, start, key, bits=16):
    goal = successor(ids, key)
    path = [start]
    cur = start
    seen = {start}
    max_hops = len(ids)

    while cur != goal and len(path) <= max_hops:
        options = fingers[cur]
        goal_dist = ring_distance(cur, goal, bits)
        nxt = options[0]

        for candidate in options:
            if candidate == goal:
                nxt = candidate
                break

            candidate_dist = ring_distance(cur, candidate, bits)
            if 0 < candidate_dist < goal_dist:
                nxt = candidate

        if nxt in seen:
            break

        cur = nxt
        path.append(cur)
        seen.add(cur)

    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", default="small")
    ap.add_argument("--auto", action="store_true")
    args = ap.parse_args()

    ids, bits = make_ring(100, 16)
    fingers = build_fingers(ids, bits)
    start = random.choice(ids)
    # pick target at least 3 hops away
    idx = ids.index(start)
    target = random.randint(
        0, 2**bits
    )  # ids[(idx + random.randint(10, 20)) % len(ids)]
    print("ReliefLedger DHT (field network)")
    print_ring(ids, start, fingers, target)
    print(f"You are node {start}.")
    print(f"Your finger table ({len(fingers[start])} entries):")
    for f in fingers[start]:
        print(f"  -> {f}")
    print(f"Target file hash (key): {target}\n")
    goal = successor(ids, target)

    if args.auto:
        path = greedy_route(ids, fingers, start, target, bits)
        hops = len(path) - 1
        cur = path[-1]
        if cur != goal:
            print(f"Routing failed to reach responsible node {goal}.")
            print(f"Your path: ({hops} hops) {' -> '.join(map(str,path))}")
            return
        print(f"Reached responsible node {goal} in {hops} hops.")
        print(f"Your path: ({hops} hops) {' -> '.join(map(str,path))}")
        print(f"Optimal path: ({hops} hops) {' -> '.join(map(str,path))}")
        return

    cur = start
    path = [cur]
    hops = 0
    while True:
        if cur == goal:
            print(f"Reached responsible node {goal} in {hops} hops.")
            opt = greedy_route(ids, fingers, start, target, bits)
            print(f"Your path: ({len(path) - 1} hops) {' -> '.join(map(str,path))}")
            print(f"Optimal path: ({len(opt) - 1} hops) {' -> '.join(map(str,opt))}")
            break
        print("Enter next node ID (from your finger table): ", end="")
        try:
            nxt = int(input().strip())
        except:
            print("Invalid.")
            break
        if nxt not in fingers[cur]:
            print("That node is not in your finger table! Try again.")
            continue
        cur = nxt
        path.append(cur)
        hops += 1
        print(f"Hop {hops} -> Node {cur}")
        print_ring(ids, cur, fingers, target)
        print(f"Finger table ({len(fingers[cur])} entries):")
        for f in fingers[cur]:
            print(f"  -> {f}")
        print(f"Target still {target}\n")
        if hops > 15:
            print("Too many hops; giving up.")
            break


if __name__ == "__main__":
    main()
