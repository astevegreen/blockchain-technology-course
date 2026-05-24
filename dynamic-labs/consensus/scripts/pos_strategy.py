#!/usr/bin/env python3
import random, time, sys

###############################################################################
# CONFIGURATION & CONSTANTS
###############################################################################

C_RESET = "\033[0m"
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_BOLD = "\033[1m"
C_PURPLE = "\033[35m"
C_CYAN = "\033[36m"


def print_header(title):
    print(f"\n{C_BLUE}{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}{C_RESET}")


def prompt_float(prompt, default, minimum=None, maximum=None):
    raw = input(f"{prompt} [default: {default}] > ").strip()
    if raw == "":
        return float(default)
    try:
        value = float(raw)
    except ValueError:
        print(f"Invalid input. Using default {default}.")
        return float(default)

    if minimum is not None and value < minimum:
        print(f"Value must be >= {minimum}. Using default {default}.")
        return float(default)
    if maximum is not None and value > maximum:
        print(f"Value must be <= {maximum}. Using default {default}.")
        return float(default)
    return value


def prompt_int(prompt, default, minimum=None, maximum=None):
    raw = input(f"{prompt} [default: {default}] > ").strip()
    if raw == "":
        return int(default)
    try:
        value = int(raw)
    except ValueError:
        print(f"Invalid input. Using default {default}.")
        return int(default)

    if minimum is not None and value < minimum:
        print(f"Value must be >= {minimum}. Using default {default}.")
        return int(default)
    if maximum is not None and value > maximum:
        print(f"Value must be <= {maximum}. Using default {default}.")
        return int(default)
    return value


def apply_stake_delta(validator, delta):
    validator.stake = max(0.0, validator.stake + delta)
    if validator.stake <= 0:
        validator.is_bankrupt = True


def pick_weighted_validator(validators):
    eligible = [v for v in validators if v.stake > 0]
    if not eligible:
        return None
    return random.choices(eligible, weights=[v.stake for v in eligible], k=1)[0]


def print_stakes(validators):
    print("-" * 30)
    for v in validators:
        print(f"{v.name}: {v.stake:.1f}")


def snapshot_stakes(validators):
    return {v.name: float(v.stake) for v in validators}


def print_performance_summary(validators, initial_stakes, focus_name="You"):
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(
        f"{'Name':<16} | {'Start':>10} | {'End':>10} | {'Delta':>10} | {'Return %':>9}"
    )
    print("-" * 60)

    rows = []
    for v in validators:
        start = float(initial_stakes.get(v.name, v.initial_stake))
        end = float(v.stake)
        delta = end - start
        ret_pct = (delta / start * 100) if start > 0 else 0.0
        rows.append((v.name, start, end, delta, ret_pct))
        print(
            f"{v.name:<16} | {start:>10.1f} | {end:>10.1f} | {delta:>10.1f} | {ret_pct:>8.2f}%"
        )

    print("-" * 60)
    ranking = sorted(rows, key=lambda r: r[4], reverse=True)
    print(
        "Return Ranking: "
        + " > ".join([f"{name} ({ret:.2f}%)" for name, _, _, _, ret in ranking])
    )

    focus = next((r for r in rows if r[0] == focus_name), None)
    if focus:
        focus_ret = focus[4]
        for name, _, _, _, ret in rows:
            if name == focus_name:
                continue
            diff = focus_ret - ret
            if diff > 0:
                label = "outperformed"
            elif diff < 0:
                label = "underperformed"
            else:
                label = "matched"
            print(f"{focus_name} {label} {name} by {abs(diff):.2f} percentage points.")


###############################################################################
# VALIDATOR CLASS
###############################################################################


class Validator:
    def __init__(self, name, stake, strategy="honest"):
        self.name = name
        self.stake = float(stake)
        self.initial_stake = float(stake)
        self.strategy = strategy
        self.is_bankrupt = False

    def __repr__(self):
        return f"{self.name}: {self.stake:.2f}"


###############################################################################
# SCENARIO 1: RICH GET RICHER
###############################################################################


