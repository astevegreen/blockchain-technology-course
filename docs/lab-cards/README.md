# Lab design cards

Every lab gets a one-page design card before it is built or changed, and the owner approves the card
(`docs/analysis/2026-11-lab-plan.md`, "Stage 2"). The card is where the content decisions sit: the belief, the
case, the choices, the twist. Building the lab afterwards is a technical job.

## Writing a card

1. Copy `template.md` to `<lab-slug>.md` here (letters, digits and `-` only).
2. Fill all ten lines and the opening case. Cite every fact with a `Blockchain.bib` key.
3. Ask the owner to approve it; record their words and the date under **Approval**.

## Building a prediction lab from an approved card

The shared files are in `blockchain-course/assets/labs/shared/`:

- `look.css`: the one look. `index.html` shows every object and what it means.
- `shell.js`: the seven-step shell. `shell-check.html` walks every step with placeholder content.

A lab is one folder, `blockchain-course/assets/labs/<lab-slug>/`, with an `index.html` like this:

```html
<link rel="stylesheet" href="../shared/look.css">
<div data-lab-root></div>
<script src="../shared/shell.js"></script>
<script>
LabShell.start({
  id: "<lab-slug>",
  title: "<lab name>",
  slide: { title: "<slide heading>", href: "<link back to the slide>" },
  steps: {
    "case":   { html: "..." },                                   // the opening case
    commit:   { question: "...", choices: ["...", "..."] },      // line 2
    "do":     { render: function (el, api) { /* line 3; call api.finish({ choice, note }) */ } },
    name:     { term: "...", parts: "...", plain: "..." },       // line 5
    explorer: { html: "..." },                                   // line 6 (or render)
    twist:    { html: "...", question: "...", choices: [...], answer: 0, why: "..." },  // line 7
    tell:     { prompt: "...", example: "..." }                  // line 8
  }
});
</script>
```

The shell refuses a config that is missing a step or names more than one term, and shows why on the page.
`api.finish({ choice })` reports which of the `commit` choices actually happened, so the shell can show the
student's prediction against it; leave `choice` out when the action has no single outcome.

What the shell gives every lab: the seven named steps; a commitment that locks; Back, Next and a Restart that
asks first; projector mode (P key, the button, or `?display=projector`); progress kept in the browser, so a
reload resumes; no network, no Pyodide, and it runs from a plain file in `src.zip`.

`tools/tests/test_lab_shared.py` checks the shared files and this template.
