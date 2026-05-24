#!/usr/bin/env python3
"""Generate student overlay artifacts for the 4-org hybrid classroom.

Produces (into --out, defaulting to this file's directory):

  configtx-4org-students.yaml   # 4-org + Meridian + configured student orgs
                                # members. Endorsement stays OutOf(3, Org1..4).
  compose-students.yaml         # Configured profile-gated student peer services that
                                # join the existing fabric_test network.
  crypto-config-student01.yaml  # (pre-existing) — unchanged, produced for
                                # completeness if missing.
  ... crypto-config-studentNN.yaml

The generator is deliberately a pure stdlib script so it can run inside the
lab.sh bootstrap flow without extra deps.

Run:
  python3 managed_runtime/generate_student_overlay.py --out managed_runtime
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from textwrap import dedent

STUDENT_COUNT = int(
    os.environ.get("HLF_STUDENT_COUNT")
    or os.environ.get("MAX_STUDENT_CAPACITY")
    or os.environ.get("STUDENT_COUNT")
    or "20"
)
FABRIC_VERSION = "2.5.15"


def _default_hlf_platform() -> str:
    arch = os.uname().machine.lower()
    if arch == "x86_64":
        return "linux/amd64"
    if arch in ("aarch64", "arm64"):
        return "linux/arm64"
    return "linux/amd64"


STUDENT_PIDS_LIMIT = max(
    0,
    int(os.environ.get("HLF_STUDENT_PIDS_LIMIT") or os.environ.get("STUDENT_PIDS_LIMIT") or "256"),
) or None
HLF_STUDENT_DISK_ROOT = (os.environ.get("HLF_STUDENT_DISK_ROOT") or "").strip()
HLF_PLATFORM = (
    os.environ.get("HLF_PLATFORM")
    or os.environ.get("PLATFORM")
    or _default_hlf_platform()
).strip()

HERE = Path(__file__).resolve().parent
HOST_HLF_DIR = Path(os.environ.get("HLF_HOST_HLF_DIR") or HERE.parent).resolve()
HOST_HLF_SCRIPTS_DIR = HOST_HLF_DIR / "scripts"


def student_id(n: int) -> str:
    return f"s{n:02d}"


def student_msp(n: int) -> str:
    return f"Student{n:02d}MSP"


def student_domain(n: int) -> str:
    return f"student{n:02d}.example.com"


def student_anchor(n: int) -> str:
    return f"Student{n:02d}"


# -- configtx -----------------------------------------------------------------


def student_org_block(n: int) -> str:
    """One Organizations: entry for a student org. Channel member (Readers,
    Writers, Endorsement wired), but the channel-level Application
    Endorsement policy in the 4-org profile excludes students from the
    signer set so chaincode transactions do not route endorsements to
    student peers."""
    msp = student_msp(n)
    return (
        f"\n"
        f"  - &{student_anchor(n)}\n"
        f"    Name: {msp}\n"
        f"    ID: {msp}\n"
        f"    MSPDir: ../organizations/peerOrganizations/{student_domain(n)}/msp\n"
        f"    Policies:\n"
        f"      Readers:\n"
        f"        Type: Signature\n"
        f"        Rule: \"OR('{msp}.admin', '{msp}.peer', '{msp}.client')\"\n"
        f"      Writers:\n"
        f"        Type: Signature\n"
        f"        Rule: \"OR('{msp}.admin', '{msp}.client')\"\n"
        f"      Admins:\n"
        f"        Type: Signature\n"
        f"        Rule: \"OR('{msp}.admin')\"\n"
        f"      Endorsement:\n"
        f"        Type: Signature\n"
        f"        Rule: \"OR('{msp}.peer')\"\n"
    )


def render_configtx_4org_students(base_configtx_path: Path) -> str:
    """Read configtx-4org.yaml, append student org blocks + profile refs.

    The 4-org file has a stable shape: Organizations section ending with
    Org5 (Meridian), then Capabilities/Application/etc., then
    Profiles.ChannelUsingRaft.Application.Organizations listing
    *Org1..*Org5. We insert student blocks after *Org5 in the
    Organizations section and append *Student01..*StudentNN refs to the
    profile's Organizations list.
    """
    text = base_configtx_path.read_text()

    # 1. Insert student Organizations after Org5 block. The Org5 block
    # ends with its Endorsement rule line; then a blank line precedes
    # Capabilities: at column 0.
    students_section = "".join(student_org_block(n) for n in range(1, STUDENT_COUNT + 1))
    org5_end_marker = "    Rule: \"OR('Org5MSP.peer')\"\n"
    if org5_end_marker not in text:
        raise RuntimeError("Could not locate Org5 Endorsement marker in configtx-4org.yaml")
    text = text.replace(
        org5_end_marker,
        org5_end_marker + students_section,
        1,
    )

    # 2. Append student refs to ChannelUsingRaft Application.Organizations.
    # The 4-org profile ends its Organizations list with `- *Org5` at
    # indent 8. Append students at the same indent, before "Capabilities:
    # *ApplicationCapabilities" which is at indent 6.
    profile_org5_marker = "        - *Org5\n"
    if profile_org5_marker not in text:
        raise RuntimeError(
            "Could not locate profile Organizations *Org5 marker in configtx-4org.yaml"
        )
    profile_student_refs = "".join(
        f"        - *{student_anchor(n)}\n" for n in range(1, STUDENT_COUNT + 1)
    )
    text = text.replace(
        profile_org5_marker,
        profile_org5_marker + profile_student_refs,
        1,
    )

    header = (
        "# Auto-generated by managed_runtime/generate_student_overlay.py\n"
        f"# Extends configtx-4org.yaml with Student01..{STUDENT_COUNT:02d} as channel members.\n"
        "# Endorsement and LifecycleEndorsement remain OutOf(3, Org1..4);\n"
        "# students are channel members (Readers/Writers) but not endorsers.\n"
    )
    # Preserve original file's leading `---` separator if present.
    return header + text


# -- compose ------------------------------------------------------------------


def render_student_peer_service(n: int) -> str:
    container = f"peer0.{student_domain(n)}"
    msp = student_msp(n)
    profile = student_id(n)
    sid = student_id(n)
    domain = student_domain(n)
    env = [
        "FABRIC_CFG_PATH=/etc/hyperledger/peercfg",
        "FABRIC_LOGGING_SPEC=INFO",
        "CORE_PEER_TLS_ENABLED=true",
        "CORE_PEER_PROFILE_ENABLED=false",
        "CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt",
        "CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key",
        "CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt",
        f"CORE_PEER_ID={container}",
        f"CORE_PEER_ADDRESS={container}:7051",
        "CORE_PEER_LISTENADDRESS=0.0.0.0:7051",
        f"CORE_PEER_CHAINCODEADDRESS={container}:7052",
        "CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:7052",
        f"CORE_PEER_GOSSIP_BOOTSTRAP={container}:7051",
        f"CORE_PEER_GOSSIP_EXTERNALENDPOINT={container}:7051",
        f"CORE_PEER_LOCALMSPID={msp}",
        "CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp",
        f"CORE_OPERATIONS_LISTENADDRESS={container}:9444",
        "CORE_METRICS_PROVIDER=prometheus",
        f'CHAINCODE_AS_A_SERVICE_BUILDER_CONFIG={{"peername":"{container}"}}',
        "CORE_CHAINCODE_EXECUTETIMEOUT=300s",
        # Per-peer ttyd shell identity
        "HLF_NODE_TYPE=student",
        f"HLF_STUDENT_ID={sid}",
        f"HLF_MSP_ID={msp}",
        f"HLF_ORG_DOMAIN={domain}",
        f"HLF_PEER_ADDRESS={container}:7051",
        "HLF_HOME_DIR=/home/student",
        f"HLF_PROMPT={sid}",
        f"HLF_TITLE={container}",
        f"HLF_ADMIN_USER=Admin@{domain}",
    ]
    if HLF_STUDENT_DISK_ROOT:
        student_mounts = [
            f"      - {HLF_STUDENT_DISK_ROOT}/{sid}/home:/home/student",
            f"      - {HLF_STUDENT_DISK_ROOT}/{sid}/production:/var/hyperledger/production",
        ]
    else:
        student_mounts = [
            f"      - {container}-home:/home/student",
            f"      - {container}:/var/hyperledger/production",
        ]
    lines = [
        f"  {container}:",
        f"    platform: {HLF_PLATFORM}",
        f"    container_name: {container}",
        "    image: hlf-peer-ttyd:latest",
        "    pull_policy: never",
        "    labels:",
        "      service: hyperledger-fabric",
        "    profiles:",
        f"      - {profile}",
        "    environment:",
    ]
    lines += [f"      - {e}" for e in env]
    lines += [
        "    volumes:",
        f"      - ../organizations/peerOrganizations/{domain}/peers/{container}:/etc/hyperledger/fabric:ro",
        "      - ./docker/peercfg:/etc/hyperledger/peercfg:ro",
        *student_mounts,
        "      - ../organizations:/opt/hlf-orgs:ro",
        "      - ../channel-artifacts:/opt/hlf-channel:ro",
        f"      - {HOST_HLF_SCRIPTS_DIR}:/opt/hlf-scripts:ro",
    ]
    if STUDENT_PIDS_LIMIT is not None:
        lines += [
            f"    pids_limit: {STUDENT_PIDS_LIMIT}",
        ]
    lines += [
        "    security_opt:",
        "      - no-new-privileges:true",
        "    cap_drop:",
        "      - ALL",
        "    cap_add:",
        "      - CHOWN",
        "      - NET_BIND_SERVICE",
        "      - SETUID",
        "      - SETGID",
        "    read_only: true",
        "    tmpfs:",
        "      - /tmp:size=64m,mode=1777",
        "      - /run:size=16m",
        '    command: ["bash", "/opt/hlf-scripts/hlf_ttyd_wrapper.sh", "peer", "node", "start"]',
        "    working_dir: /home/student",
        "    networks:",
        "      - test",
        "      - student-term",
    ]
    return "\n".join(lines) + "\n"


def render_compose_students() -> str:
    out: list[str] = []
    out.append(
        "# Auto-generated by managed_runtime/generate_student_overlay.py\n"
        f"# Student overlay compose: {STUDENT_COUNT} profile-gated student peers that\n"
        "# join the existing fabric_test network created by the 4-org\n"
        "# consortium bootstrap. Orderer + consortium + Meridian are\n"
        "# defined in compose-test-net.yaml and are not duplicated here.\n"
        "\n"
    )
    if not HLF_STUDENT_DISK_ROOT:
        out.append("volumes:\n")
        for n in range(1, STUDENT_COUNT + 1):
            out.append(f"  peer0.{student_domain(n)}:\n")
            out.append(f"  peer0.{student_domain(n)}-home:\n")
        out.append("\n")
    # External network — the 4-org bootstrap creates fabric_test, so we
    # reference it rather than redefining (docker compose would otherwise
    # try to create a second copy with a different label).
    out.append(
        "networks:\n"
        "  test:\n"
        "    name: fabric_test\n"
        "    external: true\n"
        "  student-term:\n"
        "    name: hlf-student-term\n"
        "    external: true\n"
        "\n"
    )
    out.append("services:\n\n")
    for n in range(1, STUDENT_COUNT + 1):
        out.append(render_student_peer_service(n))
        out.append("\n")
    return "".join(out)


# -- crypto-config ------------------------------------------------------------


def render_student_crypto(n: int) -> str:
    return dedent(
        f"""\
        # Auto-generated by managed_runtime/generate_student_overlay.py
        # Student overlay org {student_id(n)} ({student_msp(n)}).
        PeerOrgs:
          - Name: Student{n:02d}
            Domain: {student_domain(n)}
            EnableNodeOUs: true
            Template:
              Count: 1
              SANS:
                - localhost
            Users:
              Count: 1
        """
    )


# -- main ---------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(HERE),
        help="Directory to write generated files into (default: alongside this script)",
    )
    parser.add_argument(
        "--base-configtx",
        default=str(HERE / "configtx-4org.yaml"),
        help="Path to the base 4-org configtx.yaml to extend",
    )
    args = parser.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base = Path(args.base_configtx).resolve()
    if not base.exists():
        print(f"error: base configtx not found: {base}")
        return 1

    (out_dir / "configtx-4org-students.yaml").write_text(
        render_configtx_4org_students(base)
    )
    (out_dir / "compose-students.yaml").write_text(render_compose_students())

    # Ensure crypto-config-studentNN.yaml exist. Pre-existing files are
    # overwritten with the canonical template so drift can't sneak in.
    for n in range(1, STUDENT_COUNT + 1):
        (out_dir / f"crypto-config-student{n:02d}.yaml").write_text(
            render_student_crypto(n)
        )

    print(f"wrote: {out_dir}/configtx-4org-students.yaml")
    print(f"wrote: {out_dir}/compose-students.yaml")
    print(f"wrote: {out_dir}/crypto-config-student01..{STUDENT_COUNT:02d}.yaml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
