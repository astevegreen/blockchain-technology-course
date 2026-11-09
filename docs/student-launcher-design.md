# Student lab launcher: Phase 0 design

The contract every Phase 1 child builds against. It answers section 6 of `docs/student-launcher-spec.md` and fixes
the names, the manifest and the control API. Written 9 Nov 2026 from `a5f809a`. `dl/` means `dynamic-labs/`.
Where this departs from the spec, it says so and why. The spec still governs everything this file doesn't change.

## 1. Owner decision added in Phase 0

| Question | Answer (9 Nov 2026) |
|---|---|
| Bitcoin forensics labs 3-5 locally | **Offered.** The control page gets a "Load the forensics chain" button on the Bitcoin lab that does what the instructor's deploy does today. |

The snapshot is already in what students receive: `pages.yml` and `vm-build.yml` keep `forensics-lab-v3-instructor-dir`
and exclude only the answer files, seeders and notes. Baking it into a student image therefore matches rule 1.

## 2. Answers to the spec's section 6

**1. Ports.**
- The control page listens on `127.0.0.1:8470` and is always on, so it can explain a failure on the other ports.
- In local mode the router binds `127.0.0.1` only (`HOST_BIND`) and serves HTTP only (`NGINX_CONF=nginx-http.conf`,
  no certificates, no TLS port). `http://127.0.0.1` is a secure context, so browser crypto APIs still work.
- `HTTP_PORT` tries 80 and falls back to 8480. `8441-8444` stay fixed, because the explorer redirect at
  `routes.conf:169-185` sends the browser to `$host:844x`, so the host port must equal the container port. When one of
  them is busy, the control page marks explorer, tokens and dex as blocked and names the port.

**2. URLs.** Every link uses `http://127.0.0.1[:port]/...`, never `*.localhost`. The router already redirects an IP host
to the 8441-8444 ports. Safari's resolution of `*.localhost` subdomains depends on the macOS version (WebKit bug 160504,
read 9 Nov 2026), so the IP route is the only one that works in every browser.

**3. Docker socket.** The wrapper runs the control container with `-v /var/run/docker.sock:/var/run/docker.sock`.
- The same string is used on Windows `.cmd`, where cmd.exe does no path conversion, and on macOS.
- Docker Desktop resolves that path inside its own VM, so the macOS setting "Allow the default Docker socket to be used"
  (it adds a host symlink) is not needed. This is to be proved by the Phase 3 manual test.
- Enhanced Container Isolation, a Docker Business admin setting, blocks socket mounts. The control page and the guide
  name it when `docker run` fails with that error.
- The control container's compose calls are the only Docker client. Lab compose files must never pass a host path,
  which section 4 enforces.

**4. Bake, not seed.** Every bind-mounted repo file is small: the chain folders are 7 MB at most, the static folders
under 1 MB, and the rest are config files. They are baked with `COPY` into thin per-lab images, for example
`FROM nginx:alpine` plus the gateway config and static files. Student work already lives in named volumes and stays
there. Named seeded volumes are not used, because baked data updates with the image digest and needs no reconcile step.
- The forensics snapshot (about 58 MB of LFS `.dat` files) is baked into the lane-service student image at
  `/app/bitcoin-forensics/forensics-lab-v3-instructor-dir`. The release workflow checks out with `lfs: true`, like
  `vm-build.yml:21`. S5 fails the build if a `.dat` file is an LFS pointer.

**5. lane-service in student mode.** S3 builds a `LANE_MODE=student-local` setting in the lane-service image:
- Capacity is 1 lane per lab. Students skip the class code and claim screen and go straight to their lane.
- No `*_STUDENT_HOME_ROOT`, so no host home disks. Homes are the container's own filesystem or a named volume per lab.
- The repo trees it reads today through `../bitcoin`, `../bitcoin-forensics` and `../cryptography` are baked into the
  image at the same container paths.
- The bitcoin compose file it drives becomes `bitcoin/docker-compose.launcher.yml`, which uses images only and no
  build contexts.
- Lane images (bitcoin-lab-student, the consensus, p2p_trust and crypto students, ethereum-trainer) come from env vars
  holding the release digests, never from local `build-only` builds.
- The forensics button calls a new `POST /api/local/bitcoin/forensics-load` on lane-service. It reuses
  `labs/bitcoin.py`'s load path and exists only in student-local mode.