def run_rich_get_richer():
    print_header("SCENARIO 1: Economies of Scale (Dilution)")
    print("We will simulate 100,000 epochs.")
    print("Operating Cost is 1. Reward is 100.")
    print("Small players start profitable, but watch the 'Trend' as inflation hits.\n")

    validators = [
        Validator("Alice (Whale)", 40000),
        Validator("Bob (Large)", 35000),
        Validator("Charlie", 5000),
        Validator("Dave", 5000),
        Validator("Eve", 5000),
        Validator("Frank", 5000),
        Validator("Grace", 5000),
    ]

    initial_total = sum(v.stake for v in validators)
    for v in validators:
        v.initial_share_pct = (v.stake / initial_total) * 100

    BLOCK_REWARD = 100
    OPERATING_COST = 1

    print(f"{'Name':<15} | {'Initial Stake':<15} | {'Start Share %':<15}")
    print("-" * 50)
    for v in validators:
        print(f"{v.name:<15} | {v.stake:<15.0f} | {v.initial_share_pct:<13.1f}%")

    input("\nPress Enter to start simulation...")

    for epoch in range(1, 100001):
        current_active = [v for v in validators if not v.is_bankrupt]

        for v in validators:
            if not v.is_bankrupt:
                v.stake -= OPERATING_COST
                if v.stake <= 0:
                    v.stake = 0
                    v.is_bankrupt = True

        if not current_active:
            print("Everyone went bankrupt!")
            break

        weights = [v.stake for v in current_active]
        if not weights:
            break
        winner = random.choices(current_active, weights=weights, k=1)[0]

        winner.stake += BLOCK_REWARD

        if epoch % 5000 == 0:
            print(f"\n{C_BOLD}--- Epoch {epoch} ---{C_RESET}")
            real_total = sum(v.stake for v in validators)

            print(
                f"{'Name':<15} | {'Stake':<10} | {'Start %':<8} | {'Curr %':<8} | {'Trend'}"
            )
            print("-" * 70)

            for v in validators:
                pct_share = (v.stake / real_total * 100) if real_total > 0 else 0
                diff = pct_share - v.initial_share_pct

                status = ""
                if v.is_bankrupt:
                    status = f"{C_RED}BANKRUPT{C_RESET}"
                elif diff > 0.5:
                    status = f"{C_GREEN}+ {abs(diff):.2f}%{C_RESET}"
                elif diff < -0.5:
                    status = f"{C_RED}- {abs(diff):.2f}%{C_RESET}"
                else:
                    status = f"{C_YELLOW}= 0.00%{C_RESET}"

                print(
                    f"{v.name:<15} | {v.stake:<10.0f} | {v.initial_share_pct:<8.1f} | {pct_share:<8.1f} | {status}"
                )

            time.sleep(0.5)

    print("\nSimulation Complete.")


###############################################################################
# SCENARIO 2: CONSENSUS WAR
###############################################################################


