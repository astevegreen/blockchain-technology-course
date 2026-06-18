import streamlit as st
from lab_core import LabCore
from lesson_loader import load_lesson
from progress_beacon import fire as _fire_progress
from terminal_ui import (
    install_terminal_keyboard_shortcuts,
    render_hint,
    render_terminal_history,
)

# --- SETUP & STATE ---
st.set_page_config(layout="wide", page_title="Module 3: Cryptography")

_SCENARIO_BEACONS = {
    "1. The Leaked S1 Record": "exercise:crypto-symasym-s1",
    "2. The Embassy Collaborator": "exercise:crypto-symasym-s2",
    "3. Forged Ambassador Cables": "exercise:crypto-symasym-s3",
    "4. The 1GB ISR Video": "exercise:crypto-symasym-s4",
}

TERMINAL_COMMANDS = [
    "encrypt_record",
    "help",
    "send_file",
    "send_key_encrypted",
    "send_key_plaintext",
    "status",
    "verify_cable",
    "verify_signature",
    "view_cables",
    "view_intercept",
    "view_record",
]

if "lab3" not in st.session_state:
    st.session_state.lab3 = LabCore()

if "history3" not in st.session_state:
    st.session_state.history3 = []

if "hints_shown" not in st.session_state:
    st.session_state.hints_shown = {}


# --- CSS STYLING ---
st.markdown(
    """
<style>
/* Terminal & Form */
.stTextInput > div > div > input { font-family: 'Courier New', monospace; color: #333; }
.log-text { font-family: 'Courier New', monospace; font-size: 14px; white-space: pre-wrap; margin-bottom: 5px; }
.log-cmd { color: #2e86c1; font-weight: bold; }
.log-out { color: #333; white-space: pre-wrap; }
.stForm { border: none; }

/* Status indicators */
.status-incomplete { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; font-weight: bold; }
.status-complete { background-color: #d1e7dd; border-left: 4px solid #0f5132; padding: 10px; margin: 10px 0; font-weight: bold; color: #0f5132; }

/* Hint boxes */
.hint-box { background-color: #cfe2ff; border: 1px solid #084298; padding: 15px; margin: 10px 0; border-radius: 5px; }
.hint-title { color: #084298; font-weight: bold; margin-bottom: 10px; }

/* Success box */
.success-box { background-color: #d1e7dd; border: 2px solid #0f5132; padding: 15px; margin: 10px 0; border-radius: 5px; font-weight: bold; color: #0f5132; }
</style>
""",
    unsafe_allow_html=True,
)


# --- COMMAND PROCESSOR ---
def crypto_help(topic, active_scenario):
    topic = topic.lower()
    if topic in ("s1", "record"):
        return """Leaked S1 record commands:
  view_record
      Show the signed personnel record.
  verify_signature
      Check whether the signature is authentic.
  encrypt_record <symmetric|asymmetric|hybrid>
      Apply an encryption architecture.

Examples:
  view_record
  verify_signature
  encrypt_record asymmetric"""

    if topic in ("s2", "collaborator"):
        return """Embassy collaborator commands:
  view_intercept
      Show the encrypted message situation.
  send_key_plaintext
      Try sending the symmetric key without protection.
  send_key_encrypted
      Encrypt the symmetric key with the collaborator's public key.

Examples:
  view_intercept
  send_key_plaintext
  send_key_encrypted"""

    if topic in ("s3", "cables"):
        return """Forged cable commands:
  view_cables
      Show all received cables.
  verify_cable <A|B|C> <public_key_reference>
      Verify one cable against a named public key.

Examples:
  view_cables
  verify_cable A amb_public_key
  verify_cable B amb_public_key"""

    if topic in ("s4", "video"):
        return """ISR video commands:
  send_file <symmetric|asymmetric|hybrid>
      Try a file-transfer encryption architecture.

Examples:
  send_file symmetric
  send_file asymmetric
  send_file hybrid"""

    if topic == "status":
        return """Utility command:
  status
      Show completion state for all Module 3 scenarios."""

    topic_by_scenario = {
        "1. The Leaked S1 Record": "s1",
        "2. The Embassy Collaborator": "s2",
        "3. Forged Ambassador Cables": "s3",
        "4. The 1GB ISR Video": "s4",
    }
    default_topic = topic_by_scenario.get(active_scenario, "s1")
    return f"""Available help topics:
  help s1
  help s2
  help s3
  help s4
  help status

Current scenario quick start:
{crypto_help(default_topic, active_scenario)}"""