**6. HLF.**
- arm64 is settled: Fabric peer 2.5.15 and CA 1.5.17 publish amd64 and arm64 manifests (`docker manifest inspect`,
  9 Nov 2026). The launcher compose drops the `platform:` pins.
- The same-path mount is the hard part. S4 replaces `${PWD}:${PWD}` with one named volume, `hlf-runtime`, mounted at
  a fixed path. The Fabric binaries (305 MB) are baked into the runner image instead of downloaded at start.
- Every host path `lab.sh` and `lanes.py` hand to Docker becomes that volume, using compose's `volume.subpath`
  (S4 confirms the minimum Docker Desktop version it needs) for `../organizations` and `../channel-artifacts`.
- If that can't be done cleanly within S4, HLF ships `student_local: false` with a follow-up, as the spec allows.
- Also noted for S4: the committed `hlf/managed_runtime/compose-students.yaml` hardcodes `platform: linux/arm64`. It
  is generated from `HLF_PLATFORM`, so the launcher must regenerate it, never ship the committed copy.

**7. Names.**
- The student compose file is **`docker-compose.launcher.yml`**. It doesn't clash with `ethereum_lab`'s existing
  `docker-compose.student.yml` or `docker-compose.fullstack-local.yml`, and it says who reads it.
- The manifest is `lab.yaml`, validated by `dl/lab.schema.json` (section 3). The control API is in section 5.

## 3. Manifests

- **Where.** One `lab.yaml` per top-level `dl/` folder holding a compose file. Today that is 21 folders: the 21 ids
  `lab-manager.sh:701-755` lists. The folders without one are `shared`, `scripts`, `docs`, `tests`,
  `regression-tests`, `bitcoin-graph` (built by bitcoin) and `bitcoin-forensics` (read by lane-service).
- **Ids and kinds.**
  - `id` is the folder name (`instructor_auth_service`, `quiz-engine-v2`). The `lab-manager.sh` aliases stay.
  - `kind` is `lab`, `shared` (router, lane-service, course-site), `instructor` (quiz-engine-v2,
    instructor_auth_service) or `fixture`.
  - Instructor kinds are `student_local: false`.
- **Validation.** `tools/lab_manifest.py` validates manifests itself; the `jsonschema` package isn't installed and
  isn't added. It enforces two rules the schema can't express: `student_compose_file` is required when
  `student_local` is true, and `id` equals the folder name.
- **Generated from the manifests**, with checked-in outputs and `--write`:
  - the `BLOCK` in `course-site/inject_dynamic_links.py`;
  - `target_dir`, `list_targets` and the `ensure_networks` list in `lab-manager.sh`, between marker comments;
  - `dl/student-release-images.json` for S5. The launcher reads the manifests directly.
- **Router.** The nginx config stays hand-written. S1 moves each lab's inline locations from `routes.conf` into
  `routes/<id>.conf`, in the same order and with unchanged behaviour, then includes them by name. The instructor and
  quiz locations move into `routes/_instructor.conf` and `routes/quiz-engine-v2.conf`, which lets local mode replace
  them (section 4). The check fails when a manifest names a missing route file, a `routes/*.conf` file has no owner,
  or `routes.conf` doesn't include an owned file. Shared files starting with `_` and the `*-host.conf` files are owned
  by the router manifest.
- **New check rules** (rails: they get the second look and the rail audit):
  1. Every compose folder has a valid `lab.yaml`.
  2. The generated outputs match the manifests.
  3. A `student_local` launcher compose file has no host bind mounts (only named volumes or tmpfs), no `build:`, and
     every image is `${VAR}` with VAR from the manifest.
  4. Route ownership, as above.

## 4. Local mode

- **No course-site locally.** The lessons are on Pages, and the course-site image is a whole Quarto render, a large
  download for nothing.
  - The local router overlay sends `location /` to the control container, which is on `router-net` as
    `course-launcher`.
  - `http://127.0.0.1/` and `http://127.0.0.1:8470/` both show the control page.
  - This replaces the spec's "landing links generated without them" (4.3): there is no landing page locally.
