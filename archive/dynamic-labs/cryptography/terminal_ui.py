import html
import json
import re

import streamlit as st


SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")


def _linkify_hashes(text):
    escaped = html.escape(text)

    def replace_hash(match):
        value = match.group(0)
        return (
            f'<button class="hash-copy" type="button" data-hash="{value}" '
            f'data-tooltip="click to copy">{value}</button>'
        )

    return SHA256_RE.sub(replace_hash, escaped)


def render_terminal_history(history, height=600):
    rows = []
    for command, output in history:
        rows.append(
            "<div class='terminal-entry'>"
            f"<div class='log-cmd'>&gt;&gt; {_linkify_hashes(command)}</div>"
            f"<div class='log-out'>{_linkify_hashes(output)}</div>"
            "</div>"
        )

    if not rows:
        rows.append("<div class='terminal-empty'>Type help to see available commands.</div>")

    body = "\n".join(rows)
    st.iframe(
        f"""
<!doctype html>
<html>
<head>
<style>
html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: "Courier New", monospace;
    font-size: 14px;
}}
.terminal-history {{
    box-sizing: border-box;
    height: {height}px;
    overflow-y: auto;
    padding-right: 6px;
}}
.terminal-entry {{
    border-bottom: 1px solid rgba(49, 51, 63, 0.15);
    padding: 0 0 7px 0;
    margin-bottom: 7px;
}}
.log-cmd {{
    color: #2e86c1;
    font-weight: bold;
    white-space: pre-wrap;
}}
.log-out {{
    color: #333;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}}
.terminal-empty {{
    color: #667085;
    font-family: sans-serif;
    font-size: 13px;
}}
.hash-copy {{
    position: relative;
    display: inline;
    border: 0;
    border-bottom: 1px dotted #0f766e;
    padding: 0 1px;
    margin: 0;
    background: #ecfdf3;
    color: #0f5132;
    font-family: "Courier New", monospace;
    font-size: inherit;
    cursor: pointer;
    overflow-wrap: anywhere;
}}
.hash-copy:hover,
.hash-copy:focus,
.hash-copy.hash-token-valid {{
    background: #d1fae5;
    outline: 1px solid #0f766e;
    outline-offset: 1px;
}}
.hash-copy::after {{
    content: attr(data-tooltip);
    position: absolute;
    left: 50%;
    bottom: calc(100% + 5px);
    transform: translateX(-50%);
    z-index: 20;
    display: none;
    min-width: max-content;
    max-width: 160px;
    padding: 4px 6px;
    border-radius: 4px;
    background: #111827;
    color: white;
    font-family: sans-serif;
    font-size: 11px;
    line-height: 1.2;
    white-space: nowrap;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}}
.hash-copy:hover::after,
.hash-copy:focus::after {{
    display: block;
}}
</style>
</head>
<body>
<div class="terminal-history">{body}</div>
<script>
async function copyText(value) {{
    if (navigator.clipboard && window.isSecureContext) {{
        await navigator.clipboard.writeText(value);
        return;
    }}
    const textArea = document.createElement("textarea");
    textArea.value = value;
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    document.execCommand("copy");
    textArea.remove();
}}

document.addEventListener("click", async (event) => {{
    const button = event.target.closest(".hash-copy");
    if (!button) {{
        return;
    }}

    const hash = button.dataset.hash;
    const builderHandler = window.parent && window.parent.__terminalCommandBuilderHandleToken;
    if (builderHandler && builderHandler({{
        type: "hash",
        value: hash,
        label: "hash " + hash.slice(0, 8) + "..."
    }})) {{
        return;
    }}

    const originalText = button.textContent;
    const originalTooltip = button.dataset.tooltip;
    try {{
        await copyText(hash);
        button.textContent = "copied";
        button.dataset.tooltip = "copied";
    }} catch (err) {{
        button.textContent = "copy failed";
        button.dataset.tooltip = "copy failed";
    }}
    window.setTimeout(() => {{
        button.textContent = originalText;
        button.dataset.tooltip = originalTooltip;
    }}, 900);
}});

function updateHashTokenState() {{
    const canAccept = window.parent && window.parent.__terminalCommandBuilderCanAcceptToken;
    const active = !!(canAccept && canAccept("hash"));
    document.querySelectorAll(".hash-copy").forEach((button) => {{
        button.classList.toggle("hash-token-valid", active);
        button.dataset.tooltip = active ? "click to add hash" : "click to copy";
    }});
}}

updateHashTokenState();
window.setInterval(updateHashTokenState, 350);
</script>
</body>
</html>
""",
        height=height,
    )


