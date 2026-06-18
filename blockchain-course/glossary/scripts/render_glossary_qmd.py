#!/usr/bin/env python3
"""Render the canonical terms YAML into a Quarto page."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
GLOSSARY = ROOT / "glossary"
TERMS = GLOSSARY / "terms.yml"
SLIDE_INDEX = GLOSSARY / "slide-index.yml"
OUT = GLOSSARY / "index.qmd"
DATA_OUT = GLOSSARY / "terms.json"


def load_terms() -> list[dict[str, Any]]:
    if not TERMS.exists():
        return []
    data = yaml.safe_load(TERMS.read_text(encoding="utf-8")) or {}
    return data.get("terms", []) or []


def lesson_order() -> list[str]:
    if not SLIDE_INDEX.exists():
        return []
    data = yaml.safe_load(SLIDE_INDEX.read_text(encoding="utf-8")) or {}
    return [lesson.get("lesson_id", "") for lesson in data.get("lessons", []) if lesson.get("lesson_id")]


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def term_sort_key(term: dict[str, Any]) -> str:
    return str(term.get("display") or term.get("term") or "").lower()


def web_terms(terms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for term in terms:
        source = term.get("source", {}) or {}
        tags = term.get("tags", []) or []
        aliases = term.get("aliases", []) or []
        search_blob = " ".join(
            [
                term.get("display", ""),
                term.get("definition", ""),
                " ".join(aliases),
                source.get("lesson_id", ""),
                source.get("lesson_title", ""),
                " ".join(tags),
            ]
        ).lower()
        rows.append(
            {
                "display": str(term.get("display") or ""),
                "definition": str(term.get("definition") or ""),
                "aliases": [str(alias) for alias in aliases],
                "source": {
                    "lesson_id": str(source.get("lesson_id") or ""),
                    "lesson_title": str(source.get("lesson_title") or ""),
                    "href": str(source.get("href") or ""),
                    "slide_heading": str(source.get("slide_heading") or ""),
                },
                "tags": [str(tag) for tag in tags],
                "search": search_blob,
            }
        )
    return rows


def glossary_script(payload: str) -> str:
    script = r"""<script>
const glossaryState = __PAYLOAD__;
const searchInput = document.getElementById('glossary-search');
const lessonSelect = document.getElementById('glossary-lesson');
const tagSelect = document.getElementById('glossary-tag');
const table = document.getElementById('glossary-table');
const tbody = table.querySelector('tbody');
const count = document.getElementById('glossary-count');
const statusEl = document.getElementById('glossary-status');
let allTerms = [];
let sortState = { index: 0, direction: 'asc' };

function appendText(parent, text) {
  parent.appendChild(document.createTextNode(text || ''));
}

function buildRow(term) {
  const row = document.createElement('tr');
  row.dataset.search = term.search || '';
  row.dataset.lesson = term.source?.lesson_id || '';
  row.dataset.tags = (term.tags || []).join(' ');

  const termCell = document.createElement('td');
  const termName = document.createElement('div');
  termName.className = 'glossary-term';
  appendText(termName, term.display);
  termCell.appendChild(termName);
  const aliases = document.createElement('div');
  aliases.className = 'glossary-aliases';
  appendText(aliases, (term.aliases || []).join(', '));
  termCell.appendChild(aliases);

  const definitionCell = document.createElement('td');
  appendText(definitionCell, term.definition);

  const lessonCell = document.createElement('td');
  const lessonId = document.createElement('div');
  appendText(lessonId, term.source?.lesson_id || '');
  lessonCell.appendChild(lessonId);
  const lessonTitle = document.createElement('div');
  lessonTitle.className = 'glossary-meta';
  appendText(lessonTitle, term.source?.lesson_title || '');
  lessonCell.appendChild(lessonTitle);

  const sourceCell = document.createElement('td');
  sourceCell.className = 'glossary-source';
  if (term.source?.href) {
    const link = document.createElement('a');
    link.href = term.source.href;
    appendText(link, term.source.slide_heading || 'Source slide');
    sourceCell.appendChild(link);
  } else {
    appendText(sourceCell, term.source?.slide_heading || '');
  }

  const tagsCell = document.createElement('td');
  const tagsWrap = document.createElement('div');
  tagsWrap.className = 'glossary-tags';
  (term.tags || []).forEach((tag) => {
    const tagEl = document.createElement('span');
    appendText(tagEl, tag);
    tagsWrap.appendChild(tagEl);
  });
  tagsCell.appendChild(tagsWrap);

  [termCell, definitionCell, lessonCell, sourceCell, tagsCell].forEach((cell) => row.appendChild(cell));
  return row;
}

function cellValue(term, index) {
  if (index === 0) return term.display || '';
  if (index === 1) return term.definition || '';
  if (index === 2) return `${term.source?.lesson_id || ''} ${term.source?.lesson_title || ''}`;
  if (index === 3) return term.source?.slide_heading || '';
  return (term.tags || []).join(' ');
}

function normalizeSearchText(value) {
  return String(value || '').toLowerCase().replace(/\s+/g, ' ').trim();
}

function isExactQueryMatch(term, normalizedQuery) {
  if (!normalizedQuery) return false;
  const exactCandidates = [term.display, ...(term.aliases || [])];
  return exactCandidates.some((candidate) => normalizeSearchText(candidate) === normalizedQuery);
}