def run_consensus_game():
    print_header("SCENARIO 2: The Consensus War (Collusion & Censorship)")
    print("You are a Validator. You will have two roles:")
    print(
        f"1. {C_CYAN}PROPOSER:{C_RESET} You build the block. You decide which txs to include."
    )
    print(f"2. {C_CYAN}ATTESTER:{C_RESET} You vote on blocks proposed by others.")
    reward_amt = prompt_float("Enter block reward amount", 10.0, minimum=0.1)
    rounds = prompt_int("Enter number of rounds", 10, minimum=1, maximum=200)
    bribe_amt = prompt_float("Enter coalition bribe amount", 15.0, minimum=0.0)
    detection_prob = prompt_float(
        "Enter detection probability for harmful behavior (0-1)",
        0.30,
        minimum=0.0,
        maximum=1.0,
    )
    slash_cost = prompt_float(
        "Enter slashing cost when detected", reward_amt * 2, minimum=0.0
    )
    fork_chance = prompt_float(
        "Enter chance of fork conflict while attesting (0-1)",
        0.40,
        minimum=0.0,
        maximum=1.0,
    )
    starting_stake = prompt_float(
        "Enter equal starting stake for each validator", 3000.0, minimum=100.0
    )

    validators = [
        Validator("You", starting_stake, strategy="human"),
        Validator("Bot_Honest", starting_stake, strategy="honest"),
        Validator("Bot_Greedy", starting_stake, strategy="greedy"),
    ]
    initial_stakes = snapshot_stakes(validators)

    print(
        f"\n{C_GREEN}Network Live!{C_RESET} Total Stake: {sum(v.stake for v in validators):.1f}"
    )
    print(
        f"Config -> rounds={rounds}, reward={reward_amt}, bribe={bribe_amt}, "
        f"detection={detection_prob:.0%}, slash={slash_cost}, fork chance={fork_chance:.0%}, "
        f"starting stake={starting_stake:.1f}"
    )
    print("\n--- Starting Consensus Rounds ---")

    for r in range(1, rounds + 1):
        print(f"\n{C_BOLD}ROUND {r}{C_RESET}")
        time.sleep(0.6)

        proposer = pick_weighted_validator(validators)
        if proposer is None:
            print(
                f"{C_RED}No validators with stake remaining. Ending scenario.{C_RESET}"
            )
            break

        if proposer.name == "You":
            print(f"{C_CYAN}*** YOU ARE THE PROPOSER ***{C_RESET}")
            print("You inspect the mempool and decide what to include.")
            txs = [
                {"id": "Tx_01", "fee": 1.0, "desc": "Payment"},
                {"id": "Tx_02", "fee": 0.6, "desc": "Contract call"},
                {"id": "Tx_03", "fee": 3.2, "desc": "Flagged transfer"},
                {"id": "Tx_04", "fee": 0.4, "desc": "Settlement batch"},
            ]
            total_fees = sum(t["fee"] for t in txs)
            fees_without_flagged = total_fees - txs[2]["fee"]

            print("\nMempool:")
            for t in txs:
                marker = f"{C_RED}[FLAGGED]{C_RESET}" if t["id"] == "Tx_03" else ""
                print(f"  {t['id']} | fee={t['fee']:.1f} | {t['desc']} {marker}")

            print(
                f"\n{C_PURPLE}Coercion Offer:{C_RESET} exclude Tx_03 for bribe {bribe_amt:.1f}"
            )
            print(
                f"1. Include all -> payout {reward_amt + total_fees:.1f} "
                f"(reward + fees)"
            )
            print(
                f"2. Exclude flagged tx -> payout {reward_amt + fees_without_flagged + bribe_amt:.1f} "
                f"(reward + reduced fees + bribe)"
            )
            choice = input("Your choice (1/2): ").strip()

            if choice == "2":
                print("You accepted the offer and excluded Tx_03.")
                if random.random() < detection_prob:
                    apply_stake_delta(validators[0], -slash_cost)
                    print(
                        f"{C_RED}Detected.{C_RESET} Slashed by {slash_cost:.1f} "
                        f"(detection chance {detection_prob:.0%})."
                    )
                else:
                    gain = reward_amt + fees_without_flagged + bribe_amt
                    apply_stake_delta(validators[0], gain)
                    print(f"{C_GREEN}Not detected.{C_RESET} You gained {gain:.1f}.")
            else:
                gain = reward_amt + total_fees
                apply_stake_delta(validators[0], gain)
                print(f"You included all transactions and gained {gain:.1f}.")

        else:
            print(f"{C_BLUE}*** YOU ARE AN ATTESTER ***{C_RESET}")
            print(f"Scheduled proposer: {proposer.name}")

            if random.random() >= fork_chance:
                attestation_reward = reward_amt * 0.25
                apply_stake_delta(proposer, reward_amt)
                apply_stake_delta(validators[0], attestation_reward)
                print(
                    f"Single canonical block. {proposer.name} gained {reward_amt:.1f}, "
                    f"you gained {attestation_reward:.1f} for attesting."
                )
            else:
                print(
                    f"{C_RED}Fork detected.{C_RESET} Honest branch vs coalition branch."
                )
                print(
                    f"Coalition offers {bribe_amt:.1f} if you vote coalition and coalition wins."
                )
                print("1. Vote Honest")
                print("2. Vote Coalition")
                choice = input("Your choice (1/2): ").strip()
                choice = "2" if choice == "2" else "1"

                votes_honest = validators[1].stake
                votes_coalition = validators[2].stake
                if choice == "2":
                    votes_coalition += validators[0].stake
                    print("You voted coalition.")
                else:
                    votes_honest += validators[0].stake
                    print("You voted honest.")

                if votes_coalition > votes_honest:
                    print(f"{C_RED}Coalition branch wins.{C_RESET}")
                    apply_stake_delta(validators[2], reward_amt)
                    if choice == "2":
                        apply_stake_delta(validators[0], reward_amt * 0.25 + bribe_amt)
                        if random.random() < detection_prob:
                            apply_stake_delta(validators[0], -slash_cost)
                            print(
                                f"{C_RED}Coalition vote detected as misconduct.{C_RESET} "
                                f"Slashed by {slash_cost:.1f}."
                            )
                else:
                    print(f"{C_GREEN}Honest branch wins.{C_RESET}")
                    apply_stake_delta(validators[1], reward_amt)
                    if choice == "1":
                        apply_stake_delta(validators[0], reward_amt * 0.25)

        print_stakes(validators)
        time.sleep(0.8)

    print_performance_summary(validators, initial_stakes, focus_name="You")
    print("\nGame Over.")


