export interface IXmlText {
  type: 'text'
  text: string;
}

export function getXmlText (config?: { text?: string; elements: (IXmlText | any)[]; }) {
  if (!config || (!config.elements && !config.text)) {
    return ''
  }
  if (config.text) {
    return config.text
  }
  if (config.elements.find(el => el.name === 'bdi')) {
    return getXmlText(config.elements.find(el => el.name === 'bdi'))
  }
  return ((config.elements.find(el => el.type === 'text') || {}).text || '').trim()
}
