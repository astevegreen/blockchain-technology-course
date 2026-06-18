#!/usr/bin/env python3
"""Patch Quarto-generated assets that still contain remote runtime imports."""

from pathlib import Path
import os
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
SITE = Path(os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", ROOT / "_site")).resolve()
AXE_SOURCE = ROOT / "assets" / "vendor" / "axe-core" / "4.10.3" / "axe.min.js"
AXE_DIR = SITE / "site_libs" / "quarto-html" / "axe"
AXE_CHECK = AXE_DIR / "axe-check.js"
AXE_TARGET = AXE_DIR / "axe.min.js"

REMOTE_IMPORT = (
    '    const axe = (await import("https://cdn.'
    'sky' + 'pack.dev/pin/axe-core@v4.10.3-aVOFXWsJaCpVrtv89pCa/'
    'mode=imports,min/optimized/axe-core.js")).default;'
)

LOCAL_LOADER = """    const axe = await new Promise((resolve, reject) => {
      if (globalThis.axe) {
        resolve(globalThis.axe);
        return;
      }
      const script = document.createElement("script");
      script.src = new URL("./axe.min.js", import.meta.url).href;
      script.onload = () => {
        if (globalThis.axe) {
          resolve(globalThis.axe);
        } else {
          reject(new Error("Local axe-core did not initialize"));
        }
      };
      script.onerror = () => reject(new Error("Unable to load local axe-core"));
      document.head.appendChild(script);
    });"""

MATHJAX_REPLACEMENTS = {
    "https://cdn.jsdelivr.net/npm/mathjax@2.7.9/MathJax.js": (
        "/assets/vendor/mathjax/2.7.9/MathJax.js"
    ),
    "https://cdn.jsdelivr.net/npm/mathjax@2/MathJax.js": (
        "/assets/vendor/mathjax/2.7.9/MathJax.js"
    ),
    "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js": (
        "/assets/vendor/mathjax/3.2.2/es5/tex-mml-chtml.js"
    ),
}

LOCAL_KATEX = "/assets/vendor/katex/0.17.0"
KATEX_REPLACEMENTS = {
    "https://cdn.jsdelivr.net/npm/katex": LOCAL_KATEX,
    'e={version:"latest",delimiters:': (
        f'e={{local:"{LOCAL_KATEX}",version:"latest",delimiters:'
    ),
}
KATEX_DEFAULT_OPTIONS = re.compile(
    r"(let defaultOptions = \{\n)"
    r"(?:\s*local: ['\"]/assets/vendor/katex/0\.17\.0['\"],\n)*"
)

GOOGLE_FONT_IMPORT = re.compile(
    r"@import\s*"
    r"(?:"
    r"url\(\s*(?P<urlquote>['\"]?)https://fonts\.googleapis\.com"
    r"[^)]*(?P=urlquote)\s*\)"
    r"|(?P<quote>['\"])https://fonts\.googleapis\.com.*?(?P=quote)"
    r"|https://fonts\.googleapis\.com[^\s;]+"
    r")\s*;?",
    re.IGNORECASE,
)


def replace_text(path: Path, replacements: dict[str, str]) -> bool:
    text = path.read_text(encoding="utf-8")
    patched = text
    for remote, local in replacements.items():
        patched = patched.replace(remote, local)

    if patched == text:
        return False

    path.write_text(patched, encoding="utf-8")
    return True


def strip_google_font_imports(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    patched = GOOGLE_FONT_IMPORT.sub("", text)

    if patched == text:
        return False

    path.write_text(patched, encoding="utf-8")
    return True


def patch_katex(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    patched = text
    for remote, local in KATEX_REPLACEMENTS.items():
        patched = patched.replace(remote, local)

    if path.name == "katex.js":
        patched = KATEX_DEFAULT_OPTIONS.sub(
            lambda match: f"{match.group(1)}\t\tlocal: '{LOCAL_KATEX}',\n",
            patched,
            count=1,
        )

    if patched == text:
        return False

    path.write_text(patched, encoding="utf-8")
    return True


def patch_axe() -> None:
    if not AXE_CHECK.exists():
        return

    AXE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(AXE_SOURCE, AXE_TARGET)

    replace_text(AXE_CHECK, {REMOTE_IMPORT: LOCAL_LOADER})


def patch_mathjax() -> None:
    if not SITE.exists():
        return

    for path in SITE.rglob("*.html"):
        replace_text(path, MATHJAX_REPLACEMENTS)

    reveal_math = SITE / "site_libs" / "revealjs" / "plugin" / "math"
    if reveal_math.exists():
        for path in reveal_math.glob("*.js"):
            replace_text(path, MATHJAX_REPLACEMENTS)
            patch_katex(path)


def patch_google_fonts() -> None:
    if not SITE.exists():
        return

    for path in SITE.rglob("*.css"):
        strip_google_font_imports(path)


def main() -> None:
    patch_axe()
    patch_mathjax()
    patch_google_fonts()


if __name__ == "__main__":
    main()
