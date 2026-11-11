#!/usr/bin/env python3
import argparse
import random

###############################################################################
# CONFIGURATION
###############################################################################

# 6-bit Hex Space (000000 to FFFFFF)
ID_DIGITS = 6
ID_BASE = 16
NUM_NODES = 200

###############################################################################
# UTILITIES
###############################################################################

# ANSI Colors
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_RESET = "\033[0m"


def common_prefix_len(s1, s2):
    l = 0
    min_len = min(len(s1), len(s2))
    while l < min_len and s1[l] == s2[l]:
        l += 1
    return l


def diff(id1, id2):
    n1 = int(id1, 16)
    n2 = int(id2, 16)
    limit = 16**ID_DIGITS
    return min(abs(n1 - n2), limit - abs(n1 - n2))


###############################################################################
# PASTRY NODE CLASS
###############################################################################


class PastryNode:
    def __init__(self, node_id, all_nodes):
        self.node_id = node_id
        self.leaf_set = []
        self.routing_table = {}
        self._populate_state(all_nodes)

    def _populate_state(self, all_nodes):
        sorted_nodes = sorted(all_nodes)
        my_idx = sorted_nodes.index(self.node_id)

        # 1. Populate Leaf Set (8 closest neighbors)
        neighbors = []
        L = len(sorted_nodes)
        for i in range(-4, 5):
            if i == 0:
                continue
            neighbor = sorted_nodes[(my_idx + i) % L]
            neighbors.append(neighbor)

        self.leaf_set = sorted(neighbors, key=lambda x: diff(self.node_id, x))

        # 2. Populate Routing Table (Sparse)
        for node in all_nodes:
            if node == self.node_id:
                continue

            shl = common_prefix_len(self.node_id, node)
            if shl >= ID_DIGITS:
                continue

            next_digit = node[shl]

            if shl not in self.routing_table:
                self.routing_table[shl] = {}

            if next_digit not in self.routing_table[shl]:
                self.routing_table[shl][next_digit] = node

    # =========================================================================
    # THE BUGGY ROUTING FUNCTION
    # =========================================================================
    def get_next_hop(self, key):
        # 0. Am I the destination?
        if self.node_id == key:
            return self.node_id

        # 1. Prefix Routing Logic
        shl = common_prefix_len(self.node_id, key)
        next_digit = key[shl]

        # STUDENT PATCH AREA START
        # Replace everything from this line through STUDENT PATCH AREA END
        # with the exact code block shown in the lesson.
        # Check Routing Table
        if shl in self.routing_table and next_digit in self.routing_table[shl]:
            return self.routing_table[shl][next_digit]

        # 2. If no Routing Table entry...
        # BUG: A correct router should choose the closest known candidate from
        # both the prefix-table entry and the leaf set, then only forward if
        # that candidate moves closer to the key.
        return None
        # STUDENT PATCH AREA END


###############################################################################
# VISUALIZATION UTILS
###############################################################################


def print_node_state(node, target_key):
    """
    Dumps the full internal state of a node for debugging.
    """
    print(f"\n{C_BLUE}--- NODE {node.node_id} STATE ---{C_RESET}")
    print(f"Target Key: {target_key}")

    # 1. LEAF SET
    print(f"Leaf Set (Ring Neighbors):")
    # Highlight the best leaf if it exists
    best_leaf = min(node.leaf_set, key=lambda x: diff(x, target_key))
    dist_me = diff(node.node_id, target_key)
    dist_leaf = diff(best_leaf, target_key)

    formatted_leaves = []
    for leaf in node.leaf_set:
        if leaf == best_leaf and dist_leaf < dist_me:
            formatted_leaves.append(f"{C_GREEN}{leaf}{C_RESET}")
        else:
            formatted_leaves.append(leaf)

    leaf_str = "[" + ", ".join(formatted_leaves) + "]"
    print(f"  {leaf_str}")

    # 2. ROUTING TABLE
    print(f"Routing Table (Prefix Shortcuts):")
    if not node.routing_table:
        print("  (Empty)")
    else:
        for row_idx in sorted(node.routing_table.keys()):
            row = node.routing_table[row_idx]
            # Highlight matching prefix
            shl = common_prefix_len(node.node_id, target_key)
            prefix_marker = (
                f" {C_YELLOW}<-- PREFIX MATCH{C_RESET}" if row_idx == shl else ""
            )

            row_str = " | ".join([f"{k}:{v}" for k, v in sorted(row.items())])
            print(f"  Row {row_idx}: {{ {row_str} }}{prefix_marker}")

    # 3. ANALYSIS HINT
    shl = common_prefix_len(node.node_id, target_key)
    needed_digit = target_key[shl]
    has_route = shl in node.routing_table and needed_digit in node.routing_table[shl]
    leaf_is_better = dist_leaf < dist_me

    print(f"{C_YELLOW}Analysis:{C_RESET}")
    print(f"  Prefix match len: {shl} -> Need digit '{needed_digit}' in Row {shl}")
    print(
        f"  Routing Table has entry? {C_GREEN if has_route else C_RED}{has_route}{C_RESET}"
    )
    print(f"  Closest Leaf: {best_leaf} (Dist: {dist_leaf})")
    print(f"  Current Node Dist: {dist_me}")
    # print(
    #    f"  Is Leaf closer than Me? {C_GREEN if leaf_is_better else C_RED}{leaf_is_better}{C_RESET}"
    # )
    print("-" * 40)


