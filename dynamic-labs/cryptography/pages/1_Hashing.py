import streamlit as st
from lab_core import LabCore
from lesson_loader import load_lesson
from progress_beacon import fire as _fire_progress

_SCENARIO_BEACONS = {
    "1. Weak Hash Collisions": "exercise:crypto-hashing-s1",
    "2. The Avalanche Effect": "exercise:crypto-hashing-s2",
    "3. Entropy & Ransomware": "exercise:crypto-hashing-s3",
}

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
def process_command():
    user_input = st.session_state.input_box1
    if not user_input:
        return
    parts = user_input.strip().split()
    cmd = parts[0].lower()
    args = parts[1:]
    lab = st.session_state.lab_core
    output = ""

    if cmd == "toy_hash":
        output = f"Hash: {lab.toy_hash_4bit(' '.join(args))}"
    elif cmd == "toy_check":
        s, h = lab.check_toy_collision(" ".join(args))
        output = f"Hash: {h} " + ("[SUCCESS: SPOOFED!]" if s else "[FAIL]")
    elif cmd == "sha256":
        text = " ".join(args)
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
        output = "Available commands vary by scenario. Check the scenario description on the right."
    else:
        output = f"Unknown command: {cmd}\nType 'help' for assistance."

    st.session_state.history1.insert(0, (user_input, output))
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
)
_fire_progress(_SCENARIO_BEACONS.get(scenario, ""))

col_term, col_vis = st.columns([1, 1])

with col_term:
    st.subheader("Terminal")
    st.text_input("Enter Command", key="input_box1", on_change=process_command)
    st.caption("Type a command and press Enter.")

    log_box = st.container(height=600)
    for c, o in st.session_state.history1:
        log_box.markdown(
            f"<div class='log-cmd'>>> {c}</div><div class='log-out'>{o}</div><hr style='margin:5px 0'>",
            unsafe_allow_html=True,
        )

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
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 1:</div>{show_hint('h1', 1)}</div>",
                    unsafe_allow_html=True,
                )
        with col2:
            if st.button("Hint 2", key="h1_2"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 2:</div>{show_hint('h1', 2)}</div>",
                    unsafe_allow_html=True,
                )
        with col3:
            if st.button("Hint 3", key="h1_3"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 3:</div>{show_hint('h1', 3)}</div>",
                    unsafe_allow_html=True,
                )

    elif scenario == "2. The Avalanche Effect":
        st.markdown("### Scenario 2: The Avalanche Effect")
        st.markdown(load_lesson("crypto-hashing-s2"))
        st.markdown("")
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="h2_1"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 1:</div>{show_hint('h2', 1)}</div>",
                    unsafe_allow_html=True,
                )
        with col2:
            if st.button("Hint 2", key="h2_2"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 2:</div>{show_hint('h2', 2)}</div>",
                    unsafe_allow_html=True,
                )
        with col3:
            if st.button("Hint 3", key="h2_3"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 3:</div>{show_hint('h2', 3)}</div>",
                    unsafe_allow_html=True,
                )

    elif scenario == "3. Entropy & Ransomware":
        st.markdown("### Scenario 3: Entropy & Ransomware")
        st.markdown(load_lesson("crypto-hashing-s3").format(**lab.template_ctx()))
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="h3_1"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 1:</div>{show_hint('h3', 1)}</div>",
                    unsafe_allow_html=True,
                )
        with col2:
            if st.button("Hint 2", key="h3_2"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 2:</div>{show_hint('h3', 2)}</div>",
                    unsafe_allow_html=True,
                )
        with col3:
            if st.button("Hint 3", key="h3_3"):
                st.markdown(
                    f"<div class='hint-box'><div class='hint-title'>HINT 3:</div>{show_hint('h3', 3)}</div>",
                    unsafe_allow_html=True,
                )