###############################################################################
# SCENARIO 3: 51% CENSORSHIP ATTACK (Withholding Strategy)
###############################################################################


def run_censorship_attack():
    print_header("SCENARIO 3: The Oligarch (Selfish Mining / Censorship)")
    print("Simulation of a 51% Attack using BLOCK WITHHOLDING.")
    print("The Oligarch (70%) 'plays by the rules' of selection.")
    print("But when selected, he withholds the block to ambush the next proposer.\n")

    validators = [
        Validator("The Oligarch", 7000),  # 70% Stake
        Validator("Peasant 1", 1000),
        Validator("Peasant 2", 1000),
        Validator("Peasant 3", 1000),
    ]

    input("Press Enter to start attack simulation...")

    total_rounds = 20
    # State tracking
    hidden_block = False
    oligarch_wins = 0
    tx_confirmed = False

    for r in range(1, total_rounds + 1):
        print(
            f"\n{C_BOLD}ROUND {r:02d}{C_RESET} | State: {'Oligarch has Hidden Block' if hidden_block else 'No Hidden Block'}"
        )

        # 1. Select Scheduled Proposer (Random based on Stake)
        weights = [v.stake for v in validators]
        proposer = random.choices(validators, weights=weights, k=1)[0]

        # --- CASE A: Oligarch Selected ---
        if proposer.name == "The Oligarch":
            print(f"Proposer: {C_RED}The Oligarch{C_RESET}")

            if hidden_block:
                print(
                    f"Action:   Oligarch releases *previous* hidden block (extending chain)."
                )
                print(
                    f"          Oligarch creates NEW block (excluding Tx) and {C_RED}HIDES IT{C_RESET}."
                )
                print("Result:   Chain advances, but Oligarch maintains secret lead.")
                oligarch_wins += 1
            else:
                print(
                    f"Action:   Oligarch creates block (excluding Tx) and {C_RED}HIDES IT{C_RESET}."
                )
                print(
                    "Result:   Public chain sees a 'Missed Slot'. Oligarch has secret lead."
                )
                hidden_block = True

        # --- CASE B: Peasant Selected ---
        else:
            print(f"Proposer: {C_GREEN}{proposer.name}{C_RESET}")

            if hidden_block:
                # THE AMBUSH
                print(
                    f"Action:   Peasant proposes block including {C_GREEN}Target Tx{C_RESET}."
                )
                time.sleep(0.5)
                print(f"{C_RED}*** AMBUSH ***{C_RESET}")
                print(f"Oligarch immediately releases their HIDDEN block.")
                print(f"Fork Created: Peasant (with Tx) vs Oligarch (No Tx).")
                print(f"Vote: Oligarch (70%) vs Peasant (30%).")
                time.sleep(0.5)
                print(
                    f"Result:   {C_RED}OLIGARCH WINS.{C_RESET} Peasant block Orphaned."
                )
                print("          Target Tx returned to mempool (Censored).")

                # Oligarch uses up the hidden advantage to win this battle
                hidden_block = False
                oligarch_wins += 1
            else:
                # Oligarch has no ammo
                print(
                    f"Action:   Peasant proposes block including {C_GREEN}Target Tx{C_RESET}."
                )
                print("Result:   Oligarch has no hidden block to contest.")
                print(f"          {C_GREEN}Transaction Confirmed!{C_RESET}")
                tx_confirmed = True

        time.sleep(1.5)

    print("-" * 30)
    print(f"Total Rounds: {total_rounds}")
    print(f"Oligarch Chain Wins: {oligarch_wins}")

    if tx_confirmed:
        print(f"\nStatus: {C_GREEN}TX CONFIRMED{C_RESET}")
        print("Analysis: The Oligarch (70%) usually suppresses the Tx,")
        print(
            "but if Peasants get a lucky streak (selected when Oligarch has no ammo),"
        )
        print("the Tx can slip through.")
    else:
        print(f"\nStatus: {C_RED}TX CENSORED{C_RESET}")
        print("Analysis: The Oligarch successfully maintained the block withholding")
        print("strategy to orphan every honest attempt.")


