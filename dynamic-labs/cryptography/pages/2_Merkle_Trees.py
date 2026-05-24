import streamlit as st
from lab_core import LabCore
from lesson_loader import load_lesson
from progress_beacon import fire as _fire_progress

_SCENARIO_BEACONS = {
    "1. Build a Tree": "exercise:crypto-merkle-s1",
    "2. Verify a Proof": "exercise:crypto-merkle-s2",
}

# --- SETUP & STATE ---
if "lab_core" not in st.session_state:
    st.session_state.lab_core = LabCore()

if "history2" not in st.session_state:
    st.session_state.history2 = []

if "active_proof" not in st.session_state:
    st.session_state.active_proof = None

if "hints_shown" not in st.session_state:
    st.session_state.hints_shown = {}

# --- CSS STYLING ---
st.markdown(
    """
<style>
.stTextInput > div > div > input { font-family: 'Courier New', monospace; color: #333; }
.log-text { font-family: 'Courier New', monospace; font-size: 14px; white-space: pre-wrap; margin-bottom: 5px; }
.log-cmd { color: #2e86c1; font-weight: bold; }
.log-out { color: #333; white-space: pre-wrap; }

/* Remove the ugly box around the form to keep it looking like a clean terminal */
div[data-testid="stForm"] { border: none; padding: 0; } 

.status-incomplete { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; font-weight: bold; }
.status-complete { background-color: #d1e7dd; border-left: 4px solid #0f5132; padding: 10px; margin: 10px 0; font-weight: bold; color: #0f5132; }

.hint-box { background-color: #cfe2ff; border: 1px solid #084298; padding: 15px; margin: 10px 0; border-radius: 5px; }
.hint-title { color: #084298; font-weight: bold; margin-bottom: 10px; }

/* Merkle Tree specific styling */
.merkle-box {
    display: inline-block; width: 90px; text-align: center; padding: 5px 0; margin: 2px;
    border-radius: 4px; font-family: monospace; font-size: 10px;
    box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
}
.box-empty { background-color: #f0f2f6; border: 1px dashed #ccc; color: #aaa; }
.box-filled { background-color: #d1e7dd; border: 1px solid #0f5132; color: #0f5132; font-weight: bold; }
.centered-col { display: flex; justify-content: center; width: 100%; }

.tree-container {
    display: flex; flex-direction: column; align-items: center; width: 100%;
    font-family: monospace; font-size: 8px; margin-top: 20px;
}
.tree-row { display: flex; justify-content: center; width: 100%; margin-bottom: 10px; }
.node-base {
    height: 30px; margin: 0 2px; border-radius: 3px;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.3s ease;
}
.node-ghost { background-color: #f8f9fa; border: 1px solid #e9ecef; color: #dee2e6; flex: 1; }
.node-user  { background-color: #cff4fc; border: 2px solid #0dcaf0; color: #055160; font-weight: bold; flex: 1; box-shadow: 0 0 5px #0dcaf0;}
.node-sib   { background-color: #fff3cd; border: 2px solid #ffc107; color: #664d03; font-weight: bold; flex: 1; }
.node-root  { background-color: #20c997; border: 2px solid #198754; color: white; font-weight: bold; width: 100px; }
</style>
""",
    unsafe_allow_html=True,
)


# --- HELPER: RENDER GRID TREE ---
def render_large_tree(active_proof_id):
    path_map = {}
    if active_proof_id == "A":
        path_map = {
            4: {"user": 2, "sib": 3},
            3: {"user": 1, "sib": 0},
            2: {"user": 0, "sib": 1},
            1: {"user": 0, "sib": 1},
            0: {"user": 0},
        }
    elif active_proof_id == "B":
        path_map = {
            4: {"user": 13, "sib": 12},
            3: {"user": 6, "sib": 7},
            2: {"user": 3, "sib": 2},
            1: {"user": 1, "sib": 0},
            0: {"user": 0},
        }

    html = "<div class='tree-container'>"
    structure = [(0, 1), (1, 2), (2, 4), (3, 8), (4, 16)]
    for level, count in structure:
        html += "<div class='tree-row'>"
        for i in range(count):
            css_class = "node-ghost"
            content = "&nbsp;"
            if active_proof_id:
                info = path_map.get(level)
                if info:
                    if i == info.get("user"):
                        css_class = "node-user" if level > 0 else "node-root"
                        content = (
                            "ROOT" if level == 0 else ("Tx" if level == 4 else "Hash")
                        )
                    elif i == info.get("sib"):
                        css_class = "node-sib"
                        content = "Sib"
            if level == 0 and not active_proof_id:
                content = "ROOT"
                css_class = "node-ghost"
            html += f"<div class='node-base {css_class}'>{content}</div>"
        html += "</div>"
    html += "</div>"
    return html


