# Dynamic Labs

Containerized labs, exercises, and quiz engine for the course. A shared nginx router provides a single URL layout across all components:

| Path | Component |
|------|-----------|
| `/` | Course site |
| `/instructor/` | Centralized instructor login |
| `/labs/bitcoin/` | Bitcoin lab |
| `/labs/consensus/` | Consensus lab |
| `/labs/cryptography/` | Cryptography lab |
| `/labs/hlf/` | Hyperledger Fabric lab |
| `/exercises/<name>/` | Exercises (trust-game, bgp-game) |
| `/labs/explorer/` | Explorer lab (redirects to its own host, `explorer.<host>`; reached by IP address, to port 8441) |
| `/labs/tokens/` | Token lab (redirects to its own host, `tokens.<host>`; by IP address, to port 8442) |
| `/labs/dex/` | Exchange and bridge lab (redirects to `dex.<host>`, its L1 chain; its L2 chain is `dex-l2.<host>`; by IP address, ports 8443 and 8444) |
| `/labs/wallet/` | Wallet lab (worksheet, wallet page, saved pages; the explorer at `/labs/wallet/mempool/`) |
| `/labs/bitcoin-trace/` | Day-6 Bitcoin trace lab (worksheet, saved pages; the explorer at `/labs/bitcoin-trace/mempool/`) |
| `/labs/coinjoin-trace/` | Day-7 CoinJoin trace lab (worksheet, saved pages; the explorer at `/labs/coinjoin-trace/mempool/`) |
| `/labs/hide-and-trace/` | Days 6-7 team game "Hide and trace" (team page at `/labs/hide-and-trace/game/`, instructor page at `/labs/hide-and-trace/game/instructor/`, the explorer at `/labs/hide-and-trace/mempool/`) |
| `/labs/tron/` | Tron lab (worksheet, query page, saved results) |
| `/labs/cross-chain/` | Day-8 cross-chain lab (worksheet, query page, saved results) |
| `/labs/final-trace/` | Day-10 final trace (worksheet, Tron query page, saved pages; the explorer at `/labs/final-trace/mempool/`) |
| `/quiz/` | Quiz engine |

## Choosing how to run the labs

- **A class:** one shared host per class, the cloud by default and the classroom server as the offline fallback
  (see "Deployment" below).
- **A student's own computer:** the student launcher, the default for self-study (owner, 11 Nov 2026): one double-click that runs the labs in Docker Desktop. See
  [`student-launcher/README.md`](../student-launcher/README.md), the student guide `blockchain-course/run-labs.qmd`
  and the owner decisions in [`docs/student-launcher-spec.md`](../docs/student-launcher-spec.md).
- **Practice and self-study offline, in a VM:** the prebuilt VM image below, kept as the offline option.

## Prerequisites

- Docker and Docker Compose v2
- Ports 80 (and 443 for TLS) available on the host, and 8441-8444 for the explorer, token and exchange labs when
  students reach the site by IP address

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

For a public-facing VM with Let's Encrypt TLS. Requires inbound TCP 80 and 443 open (and 8441-8444 if students will
use the VM's IP address instead of its name), and five DNS A records pointing to the VM's public IPv4 address:

| Name | Type | Value |
|------|------|-------|
| `labs.my-course.com` (your `--domain`) | A | the VM's public IPv4 address |
| `explorer.labs.my-course.com` | A | the same address |
| `tokens.labs.my-course.com` | A | the same address |
| `dex.labs.my-course.com` | A | the same address |
| `dex-l2.labs.my-course.com` | A | the same address |

The explorer, token and exchange labs each answer on their own host name, so `deploy-cloud.sh` requests one
certificate covering all five names. Creating the records is up to whoever deploys, at their DNS provider; the script
cannot do it. Before it calls certbot it checks that each name resolves to this host, and if one does not, it prints
the records to create and stops. Remove any AAAA record for these names unless it also points at the VM. If the VM's
public address is detected wrongly (the check asks `api.ipify.org`), set `PUBLIC_IP=<address>` before running it.

No other inbound port needs to be open for the class (SSH aside, for whoever runs the VM): every lab container other
than the router publishes its ports on 127.0.0.1 only (`tests/test_host_ports_contract.py` holds them to it;
`docs/security-triage.md`, C9, says why).

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