def install_terminal_keyboard_shortcuts(input_label, commands, history):
    history_commands = [command for command, _ in history if command]
    payload = {
        "inputLabel": input_label,
        "commands": commands,
        "history": history_commands,
    }
    parent_handler = r"""
(function () {
    if (window.__terminalUxNativeHandlerInstalled) {
        return;
    }
    window.__terminalUxNativeHandlerInstalled = true;

    function setInputValue(input, value) {
        const setter = Object.getOwnPropertyDescriptor(
            HTMLInputElement.prototype,
            "value"
        ).set;
        setter.call(input, value);
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();
        window.setTimeout(() => {
            input.selectionStart = value.length;
            input.selectionEnd = value.length;
        }, 0);
    }

    function commonPrefix(values) {
        if (!values.length) {
            return "";
        }
        let prefix = values[0];
        for (const value of values.slice(1)) {
            while (!value.startsWith(prefix) && prefix) {
                prefix = prefix.slice(0, -1);
            }
        }
        return prefix;
    }

    function completeCommand(input, state) {
        const value = input.value;
        const cursor = input.selectionStart || value.length;
        const beforeCursor = value.slice(0, cursor);
        const parts = beforeCursor.split(/\s+/);
        const commandPrefix = parts[0].toLowerCase();

        if (parts.length > 1 || beforeCursor.includes(" ")) {
            return false;
        }

        const matches = state.commands.filter((command) =>
            command.startsWith(commandPrefix)
        );
        if (!matches.length) {
            return false;
        }

        let nextValue = "";
        if (matches.length === 1) {
            nextValue = matches[0] + " ";
        } else {
            const prefix = commonPrefix(matches);
            nextValue =
                prefix.length > commandPrefix.length ? prefix : matches[0] + " ";
        }
        setInputValue(input, nextValue + value.slice(cursor));
        return true;
    }

    document.addEventListener(
        "keydown",
        (event) => {
            const input =
                event.target && event.target.tagName === "INPUT"
                    ? event.target
                    : document.activeElement;
            if (!input || input.tagName !== "INPUT") {
                return;
            }

            const label = input.getAttribute("aria-label");
            const state = window.__terminalUxStates && window.__terminalUxStates[label];
            if (!state) {
                return;
            }

            if (input.__terminalHistoryIndex === undefined) {
                input.__terminalHistoryIndex = -1;
            }

            if (event.key === "ArrowUp" && state.history.length) {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();
                input.__terminalHistoryIndex = Math.min(
                    input.__terminalHistoryIndex + 1,
                    state.history.length - 1
                );
                setInputValue(input, state.history[input.__terminalHistoryIndex]);
                return;
            }

            if (event.key === "ArrowDown" && state.history.length) {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();
                input.__terminalHistoryIndex = Math.max(
                    input.__terminalHistoryIndex - 1,
                    -1
                );
                setInputValue(
                    input,
                    input.__terminalHistoryIndex === -1
                        ? ""
                        : state.history[input.__terminalHistoryIndex]
                );
                return;
            }

            if (event.key === "Tab" && completeCommand(input, state)) {
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();
            }
        },
        true
    );
})();
"""
    st.iframe(
        f"""
<!doctype html>
<html>
<body>
<script>
(function () {{
    const payload = {json.dumps(payload)};
    const parentHandler = {json.dumps(parent_handler)};
    const parentWindow = window.parent;
    const doc = parentWindow.document;

    function findInput() {{
        try {{
            const inputs = Array.from(doc.querySelectorAll("input"));
            return inputs.find((input) => input.getAttribute("aria-label") === payload.inputLabel);
        }} catch (err) {{
            return null;
        }}
    }}

    function attach() {{
        const input = findInput();
        if (!input) {{
            return false;
        }}

        parentWindow.__terminalUxStates = parentWindow.__terminalUxStates || {{}};
        parentWindow.__terminalUxStates[payload.inputLabel] = payload;
        input.__terminalUxInstalled = true;

        if (!parentWindow.__terminalUxNativeHandlerInstalled) {{
            const script = doc.createElement("script");
            script.textContent = parentHandler;
            doc.documentElement.appendChild(script);
            script.remove();
        }}
        return true;
    }}

    if (!attach()) {{
        let attempts = 0;
        const timer = window.setInterval(() => {{
            attempts += 1;
            if (attach() || attempts > 20) {{
                window.clearInterval(timer);
            }}
        }}, 150);
    }}
}})();
</script>
</body>
</html>
""",
        height=1,
    )