function visibleTerms() {
  const query = normalizeSearchText(searchInput.value);
  const lesson = lessonSelect.value;
  const tag = tagSelect.value;
  return allTerms.filter((term) => {
    const matchesQuery = !query || (term.search || '').includes(query);
    const matchesLesson = !lesson || term.source?.lesson_id === lesson;
    const matchesTag = !tag || (term.tags || []).includes(tag);
    return matchesQuery && matchesLesson && matchesTag;
  });
}

function renderRows() {
  const query = normalizeSearchText(searchInput.value);
  const terms = visibleTerms().sort((a, b) => {
    if (query) {
      const aExact = isExactQueryMatch(a, query);
      const bExact = isExactQueryMatch(b, query);
      if (aExact !== bExact) return aExact ? -1 : 1;
    }
    const av = cellValue(a, sortState.index).toLowerCase();
    const bv = cellValue(b, sortState.index).toLowerCase();
    return sortState.direction === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
  });
  const fragment = document.createDocumentFragment();
  terms.forEach((term) => fragment.appendChild(buildRow(term)));
  tbody.replaceChildren(fragment);
  count.textContent = terms.length;
}

table.querySelectorAll('th').forEach((header, index) => {
  header.addEventListener('click', () => {
    const direction = header.dataset.direction === 'asc' ? 'desc' : 'asc';
    table.querySelectorAll('th').forEach((th) => delete th.dataset.direction);
    header.dataset.direction = direction;
    sortState = { index, direction };
    renderRows();
  });
});

[searchInput, lessonSelect, tagSelect].forEach((el) => el.addEventListener('input', renderRows));

fetch('terms.json')
  .then((response) => {
    if (!response.ok) throw new Error(`Unable to load terms.json (${response.status})`);
    return response.json();
  })
  .then((data) => {
    allTerms = data.terms || [];
    statusEl.textContent = '';
    renderRows();
  })
  .catch((error) => {
    statusEl.textContent = error.message;
    statusEl.classList.add('glossary-error');
    count.textContent = '0';
  });
</script>"""
    return script.replace("__PAYLOAD__", payload)


def pdf_entries(terms: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    current = ""
    for term in terms:
        display = str(term.get("display", ""))
        first = display[:1].upper() if display else "#"
        if first != current:
            current = first
            lines.append(f"\n## {current}\n")
        source = term.get("source", {}) or {}
        aliases = term.get("aliases", []) or []
        alias_text = f" Aliases: {', '.join(aliases)}." if aliases else ""
        lines.append(f"**{display}.** {term.get('definition', '')}{alias_text}")
        lines.append("")
        href = source.get("href")
        heading = source.get("slide_heading")
        if href:
            lines.append(f"Source: {source.get('lesson_id')} - [{heading}]({href}).")
        else:
            lines.append(f"Source: {source.get('lesson_id')} - {heading}.")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    terms = sorted(load_terms(), key=term_sort_key)
    present_lessons = {
        (term.get("source") or {}).get("lesson_id", "")
        for term in terms
        if term.get("source")
    }
    ordered_lessons = lesson_order()
    lessons = [lesson for lesson in ordered_lessons if lesson in present_lessons]
    lessons.extend(sorted(present_lessons - set(lessons)))
    tags = sorted({tag for term in terms for tag in (term.get("tags", []) or [])})
    lesson_options = "\n".join(f"<option value=\"{esc(lesson)}\">{esc(lesson)}</option>" for lesson in lessons)
    tag_options = "\n".join(f"<option value=\"{esc(tag)}\">{esc(tag)}</option>" for tag in tags)
    payload = json.dumps({"count": len(terms)})
    data = {"count": len(terms), "lessons": lessons, "tags": tags, "terms": web_terms(terms)}
    DATA_OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    script = glossary_script(payload)
    qmd = f"""---
title: "Course Glossary"
format:
  html:
    toc: true
    page-layout: full
    css: glossary.css
---

This glossary defines key terms used in the course slides and links each term to its first substantive appearance.

[Download PDF](index.pdf){{.btn .btn-primary}}

<div class=\"glossary-tools\">
  <label>Search
    <input id=\"glossary-search\" type=\"search\" placeholder=\"Search terms, definitions, aliases, lessons, or tags\">
  </label>
  <label>Lesson
    <select id=\"glossary-lesson\">
      <option value=\"\">All lessons</option>
      {lesson_options}
    </select>
  </label>
  <label>Tag
    <select id=\"glossary-tag\">
      <option value=\"\">All tags</option>
      {tag_options}
    </select>
  </label>
  <div class=\"glossary-count\"><span id=\"glossary-count\">{len(terms)}</span> terms</div>
</div>

<div id=\"glossary-status\" class=\"glossary-status\">Loading glossary terms...</div>

<table class=\"glossary-table\" id=\"glossary-table\">
  <thead>
    <tr>
      <th data-sort=\"term\">Term</th>
      <th data-sort=\"definition\">Definition</th>
      <th data-sort=\"lesson\">Lesson</th>
      <th data-sort=\"source\">First slide</th>
      <th data-sort=\"tags\">Tags</th>
    </tr>
  </thead>
  <tbody></tbody>
</table>

{script}
"""
    OUT.write_text(qmd, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(terms)} terms")
    print(f"Wrote {DATA_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
