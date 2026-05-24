#!/usr/bin/env python3
import argparse, json, os, statistics, pathlib, random
import numpy as np

BASE = pathlib.Path(__file__).resolve().parents[1]
DATA = BASE / "data"
NGO_FILE = DATA / "ngos.json"
END_FILE = DATA / "endorsements.json"
BASELINE_FILE = DATA / "baseline.json"
PROGRESS_FILE = DATA / "progress.json"
PATCH_FLAG = DATA / "patch_active.flag"


def load_current():
    return json.load(open(NGO_FILE)), json.load(open(END_FILE))


def load_baseline():
    return json.load(open(BASELINE_FILE))["ngos"]


def save(ngos, ends):
    json.dump(ngos, open(NGO_FILE, "w"), indent=2)
    json.dump(ends, open(END_FILE, "w"), indent=2)


def reset():
    baseline = load_baseline()
    save(baseline, [])
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
    if PATCH_FLAG.exists():
        PATCH_FLAG.unlink()
    print("Reset: baseline NGOs restored, endorsements cleared, patch disabled.")


def register():
    ngos, ends = load_current()
    name = input("Enter new NGO name: ").strip()
    if any(n["name"] == name for n in ngos):
        print("Name already exists.")
        return

    # Generate a random 6-digit ID
    while True:
        new_id = random.randint(100000, 999999)
        if not any(n["id"] == new_id for n in ngos):
            break

    ngos.append(
        {"id": new_id, "name": name, "age": 0, "verified": False, "baseline_score": 0}
    )
    save(ngos, ends)
    print(f"Registered {name} (id={new_id}, unverified).")


def endorse():
    ngos, ends = load_current()

    # Step 1: Blind prompt for the endorser ID
    try:
        src = int(input("Endorser NGO id: "))
    except ValueError:
        print("Invalid input. ID must be an integer.")
        return

    src_ngo = next((n for n in ngos if n["id"] == src), None)

    if not src_ngo:
        print("Invalid endorser NGO id.")
        return

    # Restrict endorsements if patch is active
    if PATCH_FLAG.exists():
        if not src_ngo["verified"] or src_ngo["age"] < 7:
            print(
                "This NGO cannot endorse after the patch (must be verified and age >= 7)."
            )
            return

    # Step 2: Show available targets by name only
    print("\nAvailable targets:")
    for n in ngos:
        if n["id"] != src:
            print(f"  - {n['name']}")

    dst_name = input("\nTarget NGO name: ").strip()
    dst_ngo = next((n for n in ngos if n["name"] == dst_name), None)

    if not dst_ngo:
        print("Invalid target NGO name.")
        return

    dst = dst_ngo["id"]

    if any(e["src"] == src and e["dst"] == dst for e in ends):
        print("Already endorsed.")
        return

    ends.append({"src": src, "dst": dst})
    save(ngos, ends)
    print(f"Endorsement from {src_ngo['name']} to {dst_ngo['name']} recorded.")


def compute_scores():
    ngos, ends = load_current()
    score_map = {n["id"]: n["baseline_score"] for n in ngos}
    for e in ends:
        if e["dst"] in score_map:
            score_map[e["dst"]] += 1
    return ngos, score_map


def score():
    ngos, score_map = compute_scores()
    med = statistics.median(score_map.values()) if score_map else 0
    patch_active = PATCH_FLAG.exists()

    # Dynamically show the Verified column only if the patch is active
    if patch_active:
        print(f"{'ID':>6}  {'Name':<15} {'Endorsements':>12}  {'Age':>3}  {'Verified'}")
    else:
        print(f"{'ID':>6}  {'Name':<15} {'Endorsements':>12}  {'Age':>3}")

    for n in ngos:
        s = score_map[n["id"]]
        flag = "*ANOMALY*" if med > 0 and s > 5 * med else ""

        if patch_active:
            print(
                f"{n['id']:>6}  {n['name']:<15} {s:>12}  {n['age']:>3}  {str(n['verified']):<8} {flag}"
            )
        else:
            print(f"{n['id']:>6}  {n['name']:<15} {s:>12}  {n['age']:>3}  {flag}")

    if any(s > 5 * med for s in score_map.values()):
        json.dump({"stage": 2}, open(PROGRESS_FILE, "w"))
        print("FLAG{step2_ngospoof}")


