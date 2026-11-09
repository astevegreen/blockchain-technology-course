# Student launcher

A student double-clicks **Start-Course-Labs** and gets a page at `http://127.0.0.1:8470/` that downloads, starts,
stops and resets each lab on their own computer. Design: `docs/student-launcher-design.md` (sections 4 to 6).

| File | What it does |
| --- | --- |
| `Start-Course-Labs.cmd` (Windows), `.command` (macOS), `.sh` (Linux) | Checks Docker (starts Docker Desktop, or opens the install guide), pulls `ghcr.io/astevegreen/course-labs:launcher-stable`, runs it as `course-launcher` with the Docker socket, the `course-launcher-state` volume and `127.0.0.1:8470`, waits for `/api/health`, opens the browser. |
| `Stop-Course-Labs.*` | Asks the page to stop every lab (`POST /api/shutdown`), then removes the `course-launcher` container. Work stays on the volumes. |
| `control/` | The control container: `launcher/` (Python standard library), `static/` (the page), `Dockerfile`. |
| `control/tests/` | Unit tests against a fake Docker, and the wrappers' `--dry-run` tests. `tools/tests/test_student_launcher.py` runs them with the check. |

The names use hyphens because file names may hold only letters, digits, `-`, `_` and `.` (CLAUDE.md rule 3).
The `.command` and `.sh` copies are identical; a test keeps them so. The wrappers are unsigned (owner decision).

## Building the control image

The image carries the release it runs: `manifest.json` and `labs/<id>/docker-compose.launcher.yml`.

```bash
docker buildx build --build-context release=<staged release folder> -t <image> student-launcher/control
```

The release workflow stages that folder from the lab manifests; the smoke test stages one holding the router and
`dynamic-labs/regression-tests/fixtures/hello-lab`.

## Trying a wrapper without Docker

`Start-Course-Labs.sh --dry-run` (or `.cmd --dry-run`) prints `would: …` instead of starting Docker Desktop or a
browser. It still runs `docker` from `PATH`, so the tests put a fake one first.