- **The overlay.** It is `router/docker-compose.launcher.yml`, an override like `docker-compose.cloud.yml`. It sets
  `HOST_BIND`, `HTTP_PORT` and `NGINX_CONF`, and mounts `routes/local/staff-pages-off.conf` over
  `routes/_instructor.conf` and `routes/local/quiz-off.conf` over `routes/quiz-engine-v2.conf`. Both return 404. Other
  routes need no change, because the router resolves upstreams lazily (`resolver 127.0.0.11`, `routes.conf:1-2`).
  `CLASS_GATE` is off.
- **Secrets.** The control container generates every variable `runtime-credentials.sh` writes, with the same
  generators, into `/state/runtime-secrets.env` on its state volume, and passes it with `--env-file`. A unit test
  parses every launcher compose file for `${X:?}` and fails if the generator misses one. No instructor-credentials
  file is written.
- **Networks.** At start, the control container creates the union of every manifest's `networks` (the router joins
  them all), then starts the router, then lane-service if any lab needs it.
- **Labels.** Every launcher compose service carries `course.lab=<id>` and `course.release=<version>`, and
  reconciliation (spec 4.3) reads them. Project names stay `compose_project`, so a classroom stack and a local stack on
  one machine would collide. The control page refuses to start and says so when it finds containers without the
  `course.release` label.

## 5. Control container HTTP API

The page is static HTML and JS served by the same process, with no framework beyond the Python standard library or
Flask, which lane-service already uses. All JSON. Paths are under `/api/`.

| Method, path | Does |
|---|---|
| `GET /api/health` | `{"ok": true, "version": ...}`. The wrapper polls it before opening the browser. |
| `GET /api/system` | Docker version, memory available to Docker, CPU arch, free/busy for 80/8480/8441-8444, internet reachable. |
| `GET /api/labs` | Every `student_local` lab of kind `lab`, in `order`: `id, title, day, memory_mb, approx_download_mb, state, entry_url, actions, unavailable_reason`. |
| `POST /api/labs/<id>/start` | Pull (if needed), then compose up. Returns at once; progress comes from the next row. |
| `GET /api/labs/<id>/progress` | `{"phase": "pulling"\|"starting"\|"running"\|"error", "pulled_mb", "total_mb", "message"}`, polled each second. |
| `POST /api/labs/<id>/stop` | compose stop, keeping volumes. |
| `POST /api/labs/<id>/reset` | compose down with volumes, after the page asks the student to confirm. |
| `POST /api/labs/<id>/actions/<action>` | Runs a manifest `local_actions` entry (the forensics load). |
| `GET /api/update` | Compares the running launcher's digest with `launcher-stable` on ghcr. `{"available": bool}`. |
| `POST /api/shutdown` | Stops every lab and shared service. `Stop Course Labs` calls it, then removes the control container. |

`state` is one of `not-downloaded`, `downloaded`, `starting`, `running`, `stopped`, `error` or `unavailable` (for
example an amd64-only lab on an arm64 Mac). Errors carry a plain-language `message`: the spec lists the examples.

## 6. Release contract (S5 and S6)

- **Images.** One package, `ghcr.io/astevegreen/course-labs`. Tags are `<id>-<service>-<version>` and
  `launcher-<version>`, plus `launcher-stable`.
  - `<version>` is `yyyy.mm.dd-<run_number>`.
  - Third-party images (otterscan, foundry, nginx, python) aren't mirrored. The manifests pin them, and the launcher
    compose files reference them by digest, recorded at release.
  - All of them have amd64 and arm64 manifests (checked 9 Nov 2026).
- **Baked into the launcher image** at `/release/`: `manifest.json` (all manifests with resolved digests), each lab's
  `docker-compose.launcher.yml` under `/release/labs/<id>/`, and the router overlay with its `routes/local/` files.
- **The exclusion list.** S5 moves it into `dl/student-exclude.txt` (fnmatch patterns, the ones `pages.yml` uses
  today). `pages.yml`, `vm-build.yml` and every student image build context read it. A test like
  `tools/tests/test_src_zip.py` proves no excluded file lands in a built context.

## 7. What Phase 1 children can rely on

The S1 to S6 split and the merge order are the spec's (section 7). Each child reads this file first. S2, S3 and S4
write their labs' `lab.yaml` fields only after S1's manifests land on `main`. Until then, each records the fields it
needs in its launcher compose file's header comment.
