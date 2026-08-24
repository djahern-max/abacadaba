// A hand-rolled subset, not a dependency - see backend/CLAUDE.md's "justify
// any new dependency" and current-feature.md's "do not add a rich text
// editor." Policy pages are the only thing that renders this: headings,
// paragraphs, unordered lists, bold/italic, and links. Escapes HTML first so
// admin-authored text can never inject markup.
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function renderInline(text) {
  return escapeHtml(text)
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
}

export function renderMarkdown(source) {
  const blocks = source.trim().split(/\n{2,}/)
  return blocks
    .map((block) => {
      const headingMatch = block.match(/^(#{1,3})\s+(.*)$/)
      if (headingMatch) {
        const level = headingMatch[1].length + 1 // start at h2, h1 is the page title
        return `<h${level}>${renderInline(headingMatch[2])}</h${level}>`
      }

      const lines = block.split('\n')
      if (lines.every((line) => /^[-*]\s+/.test(line))) {
        const items = lines.map((line) => `<li>${renderInline(line.replace(/^[-*]\s+/, ''))}</li>`).join('')
        return `<ul>${items}</ul>`
      }

      return `<p>${lines.map(renderInline).join('<br />')}</p>`
    })
    .join('\n')
}
