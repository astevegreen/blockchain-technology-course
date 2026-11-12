-- Sources in the speaker notes (docs/build-spec.md, "Readability and site items").
--
-- On a RevealJS lesson, moves every `[@key]` citation off the slide the class sees and into that slide's speaker
-- notes, under "Cited on the slide", each beside the words it followed, so the instructor's notes view still
-- shows which claim rests on which source. The `.qmd` is not edited: the citations stay in the source, and the
-- lesson's reference list still lists every one, because citeproc runs after this filter and reads the notes.
--
-- A slide is what Pandoc makes one: it starts at a heading at or above the slide level, or at a horizontal rule.
-- Citations already inside a `.notes` div are left where they are. A slide with no notes div gets one.
-- A table column that held only citations (a "Source" column) is dropped, so the slide shows no empty column.
--
-- Runs before Quarto's own filters (`at: pre-ast` in _quarto.yml), on the document as Pandoc first reads it.
-- Other formats (the home page, the glossary) keep their citations: the filter does nothing there.

if not FORMAT:match("revealjs") then
  return {}
end

local slide_level = (PANDOC_WRITER_OPTIONS and PANDOC_WRITER_OPTIONS.slide_level) or 2
local WORDS = 8 -- words of the claim shown beside each moved citation
local HEADING = "Cited on the slide"
local stringify = pandoc.utils.stringify

local function is_notes(block)
  return block.t == "Div" and block.classes:includes("notes")
end

local function starts_slide(block)
  return (block.t == "Header" and block.level <= slide_level) or block.t == "HorizontalRule"
end

-- A div that wraps whole slides (a hidden run of slides): its slides are handled one by one.
local function holds_slides(div)
  local found = false
  div:walk({
    Header = function(h)
      if h.level <= slide_level then found = true end
    end,
  })
  return found
end

