export function stripHtml (value: string) {
  const tmp = document.createElement('DIV')
  tmp.innerHTML = value
  return tmp.textContent || tmp.innerText || ''
}