def process_command():
    user_input = st.session_state.input_box or ""
    stripped_input = user_input.strip()
    if not stripped_input:
        st.session_state.input_box = ""
        return
    parts = stripped_input.split()
    cmd = parts[0].lower()
    args = parts[1:]
    lab = st.session_state.lab3
    active_scenario = st.session_state.get(
        "crypto_scenario", "1. The Leaked S1 Record"
    )
    output = ""

    # ==========================================
    # SCENARIO 1 COMMANDS
    # ==========================================
    if cmd == "view_record":
        output = lab.s1_view_record()
    elif cmd == "verify_signature":
        output = lab.s1_verify_signature()
    elif cmd == "encrypt_record":
        method = args[0].lower() if len(args) == 1 else ""
        if method in ["symmetric", "asymmetric", "hybrid"]:
            output = lab.s1_encrypt_record(method)
        else:
            output = "Usage: encrypt_record <symmetric|asymmetric|hybrid>"

    # ==========================================
    # SCENARIO 2 COMMANDS
    # ==========================================
    elif cmd == "view_intercept":
        output = lab.s2_view_intercept()
    elif cmd == "send_key_plaintext":
        output = lab.s2_send_key_plaintext()
    elif cmd == "send_key_encrypted":
        output = lab.s2_send_key_encrypted()

    # ==========================================
    # SCENARIO 3 COMMANDS
    # ==========================================
    elif cmd == "view_cables":
        output = lab.s3_view_cables()
    elif cmd == "verify_cable":
        if len(args) == 2:
            output = lab.s3_verify_cable(args[0].upper(), args[1].lower())
        else:
            output = "Usage: verify_cable <A|B|C> <public_key_reference>"

    # ==========================================
    # SCENARIO 4 COMMANDS
    # ==========================================
    elif cmd == "send_file":
        method = args[0].lower() if len(args) == 1 else ""
        if method in ["symmetric", "asymmetric", "hybrid"]:
            output = lab.s4_send_file(method)
        else:
            output = "Usage: send_file <symmetric|asymmetric|hybrid>"

    # ==========================================
    # UTILITY COMMANDS
    # ==========================================
    elif cmd == "status":
        output = "SCENARIO COMPLETION STATUS:\n\n"
        output += f"1. Leaked S1 Record: {'[COMPLETE]' if lab.scenario_state['s1_completed'] else '[INCOMPLETE]'}\n"
        output += f"2. Embassy Collaborator: {'[COMPLETE]' if lab.scenario_state['s2_completed'] else '[INCOMPLETE]'}\n"
        output += f"3. Ambassador Cables: {'[COMPLETE]' if lab.scenario_state['s3_completed'] else '[INCOMPLETE]'}\n"
        output += f"4. The 1GB ISR Video: {'[COMPLETE]' if lab.scenario_state['s4_completed'] else '[INCOMPLETE]'}\n"

    elif cmd == "help":
        output = crypto_help(args[0] if args else "", active_scenario)

    else:
        output = f"Unknown command: {cmd}\nType 'help' for assistance."

    st.session_state.history3.insert(0, (stripped_input, output))
    st.session_state.input_box = ""


# --- HINT SYSTEM ---
def show_hint(scenario, level):
    """Display hints for each scenario"""
    hints = {
        "s1": {
            1: "Digital signatures prove WHO created a file, but they do NOT provide confidentiality. The text remains readable.",
            2: "The HQ policy explicitly requires Public/Private keys (Asymmetric) to protect SSN data.",
            3: "Because this is just a single, small text record, you don't need a complex hybrid setup. Try: encrypt_record asymmetric",
        },
        "s2": {
            1: "You have an encrypted message and a Symmetric key. If you send that key in plaintext over an unclassified channel, the adversary intercepts it immediately.",
            2: "You must encrypt the Symmetric key itself before sending it. How do you do that without needing another shared secret?",
            3: "Use the collaborator's Public Key to encrypt the Symmetric key. Only their Private Key can decrypt it. Try: send_key_encrypted",
        },
        "s3": {
            1: "Each cable has a signature. You need to verify which signatures mathematically align with the Ambassador's known public key.",
            2: "Only the Ambassador's true private key can create valid signatures that match their public key. The imposter is using a different keypair.",
            3: "You must explicitly declare whose key you are checking against. Try: verify_cable B amb_public_key",
        },
        "s4": {
            1: "You learned in Scenario 1 that Asymmetric encryption works perfectly for tiny payloads. Try it on the 1GB video to see what happens.",
            2: "Symmetric encryption handles the 1GB file instantly, but leaves you with a vulnerable key. Asymmetric encryption secures keys, but cannot handle 1GB files.",
            3: "To securely transmit bulk data, you must combine the speed of Symmetric and the security of Asymmetric. Try: send_file hybrid",
        },
    }

    scenario_hints = hints.get(scenario, {})
    hint_text = scenario_hints.get(level, "No more hints available.")

    hint_key = f"{scenario}_lvl{level}"
    st.session_state.hints_shown[hint_key] = True

    return hint_text


# --- UI LAYOUT ---
st.sidebar.title("Module 3: Cryptography & Identity")
st.sidebar.markdown(
    "**Learning Goal:** Understand when to use symmetric vs asymmetric cryptography in tactical environments."
)

scenario = st.sidebar.radio(
    "Select Scenario",
    [
        "1. The Leaked S1 Record",
        "2. The Embassy Collaborator",
        "3. Forged Ambassador Cables",
        "4. The 1GB ISR Video",
    ],
    key="crypto_scenario",
)
_fire_progress(_SCENARIO_BEACONS.get(scenario, ""))