The certificate lasts 90 days and renews itself with no downtime. On a cloud host the router sends plain HTTP to
HTTPS except Let's Encrypt's challenge path, `/.well-known/acme-challenge/`, which it serves from
`/var/www/course-labs-acme` (`router/https-redirect/on.conf`). `deploy-cloud.sh` gets the certificate with
`certbot --webroot` into that folder: through the running router when the labs are up, or through a stand-in nginx
on port 80 on the first deploy. certbot's timer (`certbot.timer`, or a cron entry in `/etc/cron.d/course-labs-certbot`
where there is none) renews it the same way within 30 days of expiry, and the deploy hook
`/etc/letsencrypt/renewal-hooks/deploy/course-labs-router.sh` runs `scripts/cloud-cert-deploy-hook.sh`, which copies
the new certificate to `/etc/course-labs/router-certs` (where the router reads it) and reloads the router. Rerunning
`deploy-cloud.sh` works with the labs up or down. Check renewal on the host with `sudo certbot renew --dry-run`. A
host first deployed before 9 Nov 2026 got its certificate with `--standalone`: rerun `sudo ./deploy-cloud.sh` once to
switch it to the webroot (the router stops for about a minute while certbot runs).

A cloud host is on the open internet, so `deploy-cloud.sh` turns the class gate on: students enter the class code
before any lab page ([Class Code](#class-code-student-gate)). `--no-class-gate` leaves the labs open to anyone who
finds the host.

Cloud deploy accepts the same claim-lane capacity controls as `lab-manager.sh deploy --mode instructor` and forwards them to lab-manager:

- `--max-student-capacity N` sets the base capacity for claim-based labs. Instructor deployments default to 20 and accept values up to 40.
- `--bitcoin-student-capacity N`, `--consensus-student-capacity N` and `--hlf-student-capacity N` override individual lab capacities.
- Example: `sudo ./deploy-cloud.sh --domain labs.my-course.com --max-student-capacity 20 --hlf-student-capacity 10`

#### Host size for a class (local estimate, 9 Nov 2026)

Measured on the course desktop (Docker Desktop, 20 CPUs, 15.6 GiB), not on a cloud host, with
`scripts/measure-seats.py`: a fresh classroom deploy, ten lanes of each claim-based lab started through the
instructor API, and `docker stats` read after a 45-second settle. The seats were idle (a student reading or typing),
so CPU is a floor, not a peak. The Ethereum and P2P Trust labs and the Chain Graph (`bitcoin-graph`) were archived on 11 Nov 2026
(`archive/dynamic-labs/` in the course repository); their rows and shares below are kept as measured.

| What | RAM | CPU |
|------|----:|------------------------:|
| Every lab started (`start all`), no student lanes: 56 containers | 5.0 GiB | 1.8 cores a minute after the start, 1 of them `bitcoin-graph` |
| One Fabric (hlf) seat: its student peer | 85 MiB | 1.2% of a core idle, 1.5% starting |
| One Bitcoin seat | 77 MiB | 0.6% of a core idle, 1.1% starting |
| One Ethereum seat | 37 MiB | 0.1% of a core idle |
| One consensus or P2P trust seat | 17 MiB | under 0.1% of a core |

A seat with all five lanes open costs about 0.23 GiB, so 20 seats add about 4.6 GiB and 40 seats about 9.1 GiB to
the 5 GiB the labs need on their own. In a class only the day's lab is busy: lanes stop after 20 minutes idle (60 for
Bitcoin), and each lane-service lane is capped at 512 MiB. The images took about 35 GB of disk on the desktop (test images included).

A whole class acting at once (measured the same day on the same desktop with `--burst`, every seat starting its task
at the same moment):

| Burst (as of 9 Nov 2026) | Seats | Each seat's wait | CPU while it ran |
|------|----:|------------------------:|------------------------:|
| Bitcoin: fund a fresh wallet to 50 BTC with LAB2's `mine-until`, one shared ClassNet chain | 20 | 23 s to 94 s, median 47 s | peak 5.5 cores, mean 1.6 |
| Fabric (hlf): five `invoke create` transactions from the seat's own peer | 40 | 14 s to 16 s | peak 8.3 cores, mean 3.7 |
| Ethereum: five contract-builder compiles of SimpleStorage | 40 | 4 s to 6 s | peak 15.4 cores, mean 7.7 |

The 20 Bitcoin wallets took turns at ClassNet's easy blocks: 87 blocks in all, the hardest at difficulty 0.0024, so
no student waited past about a minute and a half. All 40 Fabric peers started and every invoke succeeded; idle, a
Fabric seat used 102 MiB at 40 seats. Only the compile burst passed 16 cores, for a few seconds: on a 16-vCPU host
it takes a few seconds longer, nothing fails. Bitcoin was not run at 40 seats.

Recommended host, which these bursts fit:

- **20 seats:** 8 vCPU, 16 GiB RAM, 100 GB SSD.
- **40 seats:** 16 vCPU, 32 GiB RAM, 150 GB SSD.

Before the first class on a new host, rerun the measurement there: deploy with `--max-student-capacity` at least the
seat count, `lab-manager.sh start` the three lane labs, then
`python3 scripts/measure-seats.py --seats 20 bitcoin consensus hlf`, and the class bursts
with `python3 scripts/measure-seats.py --seats 40 --burst bitcoin hlf`. On a cloud host add
`--base-url https://<your domain>` to each: the router redirects plain `http://127.0.0.1` to HTTPS.
The full list of checks that wait for the real host, the real domain and the first real class is
`docs/before-first-class.md` in the course repository (instructors have it there; it is not part of this download).

Cloud deployment is allowed to hydrate Hyperledger Fabric build assets from the internet during image prebuild. The packaged VM path remains offline-only: it expects the shipped `hlf/runtime/fabric-samples` tree to already contain Fabric samples, binaries, and config.

### Instructor (classroom server)

One machine hosting a full classroom.

- Default claim-lane capacity is `20`; the hard limit is `40`.
- `--max-student-capacity` sets the base lane capacity ceiling for claim-based labs such as `bitcoin`, `consensus`, and `hlf`.
- Per-lab overrides are available for claim-based labs: `--bitcoin-student-capacity`, `--consensus-student-capacity`, and `--hlf-student-capacity`.

```bash
cd dynamic-labs
./lab-manager.sh deploy --mode instructor --max-student-capacity 20
./lab-manager.sh start bitcoin
```

Add `--no-tls` to skip generating a self-signed certificate. Add `--class-gate` when students outside the room could
reach the server: they then enter the class code first ([Class Code](#class-code-student-gate)).

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

`start` reuses images already built. The `course-site` image bakes in the rendered lessons, so after the lessons or
lab links change, run `./lab-manager.sh build-images course-site` and then start it again (`build-images` always
rebuilds, from cached layers where nothing changed). Start does not rebuild it on its own because a classroom
machine may be offline, and the build downloads Quarto.

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
| `exercises` | Flask exercises (trust-game, bgp-game) |
| `explorer` | Day-1 explorer lab (Otterscan on a frozen course chain); `explorer/README.md` |
| `wallet` | Day-2 wallet lab (wallet page and mempool on a frozen Bitcoin chain); `wallet/README.md` |
| `bitcoin-trace` | Day-6 Bitcoin trace lab (mempool on a frozen Bitcoin chain: a ransom, a peel chain, a service); `bitcoin-trace/README.md` |
| `coinjoin-trace` | Day-7 CoinJoin trace lab (mempool on a frozen Bitcoin chain: CoinJoin rounds, two planted leaks, a mixer); `coinjoin-trace/README.md` |
| `hide-and-trace` | Days 6-7 team game (one live Bitcoin chain and mempool for the class: teams hide 2.1 BTC, then trace another team's; a block every 30 s); `hide-and-trace/README.md` |
| `tokens` | Day-3 token lab (Otterscan on a frozen chain with a proxied dollar token and an NFT); `tokens/README.md` |
| `dex` | Day-4 exchange and bridge lab (Otterscan on two frozen chains: a pool swap on L1, a bridge to L2); `dex/README.md` |
| `tron` | Day-5 and day-9 Tron labs (query page over frozen Tron snapshots); `tron/README.md` |
| `cross-chain` | Day-8 cross-chain lab (query page over a frozen Ethereum, Arbitrum and Bitcoin snapshot); `cross-chain/README.md` |
| `final-trace` | Day-10 final trace (mempool on a frozen Bitcoin chain and a query page over an invented Tron snapshot: one unguided case); `final-trace/README.md` |
| `quiz-engine-v2` | Quiz engine |
| `hlf` | Hyperledger Fabric lab |

### How student containers work

Labs fall into two categories:

**On-demand lanes** (bitcoin, consensus, hlf): Students claim a session via `/api/<lab>/claim`, and the lab control plane starts a lane-specific container from a pre-built image. `--max-student-capacity` is the base upper bound for how many claimable stations exist at once, and the per-lab capacity flags can override it for individual labs up to the 40-lane limit.

**Shared singleton apps** (cryptography, exercises, explorer, wallet, bitcoin-trace, coinjoin-trace, hide-and-trace, tokens, dex, tron, cross-chain, final-trace, quiz-engine-v2): Students connect to one shared service per lab started directly by `docker compose up`. These labs do not use claims, lanes, or per-student replicas.

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

## Class Code (student gate)

One code per class keeps strangers off a class host. It is on for a cloud deploy (`deploy-cloud.sh`; opt out with
`--no-class-gate`), on for a classroom server deployed with `lab-manager.sh deploy --mode instructor --class-gate`,
and off otherwise. The student VM (`--mode student`) refuses `--class-gate`: it serves one student.

- **Where the code is.** `.runtime/instructor-credentials.txt` ("Class Code"), generated with the other credentials
  (eight letters and digits, without 0, O, 1, I or L), and the Class Code panel of the instructor portal
  (`/instructor/`), where the instructor can type a new code or make one up. `ROTATE_RUNTIME_CREDENTIALS=1` makes a
  new one; a plain redeploy keeps it.
- **What students see.** Any page on the server, or on the explorer, tokens, dex and dex-l2 hosts, first sends them to
  `/class/`. The right code gives that browser a signed class pass for two weeks, then returns them to the page they
  asked for. The pass is set on the course domain, so one entry covers all five host names; on an IP address it
  covers that address's ports (8441-8444).
- **Changing the code** voids every pass issued for the old one: everyone enters the new code. A redeploy that
  rotates the code wins over a code changed in the portal before it.
- **Instructors** pass with their instructor login; the code page, the instructor pages and the instructor sign-in
  stay open. On a cloud host the instructor login is set on the main host only, so on the explorer, tokens, dex and
  dex-l2 hosts the instructor enters the class code like a student.
- **Wrong codes** are limited per address (20 a minute, 100 in 15 minutes, in each of the service's two workers),
  loose enough for a class behind one address and far too slow to guess a code.

How it works: the router asks the instructor auth service about each request
(`router/routes/_class_gate.conf`, switched by `router/class-gate/on.conf` or `off.conf`), and the lane-service
checks `/claim` and `/resolve` itself, since those use their own router check. The code and pass are in
`instructor_auth_service/class_gate.py`. Tests: `tests/test_class_gate.py` (the service: no pass, valid pass, voided
pass, instructor login, wrong-code limit), `tests/test_lane_service_class_gate.py` (claim and resolve) and
`tests/test_class_gate_deploy.py` (deploy flags and router wiring).

The instructor sign-in's rate limit counts attempts by the address the router saw, the last `X-Forwarded-For`
entry, not the first one, which a client can write itself.

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

The deploy flow calls [scripts/classroom-network-helper.sh](scripts/classroom-network-helper.sh) for host-side NIC setup. You can also operate it directly:

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
docker compose --profile build-only build    # build student image (bitcoin, consensus)
docker compose up -d                         # start instructor + supporting services
```

The `--profile build-only build` step is only needed for labs where lane-service creates student containers on demand (bitcoin, consensus). Other labs start all services directly via `docker compose up -d`.

When using compose directly, pass the runtime secrets env file:

```bash
docker compose --env-file ../.runtime/runtime-secrets.env up -d
```
