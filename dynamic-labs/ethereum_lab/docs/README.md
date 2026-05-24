# Documentation index

Lab and reference markdown lives in subfolders by audience and topic. The web app mirrors this tree under `frontend/public/docs/` when you build (see `frontend/scripts/copy-docs.cjs`).

| Folder | Contents |
|--------|----------|
| **`architecture/`** | High-level system design (`ARCHITECTURE.md`, etc.) |
| **`guides/`** | How-tos and references: chain interaction, RPC details, manual, quick reference, bytecode lab, role scenario rules, student Live tab |
| **`instructor/`** | Onboarding, Docker/setup, facilitation, and multi-block lab scenarios |
| **`labs/gui/`** | Primary **Live** GUI labs: Beacon Chain, Contract Builder, Tokenization, Token Concepts, Contract Lab |
| **`labs/scenarios/`** | CLI and multi-party scenario labs (house sale, vehicle title, forensics, voting, crowdfunding, …) |

Paths in the UI look like `/docs/<folder>/…/<file>.md` (for example `/docs/labs/gui/BEACON_CHAIN_LAB.md`).