col_term, col_vis = st.columns([1, 1])

with col_term:
    st.subheader("Terminal")
    # Using on_change instead of a form to mimic a real terminal feel
    st.text_input("Enter Command", key="input_box", on_change=process_command)
    install_terminal_keyboard_shortcuts(
        "Enter Command", TERMINAL_COMMANDS, st.session_state.history3
    )
    st.caption("Type a command and press Enter.")

    render_terminal_history(st.session_state.history3)

with col_vis:
    lab = st.session_state.lab3

    # ==========================================
    # SCENARIO 1: THE LEAKED S1 RECORD
    # ==========================================
    if scenario == "1. The Leaked S1 Record":
        st.markdown("### Scenario 1: The Leaked S1 Record")

        if lab.scenario_state["s1_completed"]:
            st.markdown(
                "<div class='status-complete'>[COMPLETE] SCENARIO COMPLETE</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='status-incomplete'>[IN PROGRESS] Scenario In Progress</div>",
                unsafe_allow_html=True,
            )

        st.markdown(load_lesson("crypto-symasym-s1"))

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="h1_s1"):
                render_hint("HINT 1:", show_hint("s1", 1))
        with col2:
            if st.button("Hint 2", key="h2_s1"):
                render_hint("HINT 2:", show_hint("s1", 2))
        with col3:
            if st.button("Hint 3", key="h3_s1"):
                render_hint("HINT 3:", show_hint("s1", 3))

    # ==========================================
    # SCENARIO 2: THE EMBASSY COLLABORATOR
    # ==========================================
    elif scenario == "2. The Embassy Collaborator":
        st.markdown("### Scenario 2: The Embassy Collaborator")

        if lab.scenario_state["s2_completed"]:
            st.markdown(
                "<div class='status-complete'>[COMPLETE] SCENARIO COMPLETE</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='status-incomplete'>[IN PROGRESS] Scenario In Progress</div>",
                unsafe_allow_html=True,
            )

        st.markdown(load_lesson("crypto-symasym-s2"))

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="h1_s2"):
                render_hint("HINT 1:", show_hint("s2", 1))
        with col2:
            if st.button("Hint 2", key="h2_s2"):
                render_hint("HINT 2:", show_hint("s2", 2))
        with col3:
            if st.button("Hint 3", key="h3_s2"):
                render_hint("HINT 3:", show_hint("s2", 3))

    # ==========================================
    # SCENARIO 3: FORGED AMBASSADOR CABLES
    # ==========================================
    elif scenario == "3. Forged Ambassador Cables":
        st.markdown("### Scenario 3: Forged Ambassador Cables")

        if lab.scenario_state["s3_completed"]:
            st.markdown(
                "<div class='status-complete'>[COMPLETE] SCENARIO COMPLETE</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='status-incomplete'>[IN PROGRESS] Scenario In Progress</div>",
                unsafe_allow_html=True,
            )

        st.markdown(load_lesson("crypto-symasym-s3"))

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="h1_s3"):
                render_hint("HINT 1:", show_hint("s3", 1))
        with col2:
            if st.button("Hint 2", key="h2_s3"):
                render_hint("HINT 2:", show_hint("s3", 2))
        with col3:
            if st.button("Hint 3", key="h3_s3"):
                render_hint("HINT 3:", show_hint("s3", 3))

    # ==========================================
    # SCENARIO 4: THE 1GB ISR VIDEO
    # ==========================================
    elif scenario == "4. The 1GB ISR Video":
        st.markdown("### Scenario 4: The 1GB ISR Video")

        if lab.scenario_state["s4_completed"]:
            st.markdown(
                "<div class='status-complete'>[COMPLETE] SCENARIO COMPLETE</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='status-incomplete'>[IN PROGRESS] Scenario In Progress</div>",
                unsafe_allow_html=True,
            )

        st.markdown(load_lesson("crypto-symasym-s4"))

        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Hint 1", key="h1_s4"):
                render_hint("HINT 1:", show_hint("s4", 1))
        with col2:
            if st.button("Hint 2", key="h2_s4"):
                render_hint("HINT 2:", show_hint("s4", 2))
        with col3:
            if st.button("Hint 3", key="h3_s4"):
                render_hint("HINT 3:", show_hint("s4", 3))


# --- SIDEBAR STATUS ---
st.sidebar.divider()
st.sidebar.markdown("### Overall Progress")
lab = st.session_state.lab3
completed = sum(
    1
    for key in [
        "s1_completed",
        "s2_completed",
        "s3_completed",
        "s4_completed",
    ]
    if lab.scenario_state[key]
)
st.sidebar.progress(completed / 4)
st.sidebar.markdown(f"**{completed}/4 Scenarios Complete**")

if completed == 4:
    st.sidebar.markdown(
        "<div class='success-box'>[ALL SCENARIOS COMPLETE]<br><br>You have successfully applied the correct cryptographic architectures for tactical environments.</div>",
        unsafe_allow_html=True,
    )
