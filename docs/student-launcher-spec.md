# Student lab launcher: spec

Written 9 Nov 2026 for an orchestration session that starts child sessions to build it.
Paths are repo-relative, and `dl/` means `dynamic-labs/`. The facts in section 2 were read on 9 Nov at `520189c`.

## 1. Goal

The owner said: "I will share this course with other people who are not tech-savvy and might not have access to an LLM that can explain to them how to get everything up and running... one-button functionality... we will continue to iterate on the course lessons and labs going forward, so a feature like this would need to adapt to that."

Lessons stay on the GitHub Pages site, and nothing about them changes. This spec covers only the Docker labs on a student's own computer.

**Done means:**
- A student with nothing but Docker Desktop downloads one zip from a GitHub Release and double-clicks `Start Course Labs`.
- A local control page opens in their browser. It lists every student-facing lab, and each lab downloads the first time they press Start on it.
- When a lab is added, changed or removed in the repo, the next release carries the change. The student's next launch picks it up, with no edit to the launcher and nothing for the student to do.
- The instructor, cloud and VM paths (`lab-manager.sh`, `deploy-cloud.sh`, `vm-build/`) keep working unchanged.

## 2. Owner decisions (9 Nov 2026, in this session)

| Question | Answer |
|---|---|
| Visibility | "Visibility is fine public". Images and releases are public. |
| Docker Desktop licensing | "Docker doesn't matter for my audience" |
| Which labs, and how | All student-facing labs, downloaded **on demand** per lab from the control page |
| Quiz and instructor parts | **Hidden** in local mode. No quiz or instructor links; the quiz banks stay instructor-only. |
| Image namespace | `ghcr.io/astevegreen/...`, pushed by CI with its built-in `GITHUB_TOKEN`. No personal access token. |
| Signing | **Unsigned.** The student guide shows the one-time Windows SmartScreen and macOS Gatekeeper click-through with pictures. |

## 3. Facts that shape the design

**No lab registry.** Labs are hard-coded in four places, and the router's upstream names are fixed:
- The four places are `target_dir()` and `list_targets()` in `dl/lab-manager.sh:701-755`, the routes in `dl/router/routes.conf` and `dl/router/routes/*.conf`, and the landing links in `dl/course-site/inject_dynamic_links.py:7-37`.
- The router upstreams are hard-coded container names such as `wallet-gateway-1` and `explorer-otterscan-1`, so compose project names must not change.

**The stack is bash and a host Docker socket, not plain compose:**
- `lab-manager.sh` is 1483 lines of bash. It creates about 16 external networks (`ensure_networks`, `:645`) and writes secrets with python into `dl/.runtime/runtime-secrets.env` (`dl/runtime-credentials.sh:57-72`).
- Compose files use `${VAR:?...}`, so a missing secret fails the start (for example `dl/lane-service/docker-compose.yml:51`).

**Two services start containers through the Docker socket:**
- `lane-service` (`dl/lane-service/docker-compose.yml:56`) bind-mounts `../bitcoin`, `../bitcoin-forensics` and `../cryptography` from the repo.
- `hlf-runner` uses a same-path mount, `${PWD}:${PWD}` (`dl/hlf/docker-compose.yml:44,53-56`).
- Many labs bind-mount repo files: chain data, gateway code, and the explorer gateway, which dex and tokens share (`dl/dex/docker-compose.yml:69-74`).

**Most images are built on the machine:**
- Most lab images use `build:` and are built locally.
- Only the three Bitcoin base images were on ghcr, in another organization's registry, pushed by hand. (Since 9 Nov 2026 `student-release.yml` builds them from this repo into `ghcr.io/astevegreen/course-labs:base-bitcoin-*`, and every lab pulls them from there.)
- No workflow pushes images or uses buildx.
- The Dockerfiles already pick amd64 or arm64 by `TARGETARCH`. The hlf build-only services default to `linux/amd64` (`dl/hlf/docker-compose.yml:67,78,90`).

**Routing:**
- `http://localhost/` relies on `*.localhost` subdomains (explorer, tokens, dex, dex-l2).
- An IP host instead gets the ports 8441-8444 (`dl/router/routes.conf`). Safari's handling of `*.localhost` is unverified.

**Releases and tests:**
- Only `vm-build.yml` creates releases: `latest-vm-*`, marked as prereleases.
- `lab-tests.yml` runs `run.sh --fresh-start` per lab, and `run-lab.sh:70` has `--skip-start`.
- `tools/lab_images.py` already lists the images that labs pull from a registry.