def render_box(val, label):
    if val:
        return f"<div class='merkle-box box-filled'>[OK] {val[:6]}...</div>"
    return f"<div class='merkle-box box-empty'>{label}</div>"


# --- COMMAND PROCESSOR ---
def process_command(user_input):
    parts = user_input.strip().split()
    cmd = parts[0].lower()
    args = parts[1:]
    lab = st.session_state.lab_core
    output = ""

    if cmd == "list_tx":
        output = "Transactions:\n" + "\n".join(
            [f"{i}: {tx}" for i, tx in enumerate(lab.merkle_txs)]
        )
    elif cmd == "sha256":
        text = " ".join(args)
        output = f"SHA-256: {lab.sha256_hash(text)}"
    elif cmd == "hash_pair":
        if len(args) == 2:
            output = f"Pair Hash: {lab.sha256_hash(args[0] + args[1])}"
        else:
            output = "Usage: hash_pair <hash_L> <hash_R>"
    elif cmd == "fill_leaf":
        if len(args) == 2:
            try:
                output = lab.fill_leaf(int(args[0]), args[1])[1]
            except:
                output = "[ERROR]: Index error."
        else:
            output = "Usage: fill_leaf <idx> <hash>"
    elif cmd == "combine":
        if len(args) == 2:
            output = lab.smart_combine(args[0], args[1])[1]
        else:
            output = "Usage: combine <L_hash> <R_hash>"
    elif cmd == "get_proof":
        pid = args[0].upper() if args else ""
        if pid not in ["A", "B"]:
            output = "[ERROR]: Unknown Proof ID. Available: A, B"
        else:
            st.session_state.active_proof = pid
            is_valid = pid == "A"
            tx_data = lab.proof_a_tx if is_valid else lab.proof_b_tx
            siblings = lab.proof_a_siblings if is_valid else lab.proof_b_siblings

            output = f"--- PROOF {pid} ---\n"
            output += f"Tx Data: {tx_data}\n"
            output += f"Target Root: {lab.lg_official_root}\n"
            output += "Path to Root (Verify these steps!):\n"

            curr = lab.sha256_hash(tx_data)
            for i, step in enumerate(siblings):
                output += f"\n[STEP {i+1}]\n"
                output += f"  Current Hash: {curr}\n"
                output += f"  + Sibling ({step['pos']}): {step['hash']}\n"

                if is_valid:
                    claimed = (
                        lab.sha256_hash(curr + step["hash"])
                        if step["pos"] == "right"
                        else lab.sha256_hash(step["hash"] + curr)
                    )
                else:
                    actual = (
                        lab.sha256_hash(curr + step["hash"])
                        if step["pos"] == "right"
                        else lab.sha256_hash(step["hash"] + curr)
                    )
                    claimed = actual
                    if i == 3:
                        claimed = lab.lg_official_root  # The Lie

                output += f"  --------------------------------------------------\n"
                output += f"  Network Claims Parent is: {claimed}\n"
                curr = claimed

            output += "\nTASK: Manually hash (Current + Sibling) at each step.\n"
            output += "Run: hash_pair <Hash_L> <Hash_R> (Watch the order!)"
    elif cmd == "help":
        output = "Available commands vary by scenario. Check the scenario description on the right."
    else:
        output = f"Unknown command: {cmd}\nType 'help' for assistance."

    st.session_state.history2.insert(0, (user_input, output))


# --- HINT SYSTEM ---
def show_hint(scenario, level):
    hints = {
        "m1": {
            1: "First, generate the hash for each transaction string using `sha256 <text>`, then use `fill_leaf <idx> <hash>` to place it.",
            2: "There are only 7 transactions, but the tree needs 8 leaves to balance. You must duplicate the final transaction hash into leaf 7.",
            3: "When combining hashes, order matters! Always put the left child first. Use `combine <hash_L> <hash_R>`.",
        },
        "m2": {
            1: "Run `get_proof B`. First, hash the fake transaction string they provided you using `sha256`.",
            2: "Take your new hash and combine it with the first sibling provided using `hash_pair`. Pay close attention to whether the sibling is on the Left or Right!",
            3: "Keep combining up the tree. The final hash you generate will NOT match the Target Root, proving the transaction is a forgery.",
        },
    }
    hint_text = hints.get(scenario, {}).get(level, "No more hints available.")
    st.session_state.hints_shown[f"{scenario}_lvl{level}"] = True
    return hint_text


