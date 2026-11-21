export function scrollToElement(id: string, offsetPx = 80): void {
  const el = document.getElementById(id);
  if (!el) return;
  const computeTop = (node: HTMLElement) =>
    Math.max(0, Math.round(node.getBoundingClientRect().top + window.scrollY - offsetPx));
  window.scrollTo({ top: computeTop(el), behavior: 'auto' });
  window.requestAnimationFrame(() => {
    const fresh = document.getElementById(id);
    if (!fresh) return;
    const adjusted = computeTop(fresh);
    if (Math.abs(adjusted - window.scrollY) > 8) {
      window.scrollTo({ top: adjusted, behavior: 'auto' });
    }
  });
}
