import React, { useMemo } from 'react';
import katex from 'katex';

interface MathTextProps {
  text: string;
  inline?: boolean;
  className?: string;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderInlineSegments(line: string): string {
  const mathTokens: string[] = [];
  const withPlaceholders = line.replace(/\$([^$\n]+?)\$/g, (_, rawTex: string) => {
    const tex = rawTex.trim();
    let rendered: string;
    try {
      rendered = katex.renderToString(tex, {
        displayMode: false,
        throwOnError: false,
        strict: false,
      });
    } catch {
      rendered = `<code>${escapeHtml(tex)}</code>`;
    }
    const idx = mathTokens.length;
    mathTokens.push(rendered);
    return `\uE000MATH${idx}\uE001`;
  });

  let out = escapeHtml(withPlaceholders);
  // Highlight fill-in-the-blank underscores strictly outside math
  out = out.replace(/_{6,}/g, '<span class="blank-line">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>');
  // Render inline code and bold formatting
  out = out.replace(/`([^`\n]+?)`/g, '<code class="math-inline-code">$1</code>');
  out = out.replace(/\*\*([^\n]+?)\*\*/g, '<strong>$1</strong>');
  // Restore KaTeX HTML tokens
  out = out.replace(/\uE000MATH(\d+)\uE001/g, (_, idxStr: string) => mathTokens[Number(idxStr)] ?? '');
  return out;
}

function renderTextParagraph(para: string): string {
  const lines = para
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);
  if (lines.length === 0) return '';

  const blocks: Array<{ kind: 'list' | 'para'; lines: string[] }> = [];
  for (const line of lines) {
    const bulletMatch = line.match(/^[-•]\s+(.*)$/);
    if (bulletMatch) {
      const prev = blocks[blocks.length - 1];
      if (prev && prev.kind === 'list') {
        prev.lines.push(bulletMatch[1]);
      } else {
        blocks.push({ kind: 'list', lines: [bulletMatch[1]] });
      }
    } else {
      const prev = blocks[blocks.length - 1];
      if (prev && prev.kind === 'para') {
        prev.lines.push(line);
      } else {
        blocks.push({ kind: 'para', lines: [line] });
      }
    }
  }

  return blocks
    .map((blk) => {
      if (blk.kind === 'list') {
        return `<ul class="math-list">${blk.lines.map((l) => `<li>${renderInlineSegments(l)}</li>`).join('')}</ul>`;
      }
      return `<p class="math-para">${blk.lines.map((l) => renderInlineSegments(l)).join('<br />')}</p>`;
    })
    .join('');
}

export const MathText: React.FC<MathTextProps> = ({ text, inline = false, className = '' }) => {
  const html = useMemo(() => {
    if (!text) return '';
    if (inline) {
      const normalized = text
        .replace(/\$\$([\s\S]*?)\$\$/g, (_, inner: string) => `$${inner.trim().replace(/\s*\n\s*/g, ' ')}$`)
        .replace(/\s*\n+\s*/g, ' ');
      return renderInlineSegments(normalized);
    }

    // Split out display math blocks $$...$$ first
    const blockRegex = /\$\$([\s\S]*?)\$\$/g;
    const segments: Array<{ type: 'text' | 'display'; content: string }> = [];
    let last = 0;
    let m: RegExpExecArray | null;

    while ((m = blockRegex.exec(text)) !== null) {
      if (m.index > last) {
        segments.push({ type: 'text', content: text.slice(last, m.index) });
      }
      segments.push({ type: 'display', content: m[1].trim() });
      last = blockRegex.lastIndex;
    }
    if (last < text.length) {
      segments.push({ type: 'text', content: text.slice(last) });
    }

    return segments
      .map((seg) => {
        if (seg.type === 'display') {
          try {
            const rendered = katex.renderToString(seg.content, {
              displayMode: true,
              throwOnError: false,
              strict: false,
            });
            return `<div class="math-display-scroll">${rendered}</div>`;
          } catch {
            return `<pre class="math-fallback">${escapeHtml(seg.content)}</pre>`;
          }
        }
        const paras = seg.content
          .split(/\n{2,}/)
          .map((p) => p.trim())
          .filter(Boolean);
        return paras.map((p) => renderTextParagraph(p)).join('');
      })
      .join('');
  }, [text, inline]);

  if (inline) {
    return <span className={`math-inline ${className}`} dangerouslySetInnerHTML={{ __html: html }} />;
  }
  return <div className={`math-rich ${className}`} dangerouslySetInnerHTML={{ __html: html }} />;
};

export const KaTeXFormula: React.FC<{ latex: string; display?: boolean; className?: string }> = ({
  latex,
  display = true,
  className = '',
}) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(latex, {
        displayMode: display,
        throwOnError: false,
        strict: false,
      });
    } catch {
      return latex;
    }
  }, [latex, display]);

  return (
    <div
      className={`math-display-scroll ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
