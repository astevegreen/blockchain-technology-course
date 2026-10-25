# Dynamic Labs

Containerized labs, exercises, and quiz engine for the course. A shared nginx router provides a single URL layout across all components:

| Path | Component |
|------|-----------|
| `/` | Course site |
| `/instructor/` | Centralized instructor login |
| `/labs/bitcoin/` | Bitcoin lab |
| `/labs/consensus/` | Consensus lab |
| `/labs/cryptography/` | Cryptography lab |
| `/labs/p2p_trust/` | P2P Trust lab |
| `/labs/ethereum_lab/` | Ethereum lab |
| `/labs/hlf/` | Hyperledger Fabric lab |
| `/exercises/<name>/` | Exercises (trust-game, bgp-game) |
| `/quiz/` | Quiz engine |
| `explorer.<host>` | Course chain explorer (Otterscan), on its own name: `explorer.lab` on the classroom network |

## Prerequisites

- Docker and Docker Compose v2
- Ports 80 (and 443 for TLS) available on the host

## Prebuilt VM Images

The GitHub Actions VM build publishes split release assets instead of one
large download. The release includes:

- `blockchain-lab.qcow2.part-*` for Linux/KVM and as the preferred source
  image for Hyper-V conversion
- `blockchain-lab.ova.part-*` for VirtualBox and VMware import
- `hashes.txt` with SHA-256 hashes for the full artifacts and each split part

### Download and Merge the Parts

Download all parts for the format you want plus `hashes.txt`.

Linux/macOS:

```bash
cat blockchain-lab.qcow2.part-* > blockchain-lab.qcow2
cat blockchain-lab.ova.part-* > blockchain-lab.ova
```

Windows `cmd.exe`:

```bat
copy /b blockchain-lab.qcow2.part-* blockchain-lab.qcow2
copy /b blockchain-lab.ova.part-* blockchain-lab.ova
```

### Validate the Hash

Linux:

```bash
grep '  blockchain-lab.qcow2$' hashes.txt > blockchain-lab.qcow2.sha256
grep '  blockchain-lab.ova$' hashes.txt > blockchain-lab.ova.sha256
sha256sum -c blockchain-lab.qcow2.sha256
sha256sum -c blockchain-lab.ova.sha256
```

macOS:

```bash
shasum -a 256 blockchain-lab.qcow2
shasum -a 256 blockchain-lab.ova
```

Windows PowerShell:

```powershell
Get-FileHash .\blockchain-lab.qcow2 -Algorithm SHA256
Get-FileHash .\blockchain-lab.ova -Algorithm SHA256
```

Compare the reported hash with the matching full-artifact line in
`hashes.txt`. If you want to validate each download chunk before merging,
use the part hashes from the same file.

### Platform-Specific Use

#### Linux / KVM / libvirt

Use the merged `qcow2` directly. In `virt-manager`, create a new VM and
choose `Import existing disk image`, then select `blockchain-lab.qcow2`.

Recommended settings:

- 2 vCPU minimum
- 4 GB RAM minimum, 8 GB preferred
- 60 GB imported virtual disk
- virtio disk and NIC
- BIOS / SeaBIOS / default PC machine type
- NAT for local use, bridged networking if students must reach the VM

If you prefer the CLI, `virt-install --import` works well with the same
disk.

#### VirtualBox

Use the merged `OVA`:

- GUI: `File -> Import Appliance`
- CLI: `VBoxManage import blockchain-lab.ova`

Recommended settings after import:

- type: `Linux / Ubuntu (64-bit)`
- 2 vCPU minimum
- 4 GB RAM minimum, 8 GB preferred
- NAT or bridged networking
- leave EFI disabled unless you rebuilt the image for UEFI

If OVA import complains about metadata, extract it and attach the VMDK
directly:

```bash
tar -xf blockchain-lab.ova
```

Then create a new VM and use `blockchain-lab-disk1.vmdk` as the existing
disk.

