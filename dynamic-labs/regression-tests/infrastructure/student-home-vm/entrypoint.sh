#!/bin/sh
set -eu

ensure_loop_devices() {
    local n dev loop_min loop_max

    loop_min="${STUDENT_HOME_VM_LOOP_MIN:-19}"
    loop_max="${STUDENT_HOME_VM_LOOP_MAX:-63}"

    for n in $(seq "${loop_min}" "${loop_max}"); do
        dev="/dev/loop${n}"
        if losetup "${dev}" >/dev/null 2>&1; then
            continue
        fi
        rm -f "${dev}"
        mknod -m 0660 "${dev}" b 7 "${n}"
        chown root:disk "${dev}" || true
    done
}

sync_workspace() {
    mkdir -p /workspace
    rm -rf /workspace/dynamic-labs/.runtime \
           /workspace/dynamic-labs/lane-service/runtime \
           /workspace/dynamic-labs/hlf/runtime
    rsync -a --delete \
        --exclude '.git/' \
        --exclude '.runtime/' \
        --exclude 'dynamic-labs/.runtime/' \
        --exclude 'dynamic-labs/lane-service/runtime/' \
        --exclude 'dynamic-labs/hlf/runtime/' \
        --exclude '**/__pycache__/' \
        /src/ /workspace/
    chown -R student:student /workspace || true
}

ensure_loop_devices
sync_workspace

if [ ! -S /var/run/docker.sock ]; then
    dockerd-entrypoint.sh >/var/log/dockerd.log 2>&1 &
fi

tries=0
until docker info >/dev/null 2>&1; do
    tries=$((tries + 1))
    if [ "${tries}" -ge 60 ]; then
        echo "Nested Docker daemon did not become ready." >&2
        if [ -f /var/log/dockerd.log ]; then
            tail -100 /var/log/dockerd.log >&2 || true
        fi
        exit 1
    fi
    sleep 1
done

exec "$@"
