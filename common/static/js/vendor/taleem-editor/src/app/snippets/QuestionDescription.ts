import { IXmlText } from '@/app/snippets/IXmlText'
import { jsToXml } from '@/app/utils/jsToXML'
import { decodeHtml } from '@/app/utils/decodeHtml'

export interface IParsedXmlDescription {
  name: 'description';
  elements: IXmlText[];
}

export interface IQuestionDescription {
  description: string;
}

export class QuestionDescription {
  static createNew (): IQuestionDescription {
    return {
      description: '',
    }
  }

  static fromParsedXml (question: IQuestionDescription, parsed: IParsedXmlDescription) {
    question.description = jsToXml(parsed)
  }

  static toXML (json: IQuestionDescription) {
    return json.description ? `<description>${decodeHtml(json.description)}</description>` : '<description></description>'
  }

  static accessControl () {
    return []
  }
}