#### VMware Workstation / Player / Fusion

Start with the merged `OVA`. If VMware import is unhappy with the OVF
wrapper, extract the OVA and create a VM around the existing VMDK:

```bash
tar -xf blockchain-lab.ova
```

Recommended settings:

- guest OS: `Ubuntu 64-bit`
- 2 vCPU minimum
- 4 GB RAM minimum, 8 GB preferred
- NAT or bridged networking
- legacy BIOS firmware preferred over UEFI

#### Hyper-V

For Hyper-V, do not start from the OVA. The more reliable path is:

1. Merge `blockchain-lab.qcow2.part-*` into `blockchain-lab.qcow2`
2. Validate the QCOW2 hash
3. Convert QCOW2 to VHDX

Example conversion:

```bash
qemu-img convert -p -f qcow2 -O vhdx -o subformat=dynamic blockchain-lab.qcow2 blockchain-lab.vhdx
```

`subformat=dynamic` is optional because it is already QEMU's default for
VHDX, but leaving it in is fine.

Recommended Hyper-V settings:

- Generation 1 VM
- attach the VHDX to `IDE Controller 0`, location `0`
- 2 vCPU minimum
- 4 GB RAM minimum, 8 GB preferred
- use `Default Switch` for simple outbound connectivity, or an external
  switch for LAN access

Notes:

- Generation 2 is not the recommended default for this image
- if you insist on Generation 2, disable Secure Boot or expect boot
  problems
- if you only have the OVA, extract the VMDK first and convert the VMDK,
  not the `.ova` tar archive itself

#### Running on ARM Hardware (Apple Silicon / aarch64)

The VM image is built for x86_64. On ARM hosts (e.g. Apple Silicon Macs),
use QEMU's TCG emulation. Performance will be slower than native KVM but
sufficient for testing and small classes.

```bash
qemu-system-x86_64 \
  -machine q35 \
  -cpu max \
  -accel tcg \
  -m 8G \
  -smp 2 \
  -drive file=blockchain-lab.qcow2,format=qcow2,if=virtio \
  -nic user,hostfwd=tcp::2222-:22 \
  -nographic
```

Then connect via SSH:

```bash
ssh -p 2222 student@localhost
```

To also forward the web UI (port 80) add another `hostfwd` rule to `-nic`:

```
-nic user,hostfwd=tcp::2222-:22,hostfwd=tcp::8080-:80
```

### First Boot Inside the Guest

The image is provisioned with a `student` account:

- username: `student`
- password: `student`

After boot, deploy and start the lab stack from inside the guest:

```bash
cd /opt/dynamic-labs
./lab-manager.sh deploy --mode instructor --no-tls --max-student-capacity 20
./lab-manager.sh start all
```

For a single-user local VM instead of a classroom server:

```bash
cd /opt/dynamic-labs
./lab-manager.sh deploy --mode student --no-tls
./lab-manager.sh start all
```

## Deployment

Pick the section that matches your environment. Each deploys the shared infrastructure (router, course-site, instructor-auth-service, lane-service) and then you start individual labs.

### Cloud (public VM with HTTPS)

For a public-facing VM with Let's Encrypt TLS. Requires a DNS A record pointing to the VM and inbound TCP 80 + 443 open.

```bash
cd dynamic-labs
sudo ./deploy-cloud.sh --domain labs.my-course.com
./lab-manager.sh start all
```

`deploy-cloud.sh` provisions the Let's Encrypt certificate, starts the shared infrastructure with HTTPS, and builds the student images for on-demand labs. `lab-manager.sh start all` then starts every lab. To start only specific labs:

```bash
./lab-manager.sh start bitcoin
./lab-manager.sh start consensus
```

Verify:

```bash
cat .runtime/instructor-credentials.txt
./lab-manager.sh status all
```

`deploy-cloud.sh` saves the domain so that subsequent `lab-manager.sh start` commands preserve the HTTPS configuration automatically.