**What students may receive:** everything under `blockchain-course/` and `dl/`, except the `-x` exclusions in `pages.yml` and the removals in `vm-build.yml` (`CLAUDE.md`, "Hard rules"). Student images must honour the same exclusions.

## 4. Design

### 4.1 One manifest per lab: the source of truth

Every lab directory with a compose file gets a `lab.yaml`, validated by `dl/lab.schema.json`. Adding a lab means adding a folder with a `lab.yaml`, and removing one means deleting the folder. Nothing else lists labs by hand.

Minimum fields:
- `id`: stable, and matching the folder name.
- `title`.
- `order`: day and position.
- `compose_project`: the existing pinned name.
- `student_local`: `true` or `false`.
- `services`: each with its image source (built here or upstream) and its platforms.
- `uses_lane_service`.
- `entry_url`: the path or port the control page links to.
- `memory_mb`.
- `approx_download_mb`.
- `data`: anything that today comes from a bind mount.
- `keep_volumes_on_update`: whether student work survives an update.

**Generated from the manifests**, with "generated files change only by running their script" (CLAUDE.md):
- The landing links that `inject_dynamic_links.py` produces.
- The target lists in `lab-manager.sh`.
- The image list for the release pipeline.
- The control page's lab list.

The router's nginx config stays hand-written. Each manifest names its route files, and the check fails when a route file is missing or orphaned.

**New `tools/check.py` rules.** These are rails: they tighten, and get the rail second look.
- Every compose directory has a valid `lab.yaml`.
- The generated lists match the manifests.
- A `student_local` lab's student compose file has no host bind mounts and no `build:`.

### 4.2 Self-contained student images

The launcher drives Docker from inside a container (4.3), so any bind mount would resolve on the student's host, where the repo does not exist. Each `student_local` lab therefore gets a `docker-compose.student.yml` next to its main file. Note that `dl/ethereum_lab/docker-compose.student.yml` already exists with another purpose; Phase 0 picks a non-clashing name.

In that file:
- Every image is prebuilt and referenced by digest, through a variable the launcher fills in.
- Repo files the lab used to bind-mount are baked into the image with `COPY`, or seeded into a named volume.
- Secrets come from the launcher's env file.
- Capacity is 1 student.

The main compose file and its instructor behaviour are not touched.

`lane-service` needs the same treatment in student mode: no host paths for the lane containers it spawns. `hlf-runner`'s same-path mount must go too, replaced by a named volume or by baking.

### 4.3 The launcher

**Wrapper scripts** (`student-launcher/`):
- `Start Course Labs.cmd` for Windows and `Start Course Labs.command` for macOS. A `.sh` for Linux is optional.
- About 30 lines each, and expected never to change. They:
  1. Check that Docker is installed and running, and start Docker Desktop if needed. If Docker is missing, they open the guide page.
  2. Run `docker pull ghcr.io/astevegreen/course-labs:launcher-stable`.
  3. Run it detached with the host Docker socket, a named state volume, and the control-page port published on 127.0.0.1.
  4. Open the browser.
- `Stop Course Labs` does the reverse.

**Control container** (Python, like `lane-service`; the image includes the docker CLI and the compose plugin):
- It holds the release's manifest and all the student compose files, baked in. One pull gives a consistent snapshot of a release.
- It ports what student mode needs from `lab-manager.sh`:
  - Create the external networks.
  - Write the secrets env file into the state volume. Every `:?` variable must be covered.
  - Start shared services in order (router, course-site, lane-service as needed), then the labs on demand.
- The control page, served from it:
  - Each lab shows its title, size, memory, state, and a Start / Stop / Open / Reset button.
  - Download progress.
  - An "Update available" notice.
  - Plain-language errors, such as "Port 80 is busy", "Docker has 4 GB but this lab needs 6 GB", or "No internet".
- **On every launch it reconciles** what is installed (found by a compose label such as `course.lab=<id>`) against its manifest:
  - **Removed lab:** run `compose down`, remove its volumes, offer to free its images.
  - **Changed lab:** the digest differs, so pull on the next Start, keeping volumes when `keep_volumes_on_update` is set.
  - **New lab:** appears on the page.
- Local mode uses a router overlay that drops the `/quiz/`, `/instructor/` and `/api/instructor` routes. The landing links are generated without them.

### 4.4 Release pipeline (`.github/workflows/student-release.yml`, manual dispatch)

1. Read the manifests and build every `student_local` service with buildx for `linux/amd64` and `linux/arm64`. A service the manifest marks amd64-only stays amd64, and the control page says "not available on this Mac" for it.
2. Push everything to **one** ghcr package, `ghcr.io/astevegreen/course-labs`, tagged `<lab>-<service>-<version>`. The launcher is `launcher-<version>`.
   - Why one package: new ghcr packages appear to start private, and visibility can only be changed in the web UI (verify this). One package means the owner makes it public once, ever, and new labs never need that click again.
