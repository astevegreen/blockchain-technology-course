import html as html_lib
import re
import streamlit as st
from lab_core import LabCore
from lesson_loader import load_lesson
from progress_beacon import fire as _fire_progress
from terminal_ui import (
    install_terminal_command_builder,
    install_terminal_keyboard_shortcuts,
    render_hint,
    render_terminal_history,
)

_SCENARIO_BEACONS = {
    "1. Build a Tree": "exercise:crypto-merkle-s1",
    "2. Verify a Proof": "exercise:crypto-merkle-s2",
}

TERMINAL_COMMANDS = [
    "combine",
    "fill_leaf",
    "get_proof",
    "hash_pair",
    "help",
    "list_tx",
    "sha256",
]

TERMINAL_INPUT_LABEL = "Enter Command (Press Enter to submit)"
MERKLE_BUILDER_ID = "merkle-command-builder"
MERKLE_COMMAND_SPECS = {
    "list_tx": {
        "label": "list_tx",
        "description": "Show the transaction strings.",
        "slots": [],
    },
    "sha256": {
        "label": "sha256",
        "description": "Hash a transaction string.",
        "slots": [
            {
                "name": "text",
                "placeholder": "click a transaction",
                "accepts": ["tx_text"],
            }
        ],
    },
    "fill_leaf": {
        "label": "fill_leaf",
        "description": "Fill a leaf slot with a transaction hash.",
        "slots": [
            {
                "name": "leaf",
                "placeholder": "click Leaf-0..Leaf-7",
                "accepts": ["leaf_target"],
            },
            {
                "name": "hash",
                "placeholder": "click a calculated hash",
                "accepts": ["hash"],
            },
        ],
    },
    "combine": {
        "label": "combine",
        "description": "Build a parent node from left and right hashes.",
        "slots": [
            {
                "name": "target",
                "placeholder": "click L1/L2/ROOT",
                "accepts": ["internal_target"],
            },
            {
                "name": "left hash",
                "placeholder": "click the left child hash",
                "accepts": ["hash"],
            },
            {
                "name": "right hash",
                "placeholder": "click the right child hash",
                "accepts": ["hash"],
            },
        ],
    },
    "get_proof": {
        "label": "get_proof",
        "description": "Load proof A or proof B.",
        "slots": [
            {
                "name": "proof",
                "placeholder": "click A or B",
                "accepts": ["proof_id"],
            }
        ],
    },
    "hash_pair": {
        "label": "hash_pair",
        "description": "Combine two proof-path hashes.",
        "slots": [
            {
                "name": "left hash",
                "placeholder": "click the left hash",
                "accepts": ["hash"],
            },
            {
                "name": "right hash",
                "placeholder": "click the right hash",
                "accepts": ["hash"],
            },
        ],
    },
}
SCENARIO_BUILDER_COMMANDS = {
    "1. Build a Tree": ["list_tx", "sha256", "fill_leaf", "combine"],
    "2. Verify a Proof": ["get_proof", "sha256", "hash_pair"],
}

# --- SETUP & STATE ---
if "lab_core" not in st.session_state:
    st.session_state.lab_core = LabCore()

if "history2" not in st.session_state:
    st.session_state.history2 = []

if "active_proof" not in st.session_state:
    st.session_state.active_proof = None

if "merkle_proof_a_verified" not in st.session_state:
    st.session_state.merkle_proof_a_verified = False

