export function decodeHtml (encodedhtml) {
  return encodedhtml.replace(/&lt;/g, '<').replace(/&gt;/g, '>')
}