def print_failure_report(mode, src, key, path, current_node):
    print(f"\n\n{C_RED}FAILURE DETECTED: {mode}!{C_RESET}")
    print("=" * 60)
    print(f"Task: Route from Node {src} -> Key {key}")

    path_str = " -> ".join(path)
    if len(path) > 5:
        path_str = f"... -> {path[-2]} -> {path[-1]}"
    print(f"Path Trace: {path_str}")
    print(f"Stuck at Node: {current_node}")

    if mode == "STUCK (None Returned)":
        print(f"\n{C_YELLOW}HINT: Look at the analysis above.")
        # print(
        #     f"The Routing Table missed (Red False), but the Leaf Set had a better candidate (Green True)."
        # )
        # print(f"Your code didn't check the Leaf Set!{C_RESET}")
    elif mode == "INFINITE LOOP":
        print(f"\n{C_YELLOW}HINT: A next hop must make monotonic progress toward the key.")
        print(
            "Treat the routing-table entry and leaf set as candidates, then only "
            f"return a candidate whose distance to the key is lower than this node's.{C_RESET}"
        )


def explain_next_hop(node, target_key, next_hop):
    if next_hop is None:
        return "dropped: no next hop returned"
    if next_hop == node.node_id:
        return "stop: no known neighbor is closer"

    shl = common_prefix_len(node.node_id, target_key)
    needed_digit = target_key[shl]
    table_candidate = node.routing_table.get(shl, {}).get(needed_digit)

    sources = []
    if table_candidate == next_hop:
        sources.append(f"routing table row {shl}, digit '{needed_digit}'")
    if next_hop in node.leaf_set:
        sources.append("leaf set")

    if sources:
        return "via " + " and ".join(sources)
    return "via closest-known fallback"


def print_success_trace(nodes, src, target_key, example_no, max_hops=20):
    print(f"\n{C_BLUE}Example successful lookup #{example_no}{C_RESET}")
    print("=" * 60)
    print(f"Task: Route from Node {src} -> Key {target_key}")

    current = src
    visited = {current}
    path = [current]

    for hop in range(max_hops):
        node = nodes[current]
        next_hop = node.get_next_hop(target_key)
        current_dist = diff(current, target_key)
        shl = common_prefix_len(current, target_key)
        needed_digit = target_key[shl] if shl < ID_DIGITS else "-"
        decision = explain_next_hop(node, target_key, next_hop)

        if next_hop is None:
            print(
                f"  Hop {hop:02d}: {current} dist={current_dist:<8} "
                f"prefix={shl} need row {shl} digit '{needed_digit}' -> DROP"
            )
            break

        next_dist = diff(next_hop, target_key)
        print(
            f"  Hop {hop:02d}: {current} dist={current_dist:<8} "
            f"prefix={shl} need row {shl} digit '{needed_digit}' "
            f"-> {next_hop} dist={next_dist:<8} ({decision})"
        )

        if next_hop == current:
            print(
                f"Delivered: {current} is the closest known owner for key "
                f"{target_key}."
            )
            break

        if next_hop in visited:
            print(f"Stopped: loop detected at {next_hop}.")
            break

        current = next_hop
        visited.add(current)
        path.append(current)

    print("Path: " + " -> ".join(path))


###############################################################################
# SIMULATION ENGINE
###############################################################################


