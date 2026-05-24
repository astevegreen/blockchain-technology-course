# Blockchain Course

A blockchain course, packaged as code. The repository
ships the lecture site, hands-on labs, a question bank, a quiz engine, and the
build pipeline that produces a classroom-ready VM image — all of it forkable and
reusable for a specific course offering.

## Overview

The course is split into three layers, each of which can stand on its own:

- **`blockchain-course/`** — a [Quarto](https://quarto.org) website containing
  every lesson (RevealJS slides with instructor notes), the syllabus and
  schedule, and a set of self-contained "static" lab pages that render as HTML
  and need no server. This is what gets published to GitHub Pages.
- **`dynamic-labs/`** — the containerized side of the course: an nginx router
  fronting per-lab services (Bitcoin, Consensus, Cryptography, P2P Trust,
  Ethereum, Hyperledger Fabric), the centralized instructor login, the lane
  service that spins up per-student containers on demand, the trust-game and
  BGP exercises, and the quiz engine. This layer requires a host that can run
  Docker.
- **`vm-build/`** — a [Packer](https://www.packer.io) build that produces a
  preconfigured Ubuntu VM image with the dynamic labs baked in. CI publishes
  split `qcow2` and `ova` artifacts to a GitHub Release for instructors to
  download.

The `quizes/` directory holds the lesson-level question banks (JSON) and the
script that bundles them into a single import for the quiz engine. The bundle
is produced by a manual workflow and consumed by an instructor through the quiz
engine UI.

Three manual GitHub Actions workflows drive the release pipeline:

| Workflow | Trigger | Output |
|----------|---------|--------|
| `pages.yml` | `workflow_dispatch` | Renders the Quarto site and deploys it to GitHub Pages. Embeds links to the latest VM release. |
| `vm-build.yml` | `workflow_dispatch` | Builds the VM image with Packer and publishes split `qcow2` + `ova` parts to a `latest-vm-<run_id>` Release. Keeps only the two most recent releases. |
| `quiz-bundle.yml` | `workflow_dispatch` | Validates and concatenates the per-lesson quiz banks into one JSON file uploaded as a workflow artifact (30-day retention). |

## Deploying as a Static Site (GitHub Pages only)

If you just want the slides, readings, static labs, syllabus, schedule, and
source download — no Docker, no VM — GitHub Pages is sufficient on its own.

1. Fork or copy this repository into your own GitHub org/user.
2. In **Settings → Pages**, set the source to **GitHub Actions**.
3. Open **Actions → Publish Course to GitHub Pages (Manual) → Run workflow** on
   the `main` branch.

The workflow renders `blockchain-course/` with Quarto, packages a student-facing
`src.zip` (instructor quiz banks and forensics solutions are excluded), and
publishes the result. Re-run it whenever you want the site to reflect new
commits on `main`.

The published site links to the most recent `latest-vm-*` Release when one
exists; if no VM has been built yet, the links are simply omitted.

### Customizing or Removing the ACI Theme

Slides ship with the Army Cyber Institute theme, provided by the local Quarto
extension under `blockchain-course/_extensions/aci/`. Each lesson opts in via:

```yaml
format:
  aci-revealjs:
    slide-level: 2
```

You have three reasonable options:

- **Keep the ACI theme.** Nothing to do. The branding stays.
- **Rebrand in place.** Edit `_extensions/aci/_extension.yml` and the SCSS in
  `_extensions/aci/revealjs/custom.scss` (colors, fonts) and replace the logo
  at `_extensions/aci/logos/ACILogo.png`. Lessons keep referencing
  `aci-revealjs` and inherit your branding.
- **Switch to stock RevealJS.** Search-and-replace `aci-revealjs` with
  `revealjs` across `blockchain-course/lessons/**/*.qmd`, and drop the
  `_extensions/aci/logos/` line from the `resources:` block in
  `blockchain-course/_quarto.yml`. The deck loses the header/footer branding
  but the content is unchanged.

The HTML site theme is controlled separately in `blockchain-course/_quarto.yml`
(currently `cosmo`) and can be swapped to any [bootswatch](https://bootswatch.com)
theme without touching the lessons.

## Deploying the Dynamic Labs

The dynamic side requires a host running Docker + Docker Compose v2 with TCP 80
(and 443 if you want TLS) free. The quick paths are below; see
[`dynamic-labs/README.md`](dynamic-labs/README.md) for capacity tuning,
classroom networking (WiFi AP / Ethernet LAN), instructor credential rotation,
and direct Compose use.

### Prebuilt VM (recommended for instructors)

Run the **Build VM Image (Manual)** workflow once. When it finishes, grab the
`blockchain-lab.qcow2.part-*` (KVM/libvirt, source for Hyper-V conversion) or
`blockchain-lab.ova.part-*` (VirtualBox/VMware) parts plus `hashes.txt` from
the `latest-vm-*` Release.

```bash
cat blockchain-lab.qcow2.part-* > blockchain-lab.qcow2
sha256sum -c <(grep '  blockchain-lab.qcow2$' hashes.txt)
```

Import into your hypervisor (2 vCPU / 4–8 GB RAM / NAT or bridged). Log in as
`student` / `student`, then:

```bash
cd /opt/dynamic-labs
./lab-manager.sh deploy --mode instructor --no-tls --max-student-capacity 20
./lab-manager.sh start all
```

For a single learner on a laptop, use `--mode student` instead.

### Public Cloud VM with HTTPS

Point a DNS A record at the VM, open inbound 80 and 443, then:

```bash
cd dynamic-labs
sudo ./deploy-cloud.sh --domain labs.example.edu
./lab-manager.sh start all
```

`deploy-cloud.sh` provisions a Let's Encrypt certificate, brings up the shared
infrastructure (router, course-site, instructor-auth, lane-service), and
pre-builds the on-demand student images. The domain is persisted so subsequent
`lab-manager.sh` invocations keep the HTTPS configuration.

### Local Host (no VM, no TLS)

On any Linux host with Docker:

```bash
cd dynamic-labs
./lab-manager.sh deploy --mode student --no-tls
./lab-manager.sh start all
```

Browse to `http://localhost/`. Instructor credentials and runtime secrets are
written to `dynamic-labs/.runtime/`.

## Recommended Workflow

The intended pattern is **fork-per-offering**: each section or semester gets
its own fork so it can drift (date stamps, schedule, capstones, deletions)
without touching the upstream master copy. Patches that aren't offering-specific
flow back via pull request.

1. **Fork** this repository into your org as e.g. `blockchain-course-fall26`.
2. **Customize.** Edit the syllabus and schedule under
   `blockchain-course/assets/`, prune or add lessons under
   `blockchain-course/lessons/`, regenerate quiz banks for any new lessons
   (see `quizes/QUIZ_BANK_GENERATION_GUIDE.md`), and adjust the branding as
   described above.
3. **Publish the site.** In **Settings → Pages** pick **GitHub Actions** as
   the source, then run the **Publish Course to GitHub Pages** workflow.
4. **Build the VM** (optional, only if students will use a local VM image).
   Run the **Build VM Image** workflow; expect 2 hours. It will
   self-clean and keep only the two most recent releases.
5. **Build the quiz bundle.** Run the **Build Quiz Bank Bundle** workflow,
   download the artifact, and import it through the quiz engine's instructor
   UI on your deployment.
6. **Upstream fixes.** When you fix a bug or improve a lesson in a way that
   isn't tied to your offering, open a PR back against the upstream repo.
   Offering-specific changes (your roster, your dates, removed weeks) should
   live only in your fork.

### A Note on Workflow Artifacts and Retention

All three workflows are `workflow_dispatch`-only — nothing fires on push, so
your fork won't waste runner minutes until you ask for a build.

The quiz bundle is published as a **workflow artifact** with **30-day
retention**. After 30 days the artifact is purged, and re-running the workflow
is the only way to retrieve the current bundle. If you've authored new
questions since the last successful run, treat that re-run as the canonical
source of truth and re-import the bundle on your deployment. The per-lesson
JSON in `quizes/quiz_json/` is the durable copy; the artifact is just a
convenience packaging of it.

VM releases follow the opposite policy: they live as proper GitHub Releases
and only get pruned when a newer build supersedes them (the workflow keeps the
two most recent). Pages deployments overwrite each other and have no retention
to worry about.

## Acknowledgements

This course is developed and maintained by the
[**Army Cyber Institute**](https://cyber.army.mil/) at the United States
Military Academy at West Point. The slide theme, branding, and instructional
design carry the ACI imprint and are released here for the broader
cybersecurity education community to use, fork, and adapt.

The "courseware as code" model itself was pioneered by the **U.S. Army Cyber
School**. Their tutorial and contributing guide remain a useful reference for
anyone considering this style of curriculum development:

- ["GitLab — Courseware as Code, with Ben Allison"](https://player.fm/series/business-and-philosophy/gitlab-courseware-as-code-with-ben-allison)
- [Courseware-as-Code tutorial](https://courseware-as-code.gitlab.io/courseware-tutorial/)
- [CyBBH contributor guide](https://common.cybbh.io/contributing/contributing/latest/courseware-as-code.html)

Particular thanks to **Sonny Bhatia** ([cs380.bhatia.dev](https://github.com/aadityabhatia/cs380.bhatia.dev))
for the Quarto-based course site that this layout draws inspiration from.

## License

Released under the [MIT License](LICENSE).