if "merkle_proof_completed" not in st.session_state:
    st.session_state.merkle_proof_completed = False

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
.status-active { background-color: #cff4fc; border-left: 4px solid #0dcaf0; padding: 10px; margin: 10px 0; font-weight: bold; color: #055160; }

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

.merkle-command-inline {
    display: inline-flex;
    align-items: center;
    border: 1px solid #9ca3af;
    border-radius: 4px;
    padding: 0 4px;
    background: #f9fafb;
    color: #111827;
    cursor: pointer;
    font: inherit;
}
.merkle-command-inline:hover,
.merkle-command-inline:focus {
    border-color: #2563eb;
    background: #eff6ff;
    outline: 2px solid rgba(37, 99, 235, 0.18);
    outline-offset: 1px;
}

.merkle-command-builder {
    border: 1px solid #d0d5dd;
    border-radius: 6px;
    padding: 10px;
    margin: 8px 0 12px 0;
    background: #ffffff;
}
.merkle-builder-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 8px;
}
.merkle-builder-title {
    font-weight: 700;
    color: #101828;
}
.merkle-builder-toggle {
    border: 1px solid #98a2b3;
    border-radius: 4px;
    padding: 5px 8px;
    background: #ffffff;
    color: #344054;
    cursor: pointer;
    font-size: 12px;
}
.merkle-builder-toggle:hover,
.merkle-builder-toggle:focus {
    border-color: #2563eb;
    color: #1d4ed8;
    outline: 2px solid rgba(37, 99, 235, 0.15);
}
.merkle-builder-disabled .merkle-builder-body {
    display: none;
}
.merkle-command-buttons {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 6px;
    margin-bottom: 8px;
}
.merkle-command-button {
    border: 1px solid #d0d5dd;
    border-radius: 4px;
    background: #f9fafb;
    color: #101828;
    cursor: pointer;
    padding: 7px;
    text-align: left;
}
.merkle-command-button:hover,
.merkle-command-button:focus,
.merkle-command-active {
    border-color: #2563eb;
    background: #eff6ff;
    outline: 2px solid rgba(37, 99, 235, 0.14);
}
.merkle-command-name {
    display: block;
    font-family: "Courier New", monospace;
    font-weight: 700;
    font-size: 13px;
}
.merkle-command-desc {
    display: block;
    color: #475467;
    font-size: 11px;
    line-height: 1.25;
    margin-top: 2px;
}
.merkle-command-slots {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.merkle-slot,
.merkle-slot-placeholder {
    min-height: 42px;
    border-radius: 4px;
    border: 1px dashed #98a2b3;
    background: #ffffff;
    color: #475467;
    padding: 6px 8px;
}
.merkle-slot {
    cursor: pointer;
    text-align: left;
    min-width: 125px;
}
.merkle-slot-active {
    border-style: solid;
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.14);
}
.merkle-slot-filled {
    border-style: solid;
    border-color: #16a34a;
    background: #f0fdf4;
}
.merkle-slot-name {
    display: block;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    color: #667085;
}
.merkle-slot-value {
    display: block;
    max-width: 210px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-family: "Courier New", monospace;
    font-size: 12px;
}
.merkle-token-panel {
    border: 1px solid #d0d5dd;
    border-radius: 6px;
    padding: 10px;
    margin: 8px 0 12px 0;
    background: #ffffff;
}
.merkle-token-title {
    font-weight: 700;
    color: #101828;
    margin-bottom: 6px;
}
.merkle-token-group {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
}
.merkle-token-button {
    border: 1px solid #d0d5dd;
    border-radius: 4px;
    padding: 5px 7px;
    background: #f9fafb;
    color: #101828;
    cursor: default;
    font-family: "Courier New", monospace;
    font-size: 12px;
}
.merkle-token-node {
    cursor: default;
}
button.merkle-box,
button.node-base {
    cursor: default;
}
.merkle-token-valid {
    border-color: #2563eb !important;
    background: #eff6ff !important;
    color: #1e3a8a !important;
    cursor: pointer !important;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.16) !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# --- HELPER: COMMAND BUILDER AND CLICKABLE TOKENS ---
def _safe_html(value):
    return html_lib.escape(str(value))


def _safe_attr(value):
    return html_lib.escape(str(value), quote=True)


def command_builder_config(active_scenario):
    command_names = SCENARIO_BUILDER_COMMANDS[active_scenario]
    return {
        "builder_id": MERKLE_BUILDER_ID,
        "config_key": active_scenario,
        "commands": {
            command_name: MERKLE_COMMAND_SPECS[command_name]
            for command_name in command_names
        },
        "default_command": command_names[0],
    }


def token_button(label, tokens, class_name="merkle-token-button", title=None):
    token_types = " ".join(token["type"] for token in tokens)
    attrs = [
        'type="button"',
        'data-merkle-token="true"',
        f'data-merkle-token-types="{_safe_attr(token_types)}"',
    ]
    for token in tokens:
        token_type = token["type"]
        attrs.append(
            f'data-merkle-token-value-{token_type}="{_safe_attr(token["value"])}"'
        )
        attrs.append(
            f'data-merkle-token-label-{token_type}="{_safe_attr(token.get("label", token["value"]))}"'
        )
    if title:
        attrs.append(f'title="{_safe_attr(title)}"')

    return (
        f'<button class="{_safe_attr(class_name)}" {" ".join(attrs)}>'
        f"{_safe_html(label)}</button>"
    )


