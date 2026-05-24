/**
 * Clipboard utility with fallback for Chrome/HTTP contexts.
 * navigator.clipboard requires HTTPS; execCommand fallback works on HTTP.
 */
export async function copyToClipboard(text) {
  if (!text || typeof text !== 'string') return false;
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {}
  }
  try {
    const el = document.createElement('textarea');
    el.value = text;
    el.style.position = 'fixed';
    el.style.left = '-9999px';
    document.body.appendChild(el);
    el.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(el);
    return ok;
  } catch {
    return false;
  }
}