def patch():
    ngos, ends = load_current()
    valid = []

    for e in ends:
        src = e["src"]
        n = next((x for x in ngos if x["id"] == src), None)
        if n and n["verified"] and n["age"] >= 7:
            valid.append(e)

    save(ngos, valid)
    PATCH_FLAG.write_text("active")

    print(
        f"Patch applied. Removed {len(ends)-len(valid)} invalid endorsements. Blocking future invalid endorsements."
    )
    score()


def audit(args):
    ngos, ends = load_current()
    if not ngos:
        print("No NGOs found.")
        return

    _, score_map = compute_scores()
    naive_scores = [score_map[n["id"]] for n in ngos]

    N = len(ngos)
    id2idx = {n["id"]: i for i, n in enumerate(ngos)}

    M = np.zeros((N, N))
    for e in ends:
        if e["src"] in id2idx and e["dst"] in id2idx:
            M[id2idx[e["dst"]], id2idx[e["src"]]] = 1

    for j in range(N):
        s = M[:, j].sum()
        if s > 0:
            M[:, j] /= s

    p = np.zeros(N)
    trusted_count = 0
    for i, n in enumerate(ngos):
        if n["verified"] and n["baseline_score"] > 0:
            p[i] = 1.0
            trusted_count += 1

    if trusted_count > 0:
        p /= trusted_count
    else:
        p = np.ones(N) / N

    alpha = 0.15
    t = np.copy(p)
    for _ in range(20):
        t = (1 - alpha) * (M @ t) + alpha * p
        t /= t.sum()

    cred = M.sum(axis=1)
    peer = np.ones(N) + cred
    peer /= peer.sum()

    if getattr(args, "trace", None) is not None:
        trace_id = args.trace
        if trace_id not in id2idx:
            print(f"ID {trace_id} not found.")
            return
        idx = id2idx[trace_id]
        print(f"\n--- Trace for NGO {trace_id} ({ngos[idx]['name']}) ---")
        inbound = [
            (ngos[i]["id"], ngos[i]["name"], t[i]) for i in range(N) if M[idx, i] > 0
        ]
        print(f"Total Endorsements Received: {len(inbound)}")
        print("Trust flow from endorsers:")
        transfer = 0
        for src_id, src_name, src_trust in inbound:
            print(f"  <- [{src_id:>6}] {src_name:15} (EigenTrust: {src_trust:.4f})")
            transfer += src_trust
        print(f"Cumulative trusted inbound flow before damping: {transfer:.4f}")
        print(f"Final EigenTrust Score: {t[idx]:.4f}")
        print("-" * 50 + "\n")

    print(
        f"{'ID':>6} | {'Name':<15} | {'Naive':>5} | {'PeerTrust':>9} | {'EigenTrust':>10} | {'Pre-Trusted'}"
    )
    print("-" * 68)

    ranked_indices = np.argsort(-t)
    for i in ranked_indices:
        n = ngos[i]
        is_trusted = "★" if (n["verified"] and n["baseline_score"] > 0) else ""
        print(
            f"{n['id']:>6} | {n['name']:<15} | {naive_scores[i]:>5} | {peer[i]:>9.4f} | {t[i]:>10.4f} | {is_trusted:>6}"
        )


def scenario():
    print("=== ReliefLedger Reputation Audit Scenario ===")
    print("Run 'python3 ngo_sim.py score' to view the naive ledger.")
    print("Run 'python3 ngo_sim.py audit' to view advanced trust metrics.")
    print("Use register/endorse to explore behavior and attack the network.")
    print("Flags reveal next instructions.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    for cmd in ["register", "endorse", "score", "patch", "reset", "scenario"]:
        sub.add_parser(cmd)

    audit_parser = sub.add_parser("audit")
    audit_parser.add_argument(
        "--trace", type=int, help="Trace trust flow for a specific NGO ID"
    )

    args = ap.parse_args()

    if args.cmd == "register":
        register()
    elif args.cmd == "endorse":
        endorse()
    elif args.cmd == "score":
        score()
    elif args.cmd == "patch":
        patch()
    elif args.cmd == "audit":
        audit(args)
    elif args.cmd == "reset":
        reset()
    elif args.cmd == "scenario":
        scenario()
    else:
        print("Commands: register, endorse, score, audit, patch, reset, scenario")


if __name__ == "__main__":
    main()