Cloud deploy accepts the same claim-lane capacity controls as `lab-manager.sh deploy --mode instructor` and forwards them to lab-manager:

- `--max-student-capacity N` sets the base capacity for claim-based labs. Instructor deployments default to 20 and accept values up to 40.
- `--bitcoin-student-capacity N`, `--consensus-student-capacity N`, `--p2p-trust-student-capacity N`, `--ethereum-student-capacity N`, and `--hlf-student-capacity N` override individual lab capacities.
- Example: `sudo ./deploy-cloud.sh --domain labs.my-course.com --max-student-capacity 20 --hlf-student-capacity 10`

Cloud deployment is allowed to hydrate Hyperledger Fabric build assets from the internet during image prebuild. The packaged VM path remains offline-only: it expects the shipped `hlf/runtime/fabric-samples` tree to already contain Fabric samples, binaries, and config.

### Instructor (classroom server)

One machine hosting a full classroom.

- Default claim-lane capacity is `20`; the hard limit is `40`.
- `--max-student-capacity` sets the base lane capacity ceiling for claim-based labs such as `bitcoin`, `consensus`, `p2p_trust`, `ethereum_lab`, and `hlf`.
- Per-lab overrides are available for claim-based labs: `--bitcoin-student-capacity`, `--consensus-student-capacity`, `--p2p-trust-student-capacity`, `--ethereum-student-capacity`, and `--hlf-student-capacity`.

```bash
cd dynamic-labs
./lab-manager.sh deploy --mode instructor --max-student-capacity 20
./lab-manager.sh start bitcoin
```

Add `--no-tls` to skip generating a self-signed certificate.

### Student (local dev / single learner)

One learner on a laptop or VM. The default claim-lane capacity is `5`, which is enough to exercise multi-station flows locally without allocating the full classroom footprint.

```bash
cd dynamic-labs
./lab-manager.sh deploy --mode student --no-tls
./lab-manager.sh start consensus
```

## Managing Labs

After initial deployment, use these commands. The deployment mode is saved in `.lab-manager.env` so you don't need to repeat `deploy`.

```bash
./lab-manager.sh list               # show all managed targets
./lab-manager.sh start bitcoin      # start one lab
./lab-manager.sh start all          # start everything
./lab-manager.sh stop bitcoin       # stop one lab
./lab-manager.sh stop all           # stop everything
./lab-manager.sh status all         # check what's running
```

### Managed targets

| Target | Description |
|--------|-------------|
| `router` | Shared nginx reverse proxy |
| `course-site` | Static course site at `/` |
| `lane-service` | On-demand student container manager |
| `instructor-auth-service` | Centralized instructor login |
| `bitcoin` | Bitcoin lab (ttyd + mempool + explorer) |
| `consensus` | Consensus lab (ttyd) |
| `cryptography` | Cryptography lab (Streamlit) |
| `p2p_trust` | P2P Trust lab (ttyd) |
| `ethereum_lab` | Ethereum lab (Vite SPA + Hardhat) |
| `exercises` | Flask exercises (trust-game, bgp-game) |
| `explorer` | Course chain explorer (Otterscan + Anvil, read only) |
| `quiz-engine-v2` | Quiz engine |
| `hlf` | Hyperledger Fabric lab |

### How student containers work

Labs fall into two categories:

**On-demand lanes** (bitcoin, consensus, p2p_trust, ethereum, hlf): Students claim a session via `/api/<lab>/claim`, and the lab control plane starts a lane-specific container from a pre-built image. `--max-student-capacity` is the base upper bound for how many claimable stations exist at once, and the per-lab capacity flags can override it for individual labs up to the 40-lane limit.

**Shared singleton apps** (cryptography, exercises, explorer, quiz-engine-v2): Students connect to one shared service per lab started directly by `docker compose up`. These labs do not use claims, lanes, or per-student replicas.

That is why lane capacity only applies to the claim-based labs:

- the shared singleton labs boot once and serve the whole class
- the claim-based labs only start those containers on demand or through the warm pool, and their capacity can be tuned independently when needed