def render_command_builder_panel(config):
    command_buttons = []
    for command_name, spec in config["commands"].items():
        command_buttons.append(
            "<button type='button' class='merkle-command-button' "
            f"data-merkle-command='{_safe_attr(command_name)}'>"
            f"<span class='merkle-command-name'>{_safe_html(spec['label'])}</span>"
            f"<span class='merkle-command-desc'>{_safe_html(spec['description'])}</span>"
            "</button>"
        )

    st.markdown(
        f"""
<div class="merkle-command-builder" data-merkle-builder="{_safe_attr(config['builder_id'])}">
    <div class="merkle-builder-header">
        <div class="merkle-builder-title">Command Builder</div>
        <button type="button" class="merkle-builder-toggle" data-merkle-builder-toggle>
            Disable simplified console
        </button>
    </div>
    <div class="merkle-builder-body">
        <div class="merkle-command-buttons">{''.join(command_buttons)}</div>
        <div class="merkle-command-slots" data-merkle-command-slots>
            <span class="merkle-slot-placeholder">Choose a command.</span>
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_merkle_lesson(lesson_id, active_scenario):
    config = command_builder_config(active_scenario)
    commands = set(config["commands"])
    lesson = load_lesson(lesson_id)

    def replace_code_span(match):
        code_text = match.group(1)
        parts = code_text.strip().split()
        if not parts:
            return match.group(0)
        command = parts[0].lower()
        if command not in commands:
            return match.group(0)
        return (
            '<button type="button" class="merkle-command-inline" '
            f'data-merkle-command="{_safe_attr(command)}">'
            f"<code>{_safe_html(code_text)}</code>"
            "</button>"
        )

    rendered = re.sub(r"`([^`]+)`", replace_code_span, lesson)
    st.markdown(rendered, unsafe_allow_html=True)


def render_token_shortcuts(lab, active_scenario):
    sections = []

    def add_section(title, buttons, empty_text=None):
        if buttons:
            body = "".join(buttons)
        elif empty_text:
            body = f"<span class='merkle-slot-placeholder'>{_safe_html(empty_text)}</span>"
        else:
            return
        sections.append(
            f"<div class='merkle-token-title'>{_safe_html(title)}</div>"
            f"<div class='merkle-token-group'>{body}</div>"
        )

    if active_scenario == "1. Build a Tree":
        tx_buttons = [
            token_button(
                f"Tx{i}",
                [
                    {
                        "type": "tx_text",
                        "value": tx,
                        "label": tx,
                    }
                ],
                title=tx,
            )
            for i, tx in enumerate(lab.merkle_txs)
        ]
        add_section("Transactions", tx_buttons)
    else:
        proof_buttons = [
            token_button(
                "Proof A",
                [{"type": "proof_id", "value": "A", "label": "A"}],
                title="Load proof A",
            ),
            token_button(
                "Proof B",
                [{"type": "proof_id", "value": "B", "label": "B"}],
                title="Load proof B",
            ),
        ]
        add_section("Proofs", proof_buttons)

        active_proof = st.session_state.active_proof
        if active_proof == "A":
            proof_tx = lab.proof_a_tx
            siblings = lab.proof_a_siblings
        elif active_proof == "B":
            proof_tx = lab.proof_b_tx
            siblings = lab.proof_b_siblings
        else:
            proof_tx = None
            siblings = []

        if proof_tx:
            add_section(
                "Loaded Transaction",
                [
                    token_button(
                        active_proof,
                        [
                            {
                                "type": "tx_text",
                                "value": proof_tx,
                                "label": proof_tx,
                            }
                        ],
                        title=proof_tx,
                    )
                ],
            )
            sibling_buttons = [
                token_button(
                    f"Step {i} {step['pos']}",
                    [
                        {
                            "type": "hash",
                            "value": step["hash"],
                            "label": f"step {i} {step['pos']} sibling {step['hash'][:8]}...",
                        }
                    ],
                    title=step["hash"],
                )
                for i, step in enumerate(siblings, start=1)
            ]
            add_section("Sibling Hashes", sibling_buttons)
        else:
            add_section(
                "Loaded Proof Values",
                [],
                "Choose Proof A or Proof B, then run the command.",
            )

    if sections:
        st.markdown(
            f"<div class='merkle-token-panel'>{''.join(sections)}</div>",
            unsafe_allow_html=True,
        )


# --- HELPER: RENDER GRID TREE ---
def render_large_tree(active_proof_id, lab):
    path_map = {}
    proof_tx = None
    proof_siblings = []
    if active_proof_id == "A":
        proof_tx = lab.proof_a_tx
        proof_siblings = lab.proof_a_siblings
        path_map = {
            4: {"user": 2, "sib": 3},
            3: {"user": 1, "sib": 0},
            2: {"user": 0, "sib": 1},
            1: {"user": 0, "sib": 1},
            0: {"user": 0},
        }
    elif active_proof_id == "B":
        proof_tx = lab.proof_b_tx
        proof_siblings = lab.proof_b_siblings
        path_map = {
            4: {"user": 13, "sib": 12},
            3: {"user": 6, "sib": 7},
            2: {"user": 3, "sib": 2},
            1: {"user": 1, "sib": 0},
            0: {"user": 0},
        }

    sibling_by_level = {
        4: proof_siblings[0] if len(proof_siblings) > 0 else None,
        3: proof_siblings[1] if len(proof_siblings) > 1 else None,
        2: proof_siblings[2] if len(proof_siblings) > 2 else None,
        1: proof_siblings[3] if len(proof_siblings) > 3 else None,
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
                            "ROOT"
                            if level == 0
                            else (f"Tx {active_proof_id}" if level == 4 else "Hash")
                        )
                    elif i == info.get("sib"):
                        css_class = "node-sib"
                        content = f"Sib {5 - level}"
            if level == 0 and not active_proof_id:
                content = "ROOT"
                css_class = "node-ghost"

            token_markup = None
            if active_proof_id and content.startswith("Tx") and proof_tx:
                token_markup = token_button(
                    content,
                    [
                        {
                            "type": "tx_text",
                            "value": proof_tx,
                            "label": proof_tx,
                        }
                    ],
                    class_name=f"node-base {css_class} merkle-token-node",
                    title=proof_tx,
                )
            elif active_proof_id and content.startswith("Sib"):
                sibling = sibling_by_level.get(level)
                if sibling:
                    token_markup = token_button(
                        content,
                        [
                            {
                                "type": "hash",
                                "value": sibling["hash"],
                                "label": f"{content} {sibling['pos']} {sibling['hash'][:8]}...",
                            }
                        ],
                        class_name=f"node-base {css_class} merkle-token-node",
                        title=sibling["hash"],
                    )

            html += token_markup or f"<div class='node-base {css_class}'>{content}</div>"
        html += "</div>"
    html += "</div>"
    return html


def render_node(val, label):
    tokens = []
    if label.startswith("Leaf-"):
        tokens.append({"type": "leaf_target", "value": label, "label": label})
    elif label == "ROOT" or label.startswith("L"):
        tokens.append({"type": "internal_target", "value": label, "label": label})

    if val:
        tokens.append(
            {
                "type": "hash",
                "value": val,
                "label": f"{label} hash {val[:8]}...",
            }
        )

    css_class = "box-filled" if val else "box-empty"
    display = f"[OK] {val[:6]}..." if val else label
    node = token_button(
        display,
        tokens,
        class_name=f"merkle-box {css_class} merkle-token-node",
        title=f"{label}: {val}" if val else label,
    )
    st.markdown(
        f"<div class='centered-col'>{node}</div>",
        unsafe_allow_html=True,
    )


def render_section_status(is_complete, complete_text, incomplete_text):
    if is_complete:
        st.markdown(
            f"<div class='status-complete'>&#9745; [COMPLETE] {complete_text}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='status-incomplete'>&#9744; [IN PROGRESS] {incomplete_text}</div>",
            unsafe_allow_html=True,
        )


def build_tree_complete(lab):
    return lab.student_root == lab.root


def compute_proof_root(lab, tx_data, siblings):
    curr = lab.sha256_hash(tx_data)
    for step in siblings:
        if step["pos"] == "right":
            curr = lab.sha256_hash(curr + step["hash"])
        else:
            curr = lab.sha256_hash(step["hash"] + curr)
    return curr


def proof_a_root(lab):
    return compute_proof_root(lab, lab.proof_a_tx, lab.proof_a_siblings)


def proof_b_actual_root(lab):
    return compute_proof_root(lab, lab.proof_b_tx, lab.proof_b_siblings)


# --- COMMAND PROCESSOR ---
def merkle_help(topic, active_scenario):
    topic = topic.lower()
    if topic == "build":
        return """Build-a-tree commands:
  list_tx
      Show the transaction strings.
  sha256 <transaction text>
      Hash one transaction string.
  fill_leaf <Leaf-0..Leaf-7> <hash>
      Fill a leaf node. Leaf-7 should reuse the Leaf-6 hash.
  combine <L1-0..L1-3|L2-0..L2-1|ROOT> <left_hash> <right_hash>
      Fill a specific parent node.

Examples:
  sha256 Tx0: Payroll -> Alice
  fill_leaf Leaf-0 <hash from sha256>
  fill_leaf Leaf-7 <same hash as Leaf-6>
  combine L1-0 <Leaf-0 hash> <Leaf-1 hash>
  combine ROOT <L2-0 hash> <L2-1 hash>

Tip: Click any filled node in the tree to copy its full hash."""

    if topic == "combine":
        return """Combine syntax:
  combine <target_node> <left_hash> <right_hash>

Target nodes:
  L1-0 L1-1 L1-2 L1-3
  L2-0 L2-1
  ROOT

Examples:
  combine L1-0 <Leaf-0 hash> <Leaf-1 hash>
  combine L2-1 <L1-2 hash> <L1-3 hash>
  combine ROOT <L2-0 hash> <L2-1 hash>

Order matters: always put the left child hash before the right child hash."""

    if topic == "proof":
        return """Proof commands:
  get_proof <A|B>
      Load a transaction and its sibling path.
  sha256 <transaction text>
      Hash the proof transaction.
  hash_pair <hash_L> <hash_R>
      Manually combine two hashes without filling the build tree.

Examples:
  get_proof A
  sha256 Tx: Supply Purchase Order #9921
  hash_pair <current hash> <right sibling hash>

Use the sibling position from the proof: if the sibling is left, put the sibling hash first."""

    default_topic = "build" if active_scenario == "1. Build a Tree" else "proof"
    return f"""Available help topics:
  help build
  help combine
  help proof

Current scenario quick start:
{merkle_help(default_topic, active_scenario)}"""


def process_command(user_input, active_scenario):
    stripped_input = user_input.strip()
    if not stripped_input:
        return

    parts = stripped_input.split()
    cmd = parts[0].lower()
    args = parts[1:]
    lab = st.session_state.lab_core
    output = ""

    if cmd == "list_tx":
        output = "Transactions:\n" + "\n".join(
            [f"{i}: {tx}" for i, tx in enumerate(lab.merkle_txs)]
        )
    elif cmd == "sha256":
        text = stripped_input.split(maxsplit=1)[1] if len(parts) > 1 else ""
        output = f"SHA-256: {lab.sha256_hash(text)}"
    elif cmd == "hash_pair":
        if len(args) == 2:
            pair_hash = lab.sha256_hash(args[0] + args[1])
            output = f"Pair Hash: {pair_hash}"
            if st.session_state.active_proof == "A" and pair_hash == proof_a_root(lab):
                st.session_state.merkle_proof_a_verified = True
                output += "\n[SUCCESS] Proof A resolves to the official root."
            elif (
                st.session_state.active_proof == "B"
                and pair_hash == proof_b_actual_root(lab)
                and pair_hash != lab.lg_official_root
            ):
                st.session_state.merkle_proof_completed = True
                output += (
                    "\n[SUCCESS] Proof B recomputes to a different root. "
                    "The transaction is a forgery."
                )
        else:
            output = "Usage: hash_pair <hash_L> <hash_R>"
    elif cmd == "fill_leaf":
        if len(args) == 2:
            output = lab.fill_leaf(args[0], args[1])[1]
        else:
            output = "Usage: fill_leaf <Leaf-0..Leaf-7> <hash>"
    elif cmd == "combine":
        if len(args) == 3:
            output = lab.combine_into(args[0], args[1], args[2])[1]
            if build_tree_complete(lab):
                output += "\n[SUCCESS] Merkle tree complete. Your root matches the expected block root."
        elif len(args) == 2:
            output = lab.smart_combine(args[0], args[1])[1]
        else:
            output = "Usage: combine <target_node> <L_hash> <R_hash>\nExample: combine L1-0 <Leaf-0 hash> <Leaf-1 hash>"
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
        topic = args[0] if args else ""
        output = merkle_help(topic, active_scenario)
    else:
        output = f"Unknown command: {cmd}\nType 'help' for assistance."

    st.session_state.history2.insert(0, (stripped_input, output))


# --- HINT SYSTEM ---
def show_hint(scenario, level):
    hints = {
        "m1": {
            1: "First, generate the hash for each transaction string using `sha256 <text>`, then use `fill_leaf Leaf-0 <hash>` to place it.",
            2: "There are only 7 transactions, but the tree needs 8 leaves to balance. Use the same hash for `Leaf-6` and `Leaf-7`.",
            3: "When combining hashes, order matters! Always put the left child first and target the parent, like `combine L1-0 <Leaf-0 hash> <Leaf-1 hash>`.",
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
lab = st.session_state.lab_core
builder_config = command_builder_config(scenario)

# --- TERMINAL FORM FIX ---
with col_term:
    st.subheader("Terminal")

    with st.form("terminal_form", clear_on_submit=True):
        user_cmd = st.text_input(TERMINAL_INPUT_LABEL)
        submitted = st.form_submit_button("Run")

        if submitted:
            process_command(user_cmd, scenario)

    render_command_builder_panel(builder_config)
    render_token_shortcuts(lab, scenario)
    install_terminal_keyboard_shortcuts(
        TERMINAL_INPUT_LABEL,
        TERMINAL_COMMANDS,
        st.session_state.history2,
    )
    install_terminal_command_builder(TERMINAL_INPUT_LABEL, builder_config)
    render_terminal_history(st.session_state.history2)

with col_vis:
    if scenario == "1. Build a Tree":
        st.markdown("### Scenario 1: Build a Tree")
        render_section_status(
            build_tree_complete(lab),
            "SECTION PASSED: Merkle tree root matches the expected block root.",
            "Build the tree until ROOT is validated.",
        )
        render_merkle_lesson("crypto-merkle-s1", scenario)

        # Render Small Tree
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 1, 2])
        with c2:
            render_node(lab.student_root, "ROOT")
        st.markdown("<hr style='margin:5px 0;opacity:0.3'>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.5])
        with c2:
            render_node(lab.student_level2[0], "L2-0")
        with c3:
            render_node(lab.student_level2[1], "L2-1")
        st.markdown("<hr style='margin:5px 0;opacity:0.3'>", unsafe_allow_html=True)

        cols = st.columns([0.5, 1, 1, 1, 1, 0.5])
        for i in range(4):
            with cols[i + 1]:
                render_node(lab.student_level1[i], f"L1-{i}")
        st.markdown("<hr style='margin:5px 0;opacity:0.3'>", unsafe_allow_html=True)

        cols = st.columns(8)
        for i in range(8):
            with cols[i]:
                render_node(lab.student_leaves[i], f"Leaf-{i}")

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="m1_1"):
                render_hint("HINT 1:", show_hint("m1", 1))
        with col2:
            if st.button("Hint 2", key="m1_2"):
                render_hint("HINT 2:", show_hint("m1", 2))
        with col3:
            if st.button("Hint 3", key="m1_3"):
                render_hint("HINT 3:", show_hint("m1", 3))

    elif scenario == "2. Verify a Proof":
        st.markdown("### Scenario 2: Verify a Proof")
        render_section_status(
            st.session_state.merkle_proof_completed,
            "SECTION PASSED: Forged proof identified.",
            "Verify the proof path until the forgery is identified.",
        )
        render_merkle_lesson("crypto-merkle-s2", scenario)

        st.markdown(
            render_large_tree(st.session_state.active_proof, lab),
            unsafe_allow_html=True,
        )
        st.caption("Key: 🟦 Your Path | 🟨 Sibling Needed | ⬜ Background Data")

        if st.session_state.active_proof is None:
            st.markdown(
                "<div class='status-incomplete'>[WAITING] Run `get_proof A` or `get_proof B` to load path data.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='status-active'>[ACTIVE] Visualizing Path for Proof {st.session_state.active_proof}</div>",
                unsafe_allow_html=True,
            )

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="m2_1"):
                render_hint("HINT 1:", show_hint("m2", 1))
        with col2:
            if st.button("Hint 2", key="m2_2"):
                render_hint("HINT 2:", show_hint("m2", 2))
        with col3:
            if st.button("Hint 3", key="m2_3"):
                render_hint("HINT 3:", show_hint("m2", 3))