3. Build the launcher image with the manifest, the image digests and the student compose files baked in. Also write `latest.json` (the same manifest with digests) for people to read.
4. Create a **draft** release `student-v<yyyy.mm.dd>-<run>` with the zipped wrapper scripts and `latest.json`.
5. Run the smoke test (4.5). Only when it is green, publish the release as a non-prerelease and move `launcher-stable` to the new version.
   - The VM releases stay prereleases, so GitHub's "latest release" link always points at the student launcher.
6. Apply the student-exclusion list from `pages.yml` and `vm-build.yml` to the image build contexts. Move that list into one shared file that all three read, so the three cannot drift.
7. Rebuild the Bitcoin base images here too (trixie). Once they are pushed, switch every reference to the old registry's `bitcoin-*` images repo-wide to the new package, in the same change.

A dispatch input `publish: false` stops at the draft. The first public release is the owner's call ("publishing to students" is an owner gate).

### 4.5 Smoke test

**Runners.** CI jobs on `ubuntu-24.04` and `ubuntu-24.04-arm` run the launcher image exactly as the wrapper does. Then they call its API to start each lab, using a matrix grouped as `tools/lab_tests.py` groups them.

**Checks.**
- Run the existing per-lab suites against the running stack with `run-lab.sh --skip-start`. Make that flag work if it doesn't.
- Use a fixture lab (`dl/regression-tests/fixtures/hello-lab/`, `student_local`, excluded from real releases) to prove three things:
  - Add: a new folder appears on the page with no launcher edit.
  - Remove: an installed lab that leaves the manifest is cleaned up.
  - Change: a new digest is pulled.

**Wrapper scripts.** Lint them (shellcheck, PSScriptAnalyzer), and give them a `--dry-run` mode tested with a fake `docker`.

**What CI cannot run.** CI cannot run Docker Desktop on Windows or macOS. Those get a manual test (Phase 3) and stay "unverified" until done.

## 5. Not in scope

- Hosting lessons differently.
- Code signing.
- A student quiz bank.
- Changing the instructor, cloud or VM flows.
- Auto-installing Docker Desktop.
- Cutting the image sizes. If that comes up, it goes to `docs/follow-ups.md`.

## 6. Technical questions Phase 0 settles (an architect decision, not the owner's)

1. **Control-page port, and port 80 being busy.** Should the router's host port be configurable with a fallback?
2. **Which URLs to open.** `*.localhost` or IP plus ports 8441-8444, so that it works in Chrome, Edge, Firefox and Safari. The IP-and-ports route is preferred unless Safari is verified.
3. **Socket path.** The socket mount on Windows (`//var/run/docker.sock`) and on macOS (whether the default socket is on in Docker Desktop).
4. **Baking or seeding.** Bake data into images, or seed named volumes, for each bind mount listed in section 3. This includes the 68 MB LFS forensics snapshot: offer forensics labs 3-5 locally or not. Note that student-facing content is the owner's call, so if it is unclear, ask in the Decisions batch.
5. **lane-service in student mode.** Capacity 1, no home disks (tmpfs), and how the bitcoin compose it spawns gets its files without host paths.
6. **HLF.** Its arm64 status, and its replacement for the same-path mount. If it can't be done cleanly, mark it `student_local: false` for now and add a follow-up.
7. **The student compose file name** (see 4.2), the manifest schema, and the control container's HTTP API.

Phase 0 writes the answers to `docs/student-launcher-design.md` and commits the schema. Every child builds against that contract.

## 7. Orchestration plan

**Orchestrator: Opus at medium effort.**
- A session can't start a child on a pricier model or a higher effort than its own, and the user-level hook requires `model` and `effort` on every `start_session`.
- The orchestrator starts the children, reviews each merge, and runs integration.
- It never takes on a child's files itself. It works from the root folder or a course worktree.

**Rules for every child:**
- Its own worktree and branch (`use_worktree: true`). It touches only the files its row in the table below owns.
- Course `CLAUDE.md` applies in full: the commit format with `Requested:`, `python tools/check.py`, the reviewer and second look for rails, and Lab Tests for `dl/` changes.
- **No local Docker.** Children never run `--fresh-start` or any `docker` command on the owner's PC, because it wipes every lab's containers.
- Lab verification goes through `gh workflow run lab-tests.yml --ref <branch> -f labs=<ids>`, then `gh run watch`.
- When green, rebase onto `main`, push `HEAD:main`, and message the orchestrator with the sha and the run link.
- Shared files: only the owning session edits them. Others send the change to the orchestrator.
  - `tools/check.py` and `tools/lab_tests.py`: owned by S1 and S5 respectively.
  - `pages.yml` and `vm-build.yml`: S5.
  - `docs/follow-ups.md`: append-only.