###############################################################################
# SCENARIO 4: NOTHING-AT-STAKE VS SLASHING
###############################################################################


def run_nothing_at_stake_vs_slashing():
    print_header("SCENARIO 4: Nothing-at-Stake vs Slashing")
    print("You will see two phases:")
    print("Phase A: no slashing for equivocation.")
    print("Phase B: slashing enforced for equivocation.")

    rounds = prompt_int("Enter total rounds", 12, minimum=4, maximum=200)
    reward_per_attest = prompt_float(
        "Enter reward for voting on winning branch", 4.0, minimum=0.1
    )
    slash_detect_prob = prompt_float(
        "Enter equivocation detection probability in Phase B (0-1)",
        0.70,
        minimum=0.0,
        maximum=1.0,
    )
    slash_fraction = prompt_float(
        "Enter slash fraction of current stake when caught (0-1)",
        0.15,
        minimum=0.0,
        maximum=1.0,
    )
    starting_stake = prompt_float(
        "Enter equal starting stake for each validator", 3000.0, minimum=100.0
    )

    validators = [
        Validator("You", starting_stake, strategy="human"),
        Validator("Bot_Honest", starting_stake, strategy="honest"),
        Validator("Bot_Opportunist", starting_stake, strategy="opportunist"),
    ]
    initial_stakes = snapshot_stakes(validators)

    phase_a_rounds = rounds // 2
    print(
        f"\nConfig -> rounds={rounds}, reward={reward_per_attest}, "
        f"phase B detection={slash_detect_prob:.0%}, slash fraction={slash_fraction:.0%}, "
        f"starting stake={starting_stake:.1f}"
    )

    for r in range(1, rounds + 1):
        slashing_active = r > phase_a_rounds
        phase_name = "B (Slashing ON)" if slashing_active else "A (Slashing OFF)"
        print(f"\n{C_BOLD}ROUND {r} - Phase {phase_name}{C_RESET}")
        print("Competing branches: A and B at same height.")
        user_cmd = input("Vote [a/b/both/skip] > ").strip().lower()

        user_votes = set()
        if user_cmd == "a":
            user_votes.add("A")
        elif user_cmd == "b":
            user_votes.add("B")
        elif user_cmd == "both":
            user_votes = {"A", "B"}
        else:
            print("You skipped.")

        honest_votes = {random.choice(["A", "B"])}
        if slashing_active:
            opportunist_votes = (
                {"A", "B"} if random.random() < 0.1 else {random.choice(["A", "B"])}
            )
        else:
            opportunist_votes = {"A", "B"}

        vote_map = {
            "You": user_votes,
            "Bot_Honest": honest_votes,
            "Bot_Opportunist": opportunist_votes,
        }

        branch_weight = {"A": 0.0, "B": 0.0}
        for v in validators:
            for branch in vote_map[v.name]:
                branch_weight[branch] += v.stake

        if branch_weight["A"] > branch_weight["B"]:
            winner = "A"
        elif branch_weight["B"] > branch_weight["A"]:
            winner = "B"
        else:
            winner = random.choice(["A", "B"])

        print(
            f"Votes -> A:{branch_weight['A']:.1f} B:{branch_weight['B']:.1f} | Winner: {winner}"
        )

        for v in validators:
            votes = vote_map[v.name]
            if winner in votes:
                apply_stake_delta(v, reward_per_attest)

            if (
                slashing_active
                and len(votes) > 1
                and random.random() < slash_detect_prob
            ):
                penalty = v.stake * slash_fraction
                apply_stake_delta(v, -penalty)
                if v.name == "You":
                    print(
                        f"{C_RED}You were slashed for equivocation:{C_RESET} -{penalty:.1f}"
                    )

        print_stakes(validators)
        time.sleep(0.6)

    print_performance_summary(validators, initial_stakes, focus_name="You")
    print("\nScenario complete.")


###############################################################################
# SCENARIO 5: INACTIVITY LEAK
###############################################################################


