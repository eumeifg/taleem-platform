export function beautifyMarkdown (markdown) {
  return markdown.replace(/^[ ]\s+/gm, '').trim()
}
