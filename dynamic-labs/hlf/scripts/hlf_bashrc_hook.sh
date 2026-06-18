# HLF lab shell bootstrap
if [ -z "${HLF_SHELL_RC_SOURCED:-}" ] && [ -r /tmp/hlf-shell-rc ]; then
    export HLF_SHELL_RC_SOURCED=1
    . /tmp/hlf-shell-rc
fi