## Instructor Credentials

Runtime secrets and instructor credentials are generated on first `deploy` and saved to:

```
.runtime/runtime-secrets.env          # env vars consumed by compose
.runtime/instructor-credentials.txt   # human-readable login reference
```

One login gates all instructor surfaces across labs. To rotate credentials:

```bash
ROTATE_RUNTIME_CREDENTIALS=1 ./lab-manager.sh deploy --mode instructor --max-student-capacity 20
```

The same file holds the Hyperledger Fabric lab's Certificate Authority admin password and CouchDB password
(`HLF_CA_ADMIN_PASSWORD`, `HLF_COUCHDB_PASSWORD`). The lab will not start without them, and a plain redeploy keeps
the ones already saved. The Certificate Authority stores its admin password the first time it starts, so after a
rotation also run `hlf/lab.sh reset` to make it use the new one.

## WiFi Access Point (instructor mode)

Turn a wireless interface into a classroom hotspot. Requires `sudo`, `hostapd`, and `dnsmasq`.

```bash
sudo ./lab-manager.sh deploy \
  --mode instructor \
  --wifi-bridge wlan0 \
  --wifi-ssid CourseLabs \
  --wifi-passphrase YOUR_PASSPHRASE
```

Replace `YOUR_PASSPHRASE` with your own passphrase of 8 to 63 characters; do not reuse an example value.

Add `--uplink-iface eth0` to enable NAT for internet access through a wired connection.

This configures the classroom-network helper, assigns `10.13.37.1/24` to the WiFi interface, serves DHCP on that subnet, and leaves the router reachable on the gateway IP.

## Ethernet Classroom LAN (instructor mode)

Serve the lab over a dedicated Ethernet NIC so an external AP or router can bridge student devices onto the lab subnet.

```bash
sudo ./lab-manager.sh deploy \
  --mode instructor \
  --ethernet-lan enp2s0
```

Add `--uplink-iface wlan0` or another upstream interface if the classroom LAN should also have outbound NAT.

Default Ethernet LAN settings:
- gateway `10.13.38.1`
- subnet `10.13.38.0/24`
- DHCP pool `10.13.38.50-10.13.38.200`

For the external router use AP or bridge mode with its own DHCP disabled, then connect the VM to one of the router's LAN ports. If the router stays in normal WAN/NAT mode, the VM's DHCP server will not reach student devices behind it.

## Classroom Network Helper

The deploy flow calls [scripts/classroom-network-helper.sh](/home/ben/Code/courseware-builder-pipeline/dynamic-labs/scripts/classroom-network-helper.sh:1) for host-side NIC setup. You can also operate it directly:

```bash
sudo ./scripts/classroom-network-helper.sh status
sudo ./scripts/classroom-network-helper.sh disable
```

Inside the built VM the same helper is also installed on `PATH` as `classroom-network-helper`.
The helper saves its last applied topology and restores it automatically at boot with a systemd unit.

To clear saved WiFi/Ethernet classroom settings from `lab-manager`, redeploy with:

```bash
sudo ./lab-manager.sh deploy --mode instructor --clear-classroom-network
```

The built VM includes both the helper's default stack (`hostapd` + `dnsmasq`) and `dhcpd` (`isc-dhcp-server`) if you need to replace the built-in DHCP behavior manually.

## Working with Compose Directly

You can bypass `lab-manager.sh` and use Docker Compose if you prefer:

```bash
cd bitcoin
docker compose --profile build-only build    # build student image (bitcoin, consensus, p2p_trust)
docker compose up -d                         # start instructor + supporting services
```

The `--profile build-only build` step is only needed for labs where lane-service creates student containers on demand (bitcoin, consensus, p2p_trust). Other labs start all services directly via `docker compose up -d`.

When using compose directly, pass the runtime secrets env file:

```bash
docker compose --env-file ../.runtime/runtime-secrets.env up -d
```
