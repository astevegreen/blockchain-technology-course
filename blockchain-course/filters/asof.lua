-- "As of" dates (docs/build-spec.md, "Readability and site items").
--
-- A fact that changes carries the date it was true, written in the `.qmd` as a tagged date with no words and no
-- parentheses: `[11 Nov 2026]{.asof}`. This filter adds the parentheses, so the page shows "(11 Nov 2026)", and
-- the format can change here, in one place. Searching the lessons for `{.asof}` finds every such date;
-- `python tools/asof.py` lists them oldest first, and its `--check` refuses a tag that is not a date.

function Span(span)
  if span.classes:includes("asof") then
    span.content:insert(1, pandoc.Str("("))
    span.content:insert(pandoc.Str(")"))
    return span
  end
end
