import convert from 'xml-js'

export function jsToXml (js) {
  return convert.js2xml(js, {
    fullTagEmptyElementFn: (tag) => {
      if (tag === 'bdi') {
        return true
      }
      return false
    },
  }).trim()
}
