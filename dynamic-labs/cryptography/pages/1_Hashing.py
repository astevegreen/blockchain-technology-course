import streamlit as st
from lab_core import LabCore
from lesson_loader import load_lesson
from progress_beacon import fire as _fire_progress
from terminal_ui import (
    install_terminal_keyboard_shortcuts,
    render_hint,
    render_terminal_history,
)

_SCENARIO_BEACONS = {
    "1. Weak Hash Collisions": "exercise:crypto-hashing-s1",
    "2. The Avalanche Effect": "exercise:crypto-hashing-s2",
    "3. Entropy & Ransomware": "exercise:crypto-hashing-s3",
}

TERMINAL_COMMANDS = [
    "cat",
    "hash_and_decrypt",
    "help",
    "sha256",
    "toy_check",
    "toy_hash",
]

# --- SETUP & STATE ---
if "lab_core" not in st.session_state:
    st.session_state.lab_core = LabCore()

if "history1" not in st.session_state:
    st.session_state.history1 = []

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
.stForm { border: none; }

.status-incomplete { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; font-weight: bold; }
.status-complete { background-color: #d1e7dd; border-left: 4px solid #0f5132; padding: 10px; margin: 10px 0; font-weight: bold; color: #0f5132; }

.hint-box { background-color: #cfe2ff; border: 1px solid #084298; padding: 15px; margin: 10px 0; border-radius: 5px; }
.hint-title { color: #084298; font-weight: bold; margin-bottom: 10px; }

.success-box { background-color: #d1e7dd; border: 2px solid #0f5132; padding: 15px; margin: 10px 0; border-radius: 5px; font-weight: bold; color: #0f5132; }
</style>
""",
    unsafe_allow_html=True,
)


# --- COMMAND PROCESSOR ---
def command_payload(raw_input, cmd):
    payload = raw_input.lstrip()[len(cmd) :]
    if payload.startswith(" "):
        return payload[1:]
    return payload


def hashing_help(topic, active_scenario):
    topic = topic.lower()
    if topic == "weak":
        return """Weak-hash commands:
  toy_hash <text>
      Show the 4-bit toy hash for any text.
  toy_check <text>
      Submit a changed transaction and check whether it spoofs the target hash.

Examples:
  toy_hash PAY: ALICE | AMT: $100
  toy_check PAY: BOB | AMT: $900

Tip: In this scenario, spaces and punctuation are part of the message."""

    if topic == "avalanche":
        return """Avalanche commands:
  sha256 <text>
      Generate a SHA-256 hash for the exact text after the command.

Examples:
  sha256 Deployment Alpha
  sha256 Deployment alpha

Compare the two full hashes. A one-character change should change the whole output."""

    if topic == "ransomware":
        return """Ransomware commands:
  cat /root/README_FOR_DECRYPT.txt
      Read the ransom note.
  hash_and_decrypt <start_val> <end_val>
      Test a 10-value seed window.

Examples:
  cat /root/README_FOR_DECRYPT.txt
  hash_and_decrypt 1736670470 1736670480

Use the file modified time from the telemetry to estimate the malware start time."""

    topic_by_scenario = {
        "1. Weak Hash Collisions": "weak",
        "2. The Avalanche Effect": "avalanche",
        "3. Entropy & Ransomware": "ransomware",
    }
    default_topic = topic_by_scenario.get(active_scenario, "weak")
    return f"""Available help topics:
  help weak
  help avalanche
  help ransomware

Current scenario quick start:
{hashing_help(default_topic, active_scenario)}"""


def process_command():
    user_input = st.session_state.input_box1 or ""
    stripped_input = user_input.strip()
    if not stripped_input:
        st.session_state.input_box1 = ""
        return

    command_input = user_input.lstrip()
    parts = command_input.split()
    cmd = parts[0].lower()
    args = parts[1:]
    lab = st.session_state.lab_core
    active_scenario = st.session_state.get(
        "hashing_scenario", "1. Weak Hash Collisions"
    )
    output = ""

    if cmd == "toy_hash":
        output = f"Hash: {lab.toy_hash_4bit(command_payload(user_input, parts[0]))}"
    elif cmd == "toy_check":
        s, h = lab.check_toy_collision(command_payload(user_input, parts[0]))
        output = f"Hash: {h} " + ("[SUCCESS: SPOOFED!]" if s else "[FAIL]")
    elif cmd == "sha256":
        text = command_payload(user_input, parts[0])
        output = f"SHA-256: {lab.sha256_hash(text)}"

    elif cmd == "cat":
        if args and args[0] == "/root/README_FOR_DECRYPT.txt":
            output = lab.get_ransom_note()
        else:
            output = f"cat: {' '.join(args)}: No such file or directory"

    elif cmd == "hash_and_decrypt":
        if len(args) != 2:
            output = "Usage: hash_and_decrypt <start_val> <end_val>"
        else:
            try:
                s, e = int(args[0]), int(args[1])
                if (e - s) > 10:
                    output = "[ERROR]: Batch size limit exceeded. Maximum 10 units per attempt to conserve CPU."
                else:
                    found = False
                    for t in range(s, e + 1):
                        suc, msg = lab.attempt_decrypt(t)
                        if suc:
                            output = f"[SUCCESS] KEY FOUND derived from seed: {t}\n\nDecrypted Data: {msg}"
                            found = True
                            break
                    if not found:
                        output = f"Tested {s}-{e}: [DECRYPTION FAILED] - Valid seed not found in this interval."
            except ValueError:
                output = "[ERROR]: Bounds must be integers."
    elif cmd == "help":
        output = hashing_help(args[0] if args else "", active_scenario)
    else:
        output = f"Unknown command: {cmd}\nType 'help' for assistance."

    st.session_state.history1.insert(0, (stripped_input, output))
    st.session_state.input_box1 = ""


# --- HINT SYSTEM ---
def show_hint(scenario, level):
    hints = {
        "h1": {
            1: "The 4-bit hash simply adds the ASCII values of the characters together. You just need the math to equal the target.",
            2: "If you change a letter to one that has a lower ASCII value, you can just add a space or some punctuation at the end of the message to make up the difference.",
            3: "Try submitting the exact target string, but just add a few spaces to the end until the hash wraps around and matches.",
        },
        "h2": {
            1: "Run the command on 'Deployment Alpha'. Note the resulting hex string.",
            2: "Run the command on 'Deployment alpha'. Compare it to the first string.",
            3: "Notice how changing a single uppercase letter completely randomized the entire output string. This is why SHA-256 is secure.",
        },
        "h3": {
            1: "How did the `linux.encoder` malware generate its encryption keys? You might want to check your notes from the 'Cryptographic Assumptions and Challenges' lecture.",
            2: "The `linux.encoder` malware seeded its pseudo-random number generator using the system's state at the exact moment the malware process started executing.",
            3: "Scan the telemetry for a timestamp. Convert the 'File Last Modified' time to a Unix timestamp. The malware process started running just before this file was finally saved (usually within a 1 to 5 minute window).",
        },
    }
    hint_text = hints.get(scenario, {}).get(level, "No more hints available.")
    st.session_state.hints_shown[f"{scenario}_lvl{level}"] = True
    return hint_text


# --- UI LAYOUT ---
st.sidebar.title("Module 1: Hashing & Entropy")
st.sidebar.markdown(
    "**Learning Goal:** Understand pre-image resistance and the dangers of low-entropy seeds."
)

scenario = st.sidebar.radio(
    "Select Scenario",
    [
        "1. Weak Hash Collisions",
        "2. The Avalanche Effect",
        "3. Entropy & Ransomware",
    ],
    key="hashing_scenario",
)
_fire_progress(_SCENARIO_BEACONS.get(scenario, ""))

col_term, col_vis = st.columns([1, 1])

with col_term:
    st.subheader("Terminal")
    st.text_input("Enter Command", key="input_box1", on_change=process_command)
    install_terminal_keyboard_shortcuts(
        "Enter Command", TERMINAL_COMMANDS, st.session_state.history1
    )
    st.caption("Type a command and press Enter.")

    render_terminal_history(st.session_state.history1)

with col_vis:
    lab = st.session_state.lab_core

    if scenario == "1. Weak Hash Collisions":
        st.markdown("### Scenario 1: Weak Hash Collisions")
        st.markdown(load_lesson("crypto-hashing-s1").format(**lab.template_ctx()))
        st.markdown("")
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="h1_1"):
                render_hint("HINT 1:", show_hint("h1", 1))
        with col2:
            if st.button("Hint 2", key="h1_2"):
                render_hint("HINT 2:", show_hint("h1", 2))
        with col3:
            if st.button("Hint 3", key="h1_3"):
                render_hint("HINT 3:", show_hint("h1", 3))

    elif scenario == "2. The Avalanche Effect":
        st.markdown("### Scenario 2: The Avalanche Effect")
        st.markdown(load_lesson("crypto-hashing-s2"))
        st.markdown("")
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="h2_1"):
                render_hint("HINT 1:", show_hint("h2", 1))
        with col2:
            if st.button("Hint 2", key="h2_2"):
                render_hint("HINT 2:", show_hint("h2", 2))
        with col3:
            if st.button("Hint 3", key="h2_3"):
                render_hint("HINT 3:", show_hint("h2", 3))

    elif scenario == "3. Entropy & Ransomware":
        st.markdown("### Scenario 3: Entropy & Ransomware")
        st.markdown(load_lesson("crypto-hashing-s3").format(**lab.template_ctx()))
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="h3_1"):
                render_hint("HINT 1:", show_hint("h3", 1))
        with col2:
            if st.button("Hint 2", key="h3_2"):
                render_hint("HINT 2:", show_hint("h3", 2))
        with col3:
            if st.button("Hint 3", key="h3_3"):
                render_hint("HINT 3:", show_hint("h3", 3))