local function words_of(inlines)
  local words = {}
  -- Without the punctuation that closed the claim before: ". Blocks are scarce" reads "Blocks are scarce".
  for word in stringify(inlines):gsub("^[%s%.,;:!%?%)]+", ""):gmatch("%S+") do
    words[#words + 1] = word
  end
  return words
end

-- The claim a citation followed: the last WORDS words before it (back to the citation before, if any), or, when
-- it opens the text, the first WORDS words after it, or (a table cell that held only the citation) the row's
-- first cell.
local function label_for(before, after, fallback)
  local words = words_of(before)
  if #words > 0 then
    local from = math.max(1, #words - WORDS + 1)
    return (from > 1 and "…" or "") .. table.concat(words, " ", from)
  end
  words = words_of(after)
  if #words > 0 then
    local to = math.min(#words, WORDS)
    return table.concat(words, " ", 1, to) .. (to < #words and "…" or "")
  end
  return fallback or ""
end

local function is_space(inline)
  return inline.t == "Space" or inline.t == "SoftBreak"
end

-- One run of inline text without its citations; each citation is added to `entries` with its label.
local function strip_inlines(inlines, entries, fallback)
  local kept = pandoc.Inlines({})
  local moved = false
  local mark = 0 -- how much of `kept` the citation before had already claimed
  local last = nil -- that citation's label
  for i, inline in ipairs(inlines) do
    if inline.t == "Cite" then
      moved = true
      while #kept > mark and is_space(kept[#kept]) do
        kept:remove(#kept)
      end
      local before = pandoc.Inlines({})
      for j = mark + 1, #kept do
        before:insert(kept[j])
      end
      local label
      if last and #words_of(before) == 0 then
        label = last -- a second citation for the same claim
      else
        local after = pandoc.Inlines({})
        for j = i + 1, #inlines do
          if inlines[j].t ~= "Cite" then after:insert(inlines[j]) end
        end
        label = label_for(before, after, fallback)
      end
      entries[#entries + 1] = { label = label, cite = inline }
      mark, last = #kept, label
    else
      kept:insert(inline)
    end
  end
  if not moved then
    return nil
  end
  while #kept > 0 and is_space(kept[1]) do
    kept:remove(1)
  end
  return kept
end

local strip_blocks -- defined below; tables and blocks call each other

-- Paragraphs that held nothing but a citation are dropped, not left empty.
local drop_empty = {
  Para = function(p)
    if #p.content == 0 then return {} end
  end,
  Plain = function(p)
    if #p.content == 0 then return {} end
  end,
}

local function strip_rows(rows, entries, emptied)
  for r, row in ipairs(rows) do
    local cells = row.cells
    local label = cells[1] and stringify(cells[1].contents) or nil
    for c, cell in ipairs(cells) do
      local before = #entries
      cell.contents = strip_blocks(cell.contents, entries, label)
      if emptied and #entries > before and #cell.contents == 0 then
        emptied[c] = true
      end
      cells[c] = cell
    end
    row.cells = cells
    rows[r] = row
  end
  return rows
end

-- True when every row has one plain cell per column, so a column can be removed by position.
local function is_grid(rows, columns)
  for _, row in ipairs(rows) do
    if #row.cells ~= columns then return false end
    for _, cell in ipairs(row.cells) do
      if cell.col_span ~= 1 or cell.row_span ~= 1 then return false end
    end
  end
  return true
end

local function without_column(rows, c)
  for r, row in ipairs(rows) do
    local cells = row.cells
    cells:remove(c)
    row.cells = cells
    rows[r] = row
  end
  return rows
end

local function strip_table(tbl, entries)
  local emptied = {} -- columns where a body cell lost its only content, a citation
  local head = tbl.head
  head.rows = strip_rows(head.rows, entries, nil)
  local bodies = tbl.bodies
  for _, body in ipairs(bodies) do
    body.head = strip_rows(body.head, entries, nil)
    body.body = strip_rows(body.body, entries, emptied)
  end
  local foot = tbl.foot
  foot.rows = strip_rows(foot.rows, entries, nil)
  local caption = tbl.caption
  caption.long = strip_blocks(caption.long, entries, nil)

  -- Drop a column whose body is now empty because its cells held only citations.
  local colspecs = tbl.colspecs
  local columns = #colspecs
  local grid = is_grid(head.rows, columns) and is_grid(foot.rows, columns)
  for _, body in ipairs(bodies) do
    grid = grid and is_grid(body.head, columns) and is_grid(body.body, columns)
  end
  if grid then
    for c = columns, 1, -1 do
      local empty = emptied[c] == true
      for _, body in ipairs(bodies) do
        for _, row in ipairs(body.body) do
          if #row.cells[c].contents > 0 then empty = false end
        end
      end
      if empty and #colspecs > 1 then
        colspecs:remove(c)
        head.rows = without_column(head.rows, c)
        foot.rows = without_column(foot.rows, c)
        for _, body in ipairs(bodies) do
          body.head = without_column(body.head, c)
          body.body = without_column(body.body, c)
        end
      end
    end
  end

  tbl.colspecs = colspecs
  tbl.head = head
  tbl.bodies = bodies
  tbl.foot = foot
  tbl.caption = caption
  return tbl
end

strip_blocks = function(blocks, entries, fallback)
  local stripped = pandoc.Blocks(blocks):walk({
    traverse = "topdown",
    Table = function(tbl)
      return strip_table(tbl, entries), false
    end,
    Div = function(div)
      if is_notes(div) then return div, false end
    end,
    Inlines = function(inlines)
      return strip_inlines(inlines, entries, fallback)
    end,
  })
  return stripped:walk(drop_empty)
end

local function cited_list(entries)
  local items = {}
  for _, entry in ipairs(entries) do
    local line = pandoc.Inlines({})
    if entry.label ~= "" then
      line:insert(pandoc.Str(entry.label))
      line:insert(pandoc.Space())
    end
    line:insert(entry.cite)
    items[#items + 1] = { pandoc.Plain(line) }
  end
  return { pandoc.Para({ pandoc.Strong({ pandoc.Str(HEADING) }) }), pandoc.BulletList(items) }
end

local function process(blocks)
  local out = pandoc.Blocks({})
  local entries = {}
  local notes_at = nil -- where this slide's notes div sits in `out`

  local function finish_slide()
    if #entries > 0 then
      if notes_at then
        local notes = out[notes_at]
        notes.content:extend(cited_list(entries))
        out[notes_at] = notes
      else
        out:insert(pandoc.Div(cited_list(entries), pandoc.Attr("", { "notes" })))
      end
    end
    entries = {}
    notes_at = nil
  end

  for _, block in ipairs(blocks) do
    if starts_slide(block) then
      finish_slide()
    end
    if is_notes(block) then
      out:insert(block)
      notes_at = #out
    elseif block.t == "Div" and holds_slides(block) then
      finish_slide()
      block.content = process(block.content)
      out:insert(block)
    else
      out:extend(strip_blocks({ block }, entries, nil))
    end
  end
  finish_slide()
  return out
end

return {
  {
    Pandoc = function(doc)
      doc.blocks = process(doc.blocks)
      return doc
    end,
  },
}
