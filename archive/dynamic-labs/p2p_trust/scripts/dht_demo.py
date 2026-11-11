#!/usr/bin/env python3
import argparse
import bisect
import math
import random


def print_ring(ids, cur, fingers, target, bits=16, radius=20):
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
    goal = successor(ids, target)
    print(f"  C  = {cur}")
    for i, fid in enumerate(fingers.get(cur, [])):
        owner_note = "  (owner of T)" if fid == goal else ""
        print(f"  f{i+1} = {fid}{owner_note}")
    print(f"  T  = key {target} (file hash, not usually a node)")
    print(f"  owner(T) = {goal} (first node clockwise at or after T)")
    print()


def make_ring(n=100, bits=16):
    ids = sorted(random.sample(range(2**bits), n))
    return ids, bits


def build_fingers(ids, bits, min_f=5, max_f=8):
    # Chord finger i points to the successor of node_id + 2**i.
    fingers = {}
    ring_size = 2**bits

    for idv in ids:
        fingers[idv] = []
        seen = set()

        for i in range(bits):
            offset = 2**i
            target = (idv + offset) % ring_size
            bisect_idx = bisect.bisect_left(ids, target)
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


def choose_next(ids, fingers, cur, key, bits=16):
    goal = successor(ids, key)
    options = fingers[cur]
    target_dist = ring_distance(cur, key, bits)
    nxt = options[0]
    best_dist = 0

    for candidate in options:
        if candidate == goal:
            return candidate

        candidate_dist = ring_distance(cur, candidate, bits)
        if 0 < candidate_dist <= target_dist and candidate_dist > best_dist:
            nxt = candidate
            best_dist = candidate_dist

    return nxt


def greedy_route(ids, fingers, start, key, bits=16):
    goal = successor(ids, key)
    path = [start]
    cur = start
    seen = {start}
    max_hops = len(ids)

    while cur != goal and len(path) <= max_hops:
        nxt = choose_next(ids, fingers, cur, key, bits)
        if nxt in seen:
            break

        cur = nxt
        path.append(cur)
        seen.add(cur)

    return path


def print_finger_table(ids, fingers, cur, target, bits=16):
    goal = successor(ids, target)
    target_dist = ring_distance(cur, target, bits)
    print(f"Finger table ({len(fingers[cur])} entries):")
    for fid in fingers[cur]:
        dist = ring_distance(cur, fid, bits)
        if fid == goal:
            if fid == target:
                note = "exact T node"
            else:
                note = "owner of T (successor of key)"
        elif 0 < dist <= target_dist:
            note = "before T"
        else:
            note = "past T"
        print(f"  -> {fid}  ({note}, +{dist} clockwise)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", default="small")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--seed", type=int, help="Set a random seed for replaying a route")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    ids, bits = make_ring(100, 16)
    fingers = build_fingers(ids, bits)
    start = random.choice(ids)
    target = random.randrange(2**bits)
    print("ReliefLedger DHT (field network)")
    print_ring(ids, start, fingers, target, bits)
    print(f"You are node {start}.")
    print_finger_table(ids, fingers, start, target, bits)
    goal = successor(ids, target)
    print(f"Target file hash (T key): {target}")
    print(f"Responsible owner node: {goal}")
    print("Route to owner(T), the first node clockwise at or after T.\n")

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
        print(f"Greedy reference path: ({hops} hops) {' -> '.join(map(str,path))}")
        return

    cur = start
    path = [cur]
    hops = 0
    while True:
        if cur == goal:
            print(f"Reached responsible node {goal} in {hops} hops.")
            opt = greedy_route(ids, fingers, start, target, bits)
            print(f"Your path: ({len(path) - 1} hops) {' -> '.join(map(str,path))}")
            print(f"Greedy reference path: ({len(opt) - 1} hops) {' -> '.join(map(str,opt))}")
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
        print_ring(ids, cur, fingers, target, bits)
        print_finger_table(ids, fingers, cur, target, bits)
        print(f"Target still {target}")
        print("Choose the furthest clockwise finger before T; if none exists, use the first finger.\n")
        if hops > 15:
            print("Too many hops; giving up.")
            break


if __name__ == "__main__":
    main()
