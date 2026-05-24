// Shared lightweight markdown renderer used by the lesson UI and the
// exercises grid. Handles:
//   - triple-backtick fenced code blocks (rendered with a copy button)
//   - inline `code`
//   - **bold**
//   - paragraph breaks (\n\n)
//   - bullet (\n• ) and numbered (\n1. ) list lead-ins
//   - line breaks (\n)
//
// Fenced blocks are pulled out before inline replacements run, so their
// contents are never further munged.

function renderCodeBlock(raw) {
  const body = raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  const attr = raw
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return `<div class="code-block"><button type="button" class="copy-btn" data-copy="${attr}" aria-label="Copy to clipboard">Copy</button><pre><code>${body}</code></pre></div>`;
}

function renderProseMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n\n+/g, '</p><p>')
    .replace(/\n• /g, '</p><p class="md-bullet">• ')
    .replace(/\n(\d+)\. /g, '</p><p class="md-bullet">$1. ')
    .replace(/\n/g, '<br>');
}

function renderInlineMarkdown(text) {
  if (!text) return '';
  const re = /```[a-zA-Z0-9_-]*\n?([\s\S]*?)```/g;
  const out = [];
  let lastIdx = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIdx) {
      out.push(renderProseMarkdown(text.slice(lastIdx, m.index)));
    }
    out.push(renderCodeBlock(m[1].replace(/\n+$/, '')));
    lastIdx = m.index + m[0].length;
  }
  if (lastIdx < text.length) {
    out.push(renderProseMarkdown(text.slice(lastIdx)));
  }
  return out.join('');
}

function renderMarkdownBlock(text) {
  if (!text) return '';
  return '<p>' + renderInlineMarkdown(text) + '</p>';
}

// Delegated copy-to-clipboard handler for any rendered code block.
// Guarded so multiple includes of this file do not double-bind.
if (typeof document !== 'undefined' && !document.__hlfCopyHandlerBound) {
  document.__hlfCopyHandlerBound = true;
  document.addEventListener('click', (ev) => {
    const btn = ev.target && ev.target.closest && ev.target.closest('.copy-btn');
    if (!btn) return;
    const text = btn.getAttribute('data-copy') || '';
    const done = () => {
      const prev = btn.textContent;
      btn.classList.add('copied');
      btn.textContent = 'Copied';
      setTimeout(() => {
        btn.classList.remove('copied');
        btn.textContent = prev;
      }, 1200);
    };
    const fallback = () => {
      const code = btn.parentElement && btn.parentElement.querySelector('code');
      if (!code) return;
      const range = document.createRange();
      range.selectNode(code);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(range);
      try { document.execCommand('copy'); done(); } catch (_e) {}
      sel.removeAllRanges();
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  });
}