def run_inactivity_leak():
    print_header("SCENARIO 5: Inactivity Leak & Liveness")
    print("Finality requires enough online stake.")
    print("When finality fails, offline validators leak stake each epoch.")

    epochs = prompt_int("Enter epochs", 18, minimum=5, maximum=300)
    proposer_reward = prompt_float("Enter proposer reward", 12.0, minimum=0.1)
    attest_reward = prompt_float("Enter attester reward", 2.0, minimum=0.0)
    leak_rate = prompt_float(
        "Enter inactivity leak per offline epoch (0-1)",
        0.02,
        minimum=0.0,
        maximum=1.0,
    )
    finality_threshold = prompt_float(
        "Enter finality threshold as stake fraction (0-1)",
        0.67,
        minimum=0.5,
        maximum=1.0,
    )

    outage_start = prompt_int(
        "Enter outage start epoch for two bots",
        max(2, epochs // 3),
        minimum=1,
        maximum=epochs,
    )
    outage_end = prompt_int(
        "Enter outage end epoch for two bots",
        min(epochs, outage_start + max(2, epochs // 3)),
        minimum=outage_start,
        maximum=epochs,
    )

    validators = [
        Validator("You", 2500),
        Validator("Bot_A", 3000),
        Validator("Bot_B", 2500),
        Validator("Bot_C", 2000),
    ]
    initial_stakes = snapshot_stakes(validators)

    print(
        f"\nConfig -> epochs={epochs}, leak={leak_rate:.2%}, "
        f"finality threshold={finality_threshold:.0%}"
    )

    for epoch in range(1, epochs + 1):
        print(f"\n{C_BOLD}EPOCH {epoch}{C_RESET}")
        in_outage_window = outage_start <= epoch <= outage_end
        if in_outage_window:
            print(f"{C_YELLOW}Outage window active for Bot_B and Bot_C.{C_RESET}")

        user_state = (
            input("Stay online this epoch? [y/n, default y] > ").strip().lower()
        )
        online = {"You": user_state != "n"}

        for v in validators[1:]:
            uptime = 0.95
            if in_outage_window and v.name in {"Bot_B", "Bot_C"}:
                uptime = 0.15
            online[v.name] = random.random() < uptime

        total_stake = sum(v.stake for v in validators)
        active_stake = sum(v.stake for v in validators if online[v.name])
        finalized = active_stake >= total_stake * finality_threshold

        print(
            f"Active stake: {active_stake:.1f}/{total_stake:.1f} "
            f"({(active_stake / total_stake * 100) if total_stake else 0:.1f}%)"
        )

        if finalized:
            online_validators = [
                v for v in validators if online[v.name] and v.stake > 0
            ]
            proposer = pick_weighted_validator(online_validators)
            if proposer:
                apply_stake_delta(proposer, proposer_reward)
            for v in online_validators:
                apply_stake_delta(v, attest_reward)
            proposer_name = proposer.name if proposer else "None"
            print(
                f"{C_GREEN}Finality achieved.{C_RESET} Proposer: {proposer_name}. "
                f"Online validators received rewards."
            )
        else:
            print(f"{C_RED}No finality this epoch.{C_RESET} Applying inactivity leak.")
            for v in validators:
                if not online[v.name]:
                    penalty = v.stake * leak_rate
                    apply_stake_delta(v, -penalty)

        print("Online status:")
        for v in validators:
            state = (
                f"{C_GREEN}online{C_RESET}"
                if online[v.name]
                else f"{C_RED}offline{C_RESET}"
            )
            print(f"  {v.name:<10} {state} | stake={v.stake:.1f}")
        time.sleep(0.5)

    print_performance_summary(validators, initial_stakes, focus_name="You")
    print("\nScenario complete.")


###############################################################################
# MAIN MENU
###############################################################################


def main():
    while True:
        print_header("PROOF OF STAKE LAB")
        print("1. 'Rich Get Richer' (Stake Compounding Sim)")
        print("2. 'Consensus War' (Corruption & Forks)")
        print("3. 'The Oligarch' (Block Withholding Attack)")
        print("4. 'Nothing-at-Stake vs Slashing'")
        print("5. 'Inactivity Leak & Liveness'")
        print("6. Exit")

        choice = input("\nSelect Simulation (1-6): ").strip()

        if choice == "1":
            run_rich_get_richer()
        elif choice == "2":
            run_consensus_game()
        elif choice == "3":
            run_censorship_attack()
        elif choice == "4":
            run_nothing_at_stake_vs_slashing()
        elif choice == "5":
            run_inactivity_leak()
        elif choice == "6":
            print("Exiting.")
            sys.exit(0)
        else:
            print("Invalid selection.")

        input("\nPress Enter to return to menu...")


if __name__ == "__main__":
    main()