# --- UI LAYOUT ---
st.sidebar.title("Module 2: Merkle Trees")
st.sidebar.markdown(
    "**Learning Goal:** Understand how blockchains compress data and verify transactions log-efficiently."
)

scenario = st.sidebar.radio(
    "Select Scenario",
    [
        "1. Build a Tree",
        "2. Verify a Proof",
    ],
)
_fire_progress(_SCENARIO_BEACONS.get(scenario, ""))

col_term, col_vis = st.columns([1, 1])

# --- TERMINAL FORM FIX ---
with col_term:
    st.subheader("Terminal")

    with st.form("terminal_form", clear_on_submit=True):
        user_cmd = st.text_input("Enter Command (Press Enter to submit)")
        submitted = st.form_submit_button("Run")

        if submitted and user_cmd:
            process_command(user_cmd)

    log_box = st.container(height=600)
    for c, o in st.session_state.history2:
        log_box.markdown(
            f"<div class='log-cmd'>>> {c}</div><div class='log-out'>{o}</div><hr style='margin:5px 0'>",
            unsafe_allow_html=True,
        )

with col_vis:
    lab = st.session_state.lab_core

    if scenario == "1. Build a Tree":
        st.markdown("### Scenario 1: Build a Tree")
        st.markdown(load_lesson("crypto-merkle-s1"))

        # Render Small Tree
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 1, 2])
        with c2:
            st.markdown(
                f"<div class='centered-col'>{render_box(lab.student_root, 'ROOT')}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("<hr style='margin:5px 0;opacity:0.3'>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])
        with c2:
            st.markdown(
                f"<div class='centered-col'>{render_box(lab.student_level2[0], 'L2-0')}</div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"<div class='centered-col'>{render_box(lab.student_level2[1], 'L2-1')}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("<hr style='margin:5px 0;opacity:0.3'>", unsafe_allow_html=True)

        cols = st.columns([0.5, 1, 1, 1, 1, 0.5])
        for i in range(4):
            with cols[i + 1]:
                st.markdown(
                    f"<div class='centered-col'>{render_box(lab.student_level1[i], f'L1-{i}')}</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("<hr style='margin:5px 0;opacity:0.3'>", unsafe_allow_html=True)

        cols = st.columns(8)
        for i in range(8):
            with cols[i]:
                st.markdown(
                    f"<div class='centered-col'>{render_box(lab.student_leaves[i], f'Leaf-{i}')}</div>",
                    unsafe_allow_html=True,
                )

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="m1_1"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 1:</div>{show_hint('m1', 1)}</div>",
                    unsafe_allow_html=True,
                )
        with col2:
            if st.button("Hint 2", key="m1_2"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 2:</div>{show_hint('m1', 2)}</div>",
                    unsafe_allow_html=True,
                )
        with col3:
            if st.button("Hint 3", key="m1_3"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 3:</div>{show_hint('m1', 3)}</div>",
                    unsafe_allow_html=True,
                )

    elif scenario == "2. Verify a Proof":
        st.markdown("### Scenario 2: Verify a Proof")
        st.markdown(load_lesson("crypto-merkle-s2"))

        st.markdown(
            render_large_tree(st.session_state.active_proof), unsafe_allow_html=True
        )
        st.caption("Key: 🟦 Your Path | 🟨 Sibling Needed | ⬜ Background Data")

        if st.session_state.active_proof is None:
            st.markdown(
                "<div class='status-incomplete'>[WAITING] Run `get_proof A` or `get_proof B` to load path data.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='status-complete'>[ACTIVE] Visualizing Path for Proof {st.session_state.active_proof}</div>",
                unsafe_allow_html=True,
            )

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="m2_1"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 1:</div>{show_hint('m2', 1)}</div>",
                    unsafe_allow_html=True,
                )
        with col2:
            if st.button("Hint 2", key="m2_2"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 2:</div>{show_hint('m2', 2)}</div>",
                    unsafe_allow_html=True,
                )
        with col3:
            if st.button("Hint 3", key="m2_3"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 3:</div>{show_hint('m2', 3)}</div>",
                    unsafe_allow_html=True,
                )
