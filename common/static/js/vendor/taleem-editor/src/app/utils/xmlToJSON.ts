import xmlJs from 'xml-js'
import { xmlNameMap } from '@/app/questions/questions'

export function xmlToJSON (xml: string) {
  if (!xml || typeof xml !== 'string') {
    throw new Error('Must be valid string')
  }
  const converted = xmlJs.xml2js(xml, { compact: false, alwaysChildren: true }) as any
  const allElements = converted.elements[0].elements
  const questionComponent = Object.values(xmlNameMap).find((component: any) => {
    return allElements.map(el => el.name).includes(component.xmlName)
  }) as any
  if (questionComponent) {
    return questionComponent.fromParsedXml(allElements)
  } else {
    throw new Error('Question type is not supported')
  }
}