- gh and git run as astevegreen (the bot account is suspended). This is not a sprint: use no sprint queue or comment machinery.

**Phase 0** (the orchestrator itself): answer section 6, then commit `docs/student-launcher-design.md`, `dl/lab.schema.json` and the API sketch.

**Phase 1** (after Phase 0 is on `main`): six children at once.

| Session | Model, effort | Owns | Delivers |
|---|---|---|---|
| S1 Manifests | Sonnet medium | `dl/*/lab.yaml`, `tools/lab_manifest.py`, new rules in `tools/check.py`, `inject_dynamic_links.py`, the target lists in `lab-manager.sh` | A manifest for every lab, the generators, the check rules and their tests |
| S2 Plain labs | Opus medium | Student compose files and Dockerfile changes for explorer, tokens, dex, exercises, tron, cross-chain, wallet, bitcoin-trace, coinjoin-trace and final-trace | Self-contained student compose files, Lab Tests green on the branch |
| S3 Lane labs | Opus medium | `dl/lane-service/`, plus bitcoin, bitcoin-graph, bitcoin-forensics, consensus, p2p_trust, cryptography and ethereum_lab | lane-service student mode with no host paths, and those labs' student compose files |
| S4 HLF | Opus medium | `dl/hlf/` | A student compose file without the same-path mount and with arm64 settled, or `student_local: false` plus a follow-up |
| S5 Release | Opus medium | `.github/workflows/student-release.yml`, `pages.yml`, `vm-build.yml`, `tools/lab_tests.py`, the shared exclusion list, the ghcr reference switch | Sections 4.4 and 4.5 except the launcher internals, with a dry-run draft release |
| S6 Launcher | Opus medium | `student-launcher/` (wrappers, control container, control page), the local router overlay, the hello-lab fixture | Section 4.3, unit tests, and wrapper dry-run tests |

**Merge order.**
- S1 first. Others rebase onto it, and S2, S3 and S4 add their manifest fields after it lands.
- S5's ghcr reference switch goes only after its first image push succeeds.
- The orchestrator reads every child's diff before the child pushes to main. A child messages it with "ready" and waits for "go".

**Phase 2** (after S5 and S6 land): S7 Student guide, Sonnet medium. It adds a short "Run the labs on your computer" page to `blockchain-course/` and the guide that the wrapper opens. Each covers installing Docker Desktop, the SmartScreen and Gatekeeper click-through, and what each button does, with screenshots from the dry run. This is new site content, so it gets the reviewer and the second look.

**Phase 3** (the orchestrator, serialized):
1. Dispatch `student-release.yml` with `publish: false` and get both smoke jobs green.
2. Ask the owner before using Docker on their PC. Check `docker ps` for other lab containers first.
3. Run the wrapper from the draft release on the owner's Windows PC and start at least one lab from each of S2, S3 and S4.
4. A Mac test needs a Mac. Without one, record "macOS unverified".

**Phase 4** (the owner):
1. Make the `course-labs` package public once.
2. Run the release with `publish: true`, or tell the orchestrator to.
3. Add the release link to the course site.

## 8. Acceptance checks

1. On a clean Windows 11 PC with only Docker Desktop: download the zip, double-click, the control page opens, and a lab from each family starts and works.
2. Smoke jobs green on amd64 and arm64, including the add, remove and change fixture checks.
3. `python tools/check.py --all` green on `main`. Lab Tests green for every lab, which shows the instructor path is unchanged.
4. Deleting a lab folder, or adding one with a `lab.yaml`, needs no edit outside that folder, apart from its router route file.
5. No instructor-only file appears in any student image. The shared exclusion list is tested the way `tools/tests/test_src_zip.py` tests `src.zip`.

## 9. Risks

- **Download size.** Otterscan is about 4 GB and the mempool image about 2.4 GB. On-demand download and the sizes shown on the control page soften this.
- **Docker Desktop memory.** The default allocation may be below what a lab needs. The control page checks `docker info` and says how to raise it.
- **HLF.** It may not suit local mode. Section 6, item 6 allows dropping it.
- **ghcr visibility.** Visibility of new packages is the one manual owner step. Using a single package keeps it to one click.