def find_broken_route(nodes, sorted_ids, max_attempts=500):
    print(f"Stress testing network ({NUM_NODES} nodes in {16**ID_DIGITS} ID space)...")
    # print(
    #     "Searching for a SPECIFIC failure case (Table Miss + Leaf Hit)",
    #     end="",
    #     flush=True,
    # )

    attempts = 0
    max_hops = 20
    success_examples = []

    while attempts < max_attempts:
        attempts += 1
        if attempts % 20 == 0:
            print(".", end="", flush=True)

        src_id = random.choice(sorted_ids)
        target_key = f"{random.randrange(16**ID_DIGITS):06X}"

        current = src_id
        path = [current]
        hops = 0
        visited = {current}

        # --- PHASE 1: SILENT CHECK ---
        temp_curr = current
        temp_hops = 0
        temp_visited = {current}
        temp_path = [current]

        failure_found = False
        failure_mode = ""
        route_succeeded = False

        while temp_hops < max_hops:
            node_obj = nodes[temp_curr]
            next_hop = node_obj.get_next_hop(target_key)

            # CHECK FOR THE SPECIFIC EDUCATIONAL BUG
            if next_hop is None:
                # Is there actually a better leaf?
                best_leaf = min(node_obj.leaf_set, key=lambda x: diff(x, target_key))
                dist_me = diff(temp_curr, target_key)
                dist_leaf = diff(best_leaf, target_key)

                if dist_leaf < dist_me:
                    # YES! This is the scenario we want to show the student.
                    failure_found = True
                    failure_mode = "STUCK (None Returned)"
                    # Update current pointers to this failure point so replay works
                    current = temp_curr
                    break
                else:
                    # NO. This node is actually the closest.
                    # The buggy code returned None (which is technically wrong, it should be Self),
                    # but this isn't the "Leaf Set" lesson we want to teach.
                    # SKIP THIS ATTEMPT and try a new random route.
                    break

            if next_hop == temp_curr:
                route_succeeded = True
                break  # Succeeded (or stuck at self)

            if next_hop in temp_visited:
                failure_found = True
                failure_mode = "INFINITE LOOP"
                current = temp_curr
                break

            temp_curr = next_hop
            temp_visited.add(temp_curr)
            temp_path.append(temp_curr)
            temp_hops += 1

        if temp_hops >= max_hops:
            failure_found = True
            failure_mode = "HOP LIMIT EXCEEDED"

        if (
            route_succeeded
            and not failure_found
            and len(success_examples) < 2
            and len(temp_path) > 1
        ):
            success_examples.append((src_id, target_key))

        # --- PHASE 2: VERBOSE REPLAY (Only if Interesting Failure Found) ---
        if failure_found:
            print(
                f"\n\n{C_RED}Found instructional failure on attempt #{attempts}! Replaying trace...{C_RESET}"
            )

            # Reset replay pointers
            curr_replay = src_id
            replay_hops = 0
            replay_visited = {curr_replay}
            replay_path = [curr_replay]

            while replay_hops < max_hops:
                node_obj = nodes[curr_replay]

                # PRINT STATE
                print_node_state(node_obj, target_key)

                next_hop = node_obj.get_next_hop(target_key)
                print(f"   > Logic decided next hop: {next_hop}")

                # Check stop conditions
                if (
                    next_hop is None
                    or next_hop == curr_replay
                    or next_hop in replay_visited
                ):
                    break

                curr_replay = next_hop
                replay_visited.add(curr_replay)
                replay_path.append(curr_replay)
                replay_hops += 1

                # If we are about to hit the failure node, pause
                if curr_replay == current:
                    input("   (Press Enter to step to the failure node...)")
                else:
                    input("   (Press Enter for next hop...)")

            # Print Final State of the node where it failed
            if next_hop is None:
                print_node_state(nodes[curr_replay], target_key)

            print_failure_report(
                failure_mode, src_id, target_key, replay_path, curr_replay
            )
            return

    print(
        f"\n{C_GREEN}No delivery failures found in {attempts} sampled routes.{C_RESET}"
    )
    print("The router did not drop, loop, or exceed the hop limit during this stress test.")
    if success_examples:
        print("\nHere are example Pastry lookups from the successful run:")
        for i, (src_id, target_key) in enumerate(success_examples, start=1):
            print_success_trace(nodes, src_id, target_key, i, max_hops=max_hops)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, help="Set a random seed for replaying a run")
    ap.add_argument(
        "--attempts",
        type=int,
        default=500,
        help="Number of random routes to test before reporting success",
    )
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    ids = set()
    while len(ids) < NUM_NODES:
        ids.add(f"{random.randrange(16**ID_DIGITS):06X}")
    sorted_ids = sorted(list(ids))
    nodes = {nid: PastryNode(nid, sorted_ids) for nid in sorted_ids}

    find_broken_route(nodes, sorted_ids, max_attempts=args.attempts)


if __name__ == "__main__":
    main()