def install_terminal_command_builder(input_label, config):
    payload = {
        "inputLabel": input_label,
        "builderId": config["builder_id"],
        "configKey": config.get("config_key", config["builder_id"]),
        "commands": config["commands"],
        "defaultCommand": config.get("default_command", ""),
    }
    parent_handler = r"""
(function () {
    if (window.__terminalCommandBuilderInstalled) {
        return;
    }
    window.__terminalCommandBuilderInstalled = true;
    window.__terminalCommandBuilders = window.__terminalCommandBuilders || {};

    function cssEscape(value) {
        if (window.CSS && window.CSS.escape) {
            return window.CSS.escape(value);
        }
        return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
    }

    function htmlEscape(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function findInput(builder) {
        const inputs = Array.from(document.querySelectorAll("input"));
        return inputs.find((input) => input.getAttribute("aria-label") === builder.inputLabel);
    }

    function setInputValue(input, value) {
        const setter = Object.getOwnPropertyDescriptor(
            HTMLInputElement.prototype,
            "value"
        ).set;
        setter.call(input, value);
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();
        window.setTimeout(() => {
            input.selectionStart = value.length;
            input.selectionEnd = value.length;
        }, 0);
    }

    function storageKey(builder) {
        return "terminal-command-builder:" + builder.builderId + ":enabled";
    }

    function submissionStorageKey(builder) {
        return "terminal-command-builder:" + builder.builderId + ":submitted";
    }

    function builderEnabled(builder) {
        return window.sessionStorage.getItem(storageKey(builder)) !== "false";
    }

    function setBuilderEnabled(builder, enabled) {
        window.sessionStorage.setItem(storageKey(builder), enabled ? "true" : "false");
        builder.enabled = enabled;
        updateBuilder(builder);
    }

    function markBuilderSubmitted(builder) {
        if (!builder || !builder.activeCommand) {
            return;
        }
        builder.pendingPostSubmitReset = true;
        builder.submittedAt = Date.now();
        window.sessionStorage.setItem(
            submissionStorageKey(builder),
            JSON.stringify({
                command: builder.activeCommand,
                configKey: builder.configKey,
                timestamp: builder.submittedAt
            })
        );
        schedulePostSubmitReset(builder.builderId);
    }

    function markRunButtonSubmitted(event) {
        const builder = activeBuilder();
        if (!builder) {
            return;
        }
        const runButton = event.target.closest("button");
        if (runButton && runButton.textContent.trim() === "Run") {
            markBuilderSubmitted(builder);
        }
    }

    function commandSpec(builder) {
        return builder.commands[builder.activeCommand] || null;
    }

    function activeSlot(builder) {
        const spec = commandSpec(builder);
        if (!spec || builder.activeSlotIndex < 0) {
            return null;
        }
        return spec.slots[builder.activeSlotIndex] || null;
    }

    function slotAccepts(slot, tokenType) {
        return !!(slot && slot.accepts && slot.accepts.indexOf(tokenType) !== -1);
    }

    function currentAcceptedTypes(builder) {
        const slot = activeSlot(builder);
        return slot && slot.accepts ? slot.accepts : [];
    }

    function commandText(builder) {
        if (!builder.activeCommand) {
            return "";
        }
        const spec = commandSpec(builder);
        if (!spec) {
            return builder.activeCommand;
        }
        const values = spec.slots
            .map((slot, index) => builder.slotValues[index] && builder.slotValues[index].value)
            .filter((value) => value !== undefined && value !== null && String(value).length > 0);
        return [builder.activeCommand].concat(values).join(" ");
    }

    function syncInput(builder) {
        const input = findInput(builder);
        if (!input) {
            return;
        }
        setInputValue(input, commandText(builder));
    }

    function ensureCommand(builder, command) {
        if (!builder.commands[command]) {
            return false;
        }
        if (builder.activeCommand !== command) {
            builder.activeCommand = command;
            builder.slotValues = [];
            const slots = builder.commands[command].slots || [];
            builder.activeSlotIndex = slots.length ? 0 : -1;
        }
        return true;
    }

    function selectCommand(builder, command) {
        if (!ensureCommand(builder, command)) {
            return;
        }
        syncInput(builder);
        updateBuilder(builder);
    }

    function moveSlot(builder, delta) {
        const spec = commandSpec(builder);
        if (!spec || !spec.slots.length) {
            return;
        }
        const next = Math.min(
            Math.max(builder.activeSlotIndex + delta, 0),
            spec.slots.length - 1
        );
        builder.activeSlotIndex = next;
        syncInput(builder);
        updateBuilder(builder);
    }

    function clearActiveSlot(builder) {
        const spec = commandSpec(builder);
        if (!spec || builder.activeSlotIndex < 0) {
            builder.activeCommand = "";
            builder.slotValues = [];
            builder.activeSlotIndex = -1;
            syncInput(builder);
            updateBuilder(builder);
            return;
        }
        if (builder.slotValues[builder.activeSlotIndex]) {
            builder.slotValues[builder.activeSlotIndex] = null;
        } else if (builder.activeSlotIndex > 0) {
            builder.activeSlotIndex -= 1;
            builder.slotValues[builder.activeSlotIndex] = null;
        }
        syncInput(builder);
        updateBuilder(builder);
    }

    function tokenForType(element, tokenType) {
        const value = element.getAttribute("data-merkle-token-value-" + tokenType);
        if (value === null) {
            return null;
        }
        return {
            type: tokenType,
            value: value,
            label:
                element.getAttribute("data-merkle-token-label-" + tokenType) ||
                element.textContent.trim() ||
                value
        };
    }

    function applyToken(builder, token) {
        if (!builder || !builder.enabled || !builder.activeCommand) {
            return false;
        }
        const slot = activeSlot(builder);
        if (!slot || !slotAccepts(slot, token.type)) {
            return false;
        }
        builder.slotValues[builder.activeSlotIndex] = {
            value: token.value,
            label: token.label || token.value
        };
        const spec = commandSpec(builder);
        const nextEmpty = spec.slots.findIndex((candidate, index) =>
            index > builder.activeSlotIndex && !builder.slotValues[index]
        );
        if (nextEmpty !== -1) {
            builder.activeSlotIndex = nextEmpty;
        } else if (builder.activeSlotIndex < spec.slots.length - 1) {
            builder.activeSlotIndex += 1;
        }
        syncInput(builder);
        updateBuilder(builder);
        return true;
    }

    function resetSlotsIfInputCleared(builder) {
        const input = findInput(builder);
        const hasSlotValues =
            Array.isArray(builder.slotValues) &&
            builder.slotValues.some((value) => !!value);
        if (!input || input.value.trim() !== "" || !hasSlotValues) {
            return false;
        }
        const spec = commandSpec(builder);
        builder.slotValues = [];
        builder.activeSlotIndex = spec && spec.slots.length ? 0 : -1;
        syncInput(builder);
        updateBuilder(builder);
        return true;
    }

    function clearBuilderSlots(builder) {
        const spec = commandSpec(builder);
        builder.slotValues = [];
        builder.activeSlotIndex = spec && spec.slots.length ? 0 : -1;
        updateBuilder(builder);
    }

    function postSubmitResetStillFresh(builder) {
        return !!(
            builder &&
            builder.pendingPostSubmitReset &&
            builder.submittedAt &&
            Date.now() - builder.submittedAt < 8000
        );
    }

    function finalizePostSubmitReset(builder) {
        if (!postSubmitResetStillFresh(builder)) {
            return true;
        }

        const input = findInput(builder);
        if (!input) {
            return false;
        }

        const hasSlotValues =
            Array.isArray(builder.slotValues) &&
            builder.slotValues.some((value) => !!value);
        if (hasSlotValues) {
            clearBuilderSlots(builder);
        }

        if (input.value.trim() === "") {
            syncInput(builder);
            builder.pendingPostSubmitReset = false;
            updateBuilder(builder);
            return true;
        }

        if (input.value.trim() === commandText(builder).trim()) {
            builder.pendingPostSubmitReset = false;
            updateBuilder(builder);
            return true;
        }

        return false;
    }

    function schedulePostSubmitReset(builderId) {
        let resetAttempts = 0;
        const resetTimer = window.setInterval(() => {
            resetAttempts += 1;
            const builder = window.__terminalCommandBuilders[builderId];
            if (!builder || finalizePostSubmitReset(builder) || resetAttempts >= 80) {
                if (builder) {
                    builder.pendingPostSubmitReset = false;
                    updateBuilder(builder);
                }
                window.clearInterval(resetTimer);
            }
        }, 75);
    }

    function renderSlots(builder, root) {
        const container = root.querySelector("[data-merkle-command-slots]");
        if (!container) {
            return;
        }
        const spec = commandSpec(builder);
        if (!builder.activeCommand || !spec) {
            container.innerHTML = '<span class="merkle-slot-placeholder">Choose a command.</span>';
            return;
        }
        if (!spec.slots.length) {
            container.innerHTML = '<span class="merkle-slot-placeholder">No arguments needed.</span>';
            return;
        }
        container.innerHTML = spec.slots.map((slot, index) => {
            const value = builder.slotValues[index];
            const active = index === builder.activeSlotIndex ? " merkle-slot-active" : "";
            const filled = value ? " merkle-slot-filled" : "";
            const label = value ? value.label : slot.placeholder;
            return '<button type="button" class="merkle-slot' + active + filled + '" '
                + 'data-merkle-slot-index="' + index + '">'
                + '<span class="merkle-slot-name">' + htmlEscape(slot.name) + '</span>'
                + '<span class="merkle-slot-value">' + htmlEscape(label) + '</span>'
                + '</button>';
        }).join("");
    }

    function updateTokenHighlights(builder) {
        const accepted = builder.enabled ? currentAcceptedTypes(builder) : [];
        document.querySelectorAll("[data-merkle-token='true']").forEach((element) => {
            const tokenTypes = (element.getAttribute("data-merkle-token-types") || "")
                .split(/\s+/)
                .filter(Boolean);
            const valid = tokenTypes.some((tokenType) => accepted.indexOf(tokenType) !== -1);
            element.classList.toggle("merkle-token-valid", valid);
        });
    }

    function updateBuilder(builder) {
        const root = document.querySelector(
            "[data-merkle-builder='" + cssEscape(builder.builderId) + "']"
        );
        builder.enabled = builderEnabled(builder);
        if (root) {
            root.classList.toggle("merkle-builder-disabled", !builder.enabled);
            root.querySelectorAll("[data-merkle-command]").forEach((button) => {
                button.classList.toggle(
                    "merkle-command-active",
                    button.getAttribute("data-merkle-command") === builder.activeCommand
                );
            });
            const toggle = root.querySelector("[data-merkle-builder-toggle]");
            if (toggle) {
                toggle.textContent = builder.enabled
                    ? "Disable simplified console"
                    : "Enable simplified console";
                toggle.setAttribute(
                    "aria-pressed",
                    builder.enabled ? "false" : "true"
                );
            }
            renderSlots(builder, root);
        }
        updateTokenHighlights(builder);
    }

    function activeBuilder() {
        return window.__terminalCommandBuilders[window.__terminalCommandBuilderActiveId];
    }

    window.__terminalCommandBuilderRefresh = function (builderId) {
        const builder = window.__terminalCommandBuilders[builderId];
        if (builder) {
            updateBuilder(builder);
        }
    };

    window.__terminalCommandBuilderSyncInput = function (builderId) {
        const builder = window.__terminalCommandBuilders[builderId];
        if (builder) {
            syncInput(builder);
            updateBuilder(builder);
        }
    };

    window.__terminalCommandBuilderResetIfInputCleared = function (builderId) {
        const builder = window.__terminalCommandBuilders[builderId];
        if (builder) {
            resetSlotsIfInputCleared(builder);
        }
    };

    window.__terminalCommandBuilderFinalizePostSubmitReset = function (builderId) {
        const builder = window.__terminalCommandBuilders[builderId];
        if (builder) {
            finalizePostSubmitReset(builder);
        }
    };

    window.__terminalCommandBuilderHandleToken = function (token) {
        const builder = activeBuilder();
        return applyToken(builder, token);
    };

    window.__terminalCommandBuilderCanAcceptToken = function (tokenType) {
        const builder = activeBuilder();
        if (!builder || !builder.enabled) {
            return false;
        }
        return currentAcceptedTypes(builder).indexOf(tokenType) !== -1;
    };

    document.addEventListener("pointerdown", markRunButtonSubmitted, true);

    document.addEventListener("click", (event) => {
        const builder = activeBuilder();
        if (!builder) {
            return;
        }

        const runButton = event.target.closest("button");
        if (runButton && runButton.textContent.trim() === "Run") {
            markBuilderSubmitted(builder);
        }

        const commandButton = event.target.closest("[data-merkle-command]");
        if (commandButton) {
            event.preventDefault();
            selectCommand(builder, commandButton.getAttribute("data-merkle-command"));
            return;
        }

        const slotButton = event.target.closest("[data-merkle-slot-index]");
        if (slotButton) {
            event.preventDefault();
            builder.activeSlotIndex = Number.parseInt(
                slotButton.getAttribute("data-merkle-slot-index"),
                10
            );
            syncInput(builder);
            updateBuilder(builder);
            return;
        }

        const toggle = event.target.closest("[data-merkle-builder-toggle]");
        if (toggle) {
            event.preventDefault();
            setBuilderEnabled(builder, !builder.enabled);
            return;
        }

        const tokenButton = event.target.closest("[data-merkle-token='true']");
        if (tokenButton) {
            const slot = activeSlot(builder);
            if (!slot || !builder.enabled) {
                return;
            }
            const types = (tokenButton.getAttribute("data-merkle-token-types") || "")
                .split(/\s+/)
                .filter(Boolean);
            const tokenType = types.find((type) => slotAccepts(slot, type));
            if (!tokenType) {
                return;
            }
            const token = tokenForType(tokenButton, tokenType);
            if (token && applyToken(builder, token)) {
                event.preventDefault();
            }
        }
    }, true);

    document.addEventListener("keydown", (event) => {
        const builder = activeBuilder();
        if (!builder || !builder.enabled) {
            return;
        }
        const input =
            event.target && event.target.tagName === "INPUT"
                ? event.target
                : document.activeElement;
        if (!input || input.tagName !== "INPUT") {
            return;
        }
        if (input.getAttribute("aria-label") !== builder.inputLabel) {
            return;
        }

        if (event.key === "Enter") {
            markBuilderSubmitted(builder);
            return;
        }

        if (event.key === "ArrowLeft") {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            moveSlot(builder, -1);
            return;
        }
        if (event.key === "ArrowRight") {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            moveSlot(builder, 1);
            return;
        }
        if (event.key === "Backspace") {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            clearActiveSlot(builder);
        }
    }, true);
})();
"""
    st.iframe(
        f"""
<!doctype html>
<html>
<body>
<script>
(function () {{
    const payload = {json.dumps(payload)};
    const parentHandler = {json.dumps(parent_handler)};
    const parentWindow = window.parent;
    const doc = parentWindow.document;

    function install() {{
        if (!parentWindow.__terminalCommandBuilderInstalled) {{
            const script = doc.createElement("script");
            script.textContent = parentHandler;
            doc.documentElement.appendChild(script);
            script.remove();
        }}
        parentWindow.__terminalCommandBuilders = parentWindow.__terminalCommandBuilders || {{}};
        const previous = parentWindow.__terminalCommandBuilders[payload.builderId] || {{}};
        const submissionKey = "terminal-command-builder:" + payload.builderId + ":submitted";
        let submittedCommand = null;
        try {{
            const submittedPayload = JSON.parse(
                parentWindow.sessionStorage.getItem(submissionKey) || "null"
            );
            parentWindow.sessionStorage.removeItem(submissionKey);
            if (
                submittedPayload &&
                submittedPayload.configKey === payload.configKey &&
                payload.commands[submittedPayload.command]
            ) {{
                submittedCommand = submittedPayload.command;
            }}
        }} catch (err) {{
            parentWindow.sessionStorage.removeItem(submissionKey);
        }}
        const previousConfigStillValid = previous.configKey === payload.configKey;
        const previousCommandStillValid =
            previousConfigStillValid && !!payload.commands[previous.activeCommand];
        const commandInput = Array.from(doc.querySelectorAll("input")).find(
            (input) => input.getAttribute("aria-label") === payload.inputLabel
        );
        const inputWasClearedAfterSubmit =
            previousCommandStillValid &&
            commandInput &&
            commandInput.value.trim() === "" &&
            Array.isArray(previous.slotValues) &&
            previous.slotValues.some((value) => !!value);
        const resetCommand = submittedCommand || (
            inputWasClearedAfterSubmit ? previous.activeCommand : null
        );
        const previousPostSubmitStillFresh = !!(
            previous.pendingPostSubmitReset &&
            previous.submittedAt &&
            Date.now() - previous.submittedAt < 8000
        );
        const pendingPostSubmitReset = !!resetCommand || previousPostSubmitStillFresh;
        const shouldSyncInput =
            pendingPostSubmitReset || (!!previous.activeCommand && !previousCommandStillValid);
        const activeCommand = resetCommand
            ? resetCommand
            : previousCommandStillValid
            ? previous.activeCommand
            : payload.defaultCommand || "";
        const activeSlots =
            activeCommand && payload.commands[activeCommand]
                ? payload.commands[activeCommand].slots || []
                : [];
        const previousSlotIndex = previousCommandStillValid && Number.isInteger(previous.activeSlotIndex)
            ? previous.activeSlotIndex
            : activeSlots.length
                ? 0
                : -1;
        const activeSlotIndex = resetCommand
            ? activeSlots.length
                ? 0
                : -1
            : Math.min(previousSlotIndex, activeSlots.length - 1);
        parentWindow.__terminalCommandBuilders[payload.builderId] = {{
            builderId: payload.builderId,
            configKey: payload.configKey,
            inputLabel: payload.inputLabel,
            commands: payload.commands,
            activeCommand: activeCommand,
            activeSlotIndex: activeSlotIndex,
            slotValues: resetCommand
                ? []
                : activeCommand === previous.activeCommand
                    ? previous.slotValues || []
                    : [],
            enabled: true,
            pendingPostSubmitReset: pendingPostSubmitReset,
            submittedAt: pendingPostSubmitReset
                ? previous.submittedAt || Date.now()
                : null
        }};
        parentWindow.__terminalCommandBuilderActiveId = payload.builderId;
        if (
            parentWindow.__terminalCommandBuilderRefresh &&
            parentWindow.__terminalCommandBuilders[payload.builderId]
        ) {{
            parentWindow.__terminalCommandBuilderRefresh(payload.builderId);
        }}
        if (shouldSyncInput && parentWindow.__terminalCommandBuilderSyncInput) {{
            parentWindow.__terminalCommandBuilderSyncInput(payload.builderId);
        }}
        if (
            pendingPostSubmitReset &&
            parentWindow.__terminalCommandBuilderFinalizePostSubmitReset
        ) {{
            parentWindow.__terminalCommandBuilderFinalizePostSubmitReset(payload.builderId);
        }}
        if (parentWindow.__terminalCommandBuilderResetIfInputCleared) {{
            let resetAttempts = 0;
            const resetTimer = parentWindow.setInterval(() => {{
                resetAttempts += 1;
                parentWindow.__terminalCommandBuilderResetIfInputCleared(payload.builderId);
                if (parentWindow.__terminalCommandBuilderFinalizePostSubmitReset) {{
                    parentWindow.__terminalCommandBuilderFinalizePostSubmitReset(payload.builderId);
                }}
                if (resetAttempts >= 30) {{
                    parentWindow.clearInterval(resetTimer);
                }}
            }}, 100);
        }}
    }}

    install();
    window.setTimeout(install, 100);
    window.setTimeout(install, 400);
}})();
</script>
</body>
</html>
""",
        height=1,
    )


def render_hint(title, text):
    safe_title = html.escape(title)
    safe_text = html.escape(text)
    st.markdown(
        f"<div class='hint-box'><div class='hint-title'>{safe_title}</div>{safe_text}</div>",
        unsafe_allow_html=True,
    )
