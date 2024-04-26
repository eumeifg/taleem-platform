import { IXmlText } from '@/app/snippets/IXmlText'
import { stripHtml } from '@/app/utils/stripHtml'
import { jsToXml } from '@/app/utils/jsToXML'
import { decodeHtml } from '@/app/utils/decodeHtml'

export interface IParsedXmlExplanation {
  name: 'solution';
  elements: ({
    name: 'div',
    elements: (IXmlText & {
      name: 'p';
      elements: IXmlText[];
    })[];
  })[];
}

export interface IQuestionExplanation {
  explanation: string;
}
export class QuestionExplanation {
  static createNew (): IQuestionExplanation {
    return {
      explanation: '',
    }
  }

  static fromParsedXml (question: IQuestionExplanation, parsed: IParsedXmlExplanation) {
    question.explanation = jsToXml(parsed)
  }

  static toMarkdown (json: IQuestionExplanation) {
    return json.explanation ? `[explanation]
      ${stripHtml(json.explanation)}
    [explanation]` : ''
  }

  static toXML (json: IQuestionExplanation) {
    return json.explanation ? `<solution>
      ${decodeHtml(json.explanation)}
    </solution>` : ''
  }
}
