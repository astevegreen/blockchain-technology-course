"""The release baked into the launcher image at /release/ (docs/student-launcher-design.md section 6).

/release/manifest.json: {"version", "launcher_image", "labs": [every lab.yaml as JSON], "images": {VAR: ref}}
/release/labs/<id>/docker-compose.launcher.yml for every student_local lab and shared service.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

ROUTER = "router"
LANE_SERVICE = "lane-service"
# Shown on the control page. Fixtures exist only in the smoke test's fixture build (spec 4.5).
PAGE_KINDS = ("lab", "fixture")


def image_var(lab_id: str, service: str, spec: dict) -> str:
    """The variable a launcher compose file reads a service's image from (lab.schema.json `variable`)."""
    return spec.get("variable") or f"{lab_id}_{service}_IMAGE".upper().replace("-", "_")


@dataclass
class Release:
    version: str
    launcher_image: str
    labs: list[dict]
    images: dict[str, str] = field(default_factory=dict)
    root: Path = Path("/release")

    @classmethod
    def load(cls, root: Path) -> "Release":
        data = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        return cls(version=str(data.get("version", "dev")), launcher_image=data.get("launcher_image", ""),
                   labs=list(data.get("labs", [])), images=dict(data.get("images", {})), root=root)

    def lab(self, lab_id: str) -> dict | None:
        return next((lab for lab in self.labs if lab.get("id") == lab_id), None)

    def page_labs(self) -> list[dict]:
        labs = [lab for lab in self.labs if lab.get("student_local") and lab.get("kind") in PAGE_KINDS]
        return sorted(labs, key=lambda lab: (lab.get("order", {}).get("day") is None,
                                             lab.get("order", {}).get("day") or 0,
                                             lab.get("order", {}).get("position", 0), lab.get("id", "")))

    def compose_file(self, lab: dict) -> Path:
        return self.root / "labs" / lab["id"] / lab.get("student_compose_file", "docker-compose.launcher.yml")

    def lab_images(self, lab: dict) -> dict[str, str]:
        """VAR -> image reference for every service the lab's launcher compose file starts."""
        refs = {}
        for name, spec in (lab.get("services") or {}).items():
            var = image_var(lab["id"], name, spec)
            ref = self.images.get(var) or spec.get("image")
            if ref:
                refs[var] = ref
        return refs

    def all_images(self) -> dict[str, str]:
        refs = dict(self.images)
        for lab in self.labs:
            for var, ref in self.lab_images(lab).items():
                refs.setdefault(var, ref)
        return refs

    def networks(self) -> dict[str, bool]:
        """The union of every student_local manifest's networks: name -> internal."""
        nets: dict[str, bool] = {}
        for lab in self.labs:
            if not lab.get("student_local"):
                continue
            for net in lab.get("networks") or []:
                nets[net["name"]] = nets.get(net["name"], True) and bool(net.get("internal"))
        return nets

    def compose_projects(self) -> dict[str, str]:
        """compose_project -> lab id, for every manifest (instructor ones too: a classroom stack runs them)."""
        return {lab["compose_project"]: lab["id"] for lab in self.labs if lab.get("compose_project")}
