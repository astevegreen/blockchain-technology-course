#!/usr/bin/env python3
"""Render glossary HTML and PDF from a temporary project copy.

Some shared filesystems do not support Deno KV locking reliably, which Quarto
uses for `.quarto/project-cache`. Rendering from `/tmp` avoids that failure
while preserving the normal website output paths.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GLOSSARY = ROOT / "glossary"
sys.path.insert(0, str(GLOSSARY / "scripts"))

from render_glossary_qmd import load_terms, pdf_entries, term_sort_key  # noqa: E402


def copy_required_inputs(tmp: Path) -> None:
    (tmp / "glossary").mkdir(parents=True, exist_ok=True)
    (tmp / "scripts").mkdir(parents=True, exist_ok=True)
    for name in ("_quarto.yml", "index.qmd", "styles.css"):
        shutil.copy2(ROOT / name, tmp / name)
    shutil.copy2(ROOT / "scripts" / "patch_quarto_output.py", tmp / "scripts" / "patch_quarto_output.py")
    for name in ("index.qmd", "glossary.css", "terms.json"):
        shutil.copy2(GLOSSARY / name, tmp / "glossary" / name)
    axe_source = ROOT / "assets" / "vendor" / "axe-core" / "4.10.3" / "axe.min.js"
    axe_target = tmp / "assets" / "vendor" / "axe-core" / "4.10.3" / "axe.min.js"
    axe_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(axe_source, axe_target)
    if (GLOSSARY / "index.pdf").exists():
        shutil.copy2(GLOSSARY / "index.pdf", tmp / "glossary" / "index.pdf")


def write_pdf_source(tmp: Path) -> None:
    terms = sorted(load_terms(), key=term_sort_key)
    qmd = f"""---
title: "Course Glossary"
format:
  pdf:
    toc: true
    documentclass: article
    geometry:
      - margin=0.75in
---

This glossary defines key terms used in the course slides. The web version links each term to its first substantive appearance in the slides.

{pdf_entries(terms)}
"""
    (tmp / "glossary" / "glossary-pdf.qmd").write_text(qmd, encoding="utf-8")


def run_quarto(tmp: Path, input_path: str, fmt: str, output: str | None = None) -> None:
    command = ["quarto", "render", input_path, "--to", fmt]
    if output:
        command.extend(["--output", output])
    subprocess.run(command, cwd=tmp, check=True)


def copy_referenced_site_assets(tmp: Path) -> None:
    html_path = tmp / "_site" / "glossary" / "index.html"
    html = html_path.read_text(encoding="utf-8")
    refs = re.findall(r'(?:href|src)="([^"]+)"', html)
    for ref in refs:
        if ref.startswith(("http:", "https:", "#", "data:", "mailto:")):
            continue
        ref_file = ref.split("#", 1)[0]
        if not ref_file:
            continue
        source = (html_path.parent / ref_file).resolve()
        try:
            rel = source.relative_to(tmp / "_site")
        except ValueError:
            continue
        if not source.exists() or source.is_dir():
            continue
        dest = ROOT / "_site" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(source, dest)


def rendered_pdf_path(tmp: Path) -> Path:
    root_pdf = tmp / "_site" / "index.pdf"
    if root_pdf.exists():
        return root_pdf
    return tmp / "_site" / "glossary" / "index.pdf"


def copy_outputs(tmp: Path) -> None:
    rendered_pdf = rendered_pdf_path(tmp)
    shutil.copy2(rendered_pdf, GLOSSARY / "index.pdf")

    out_dir = ROOT / "_site" / "glossary"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        print(f"Warning: could not create {out_dir}: {exc}", file=sys.stderr)
        return

    copied_site_html = False
    for name in ("index.html", "index.pdf", "glossary.css", "terms.json"):
        source = rendered_pdf if name == "index.pdf" else tmp / "_site" / "glossary" / name
        try:
            shutil.copy2(source, out_dir / name)
            if name == "index.html":
                copied_site_html = True
        except PermissionError as exc:
            print(f"Warning: could not copy _site/glossary/{name}: {exc}", file=sys.stderr)
    if copied_site_html:
        copy_referenced_site_assets(tmp)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="blockchain-glossary-render.") as tmp_name:
        tmp = Path(tmp_name)
        copy_required_inputs(tmp)
        write_pdf_source(tmp)
        run_quarto(tmp, "glossary/index.qmd", "html")
        run_quarto(tmp, "glossary/glossary-pdf.qmd", "pdf", "index.pdf")
        copy_outputs(tmp)
    print("Rendered _site/glossary/index.html")
    print("Rendered _site/glossary/index.pdf")
    print("Copied glossary/index.pdf")


if __name__ == "__main__":
    main()
