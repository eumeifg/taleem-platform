import { IQuestionDescription } from '@/app/snippets/QuestionDescription'
import { getXmlText, IXmlText } from '@/app/snippets/IXmlText'
import { stripHtml } from '@/app/utils/stripHtml'
import { jsToXml } from '@/app/utils/jsToXML'

export interface IParsedXmlTitle {
  name: 'label';
  elements: IXmlText[];
}

export interface IQuestionTitle {
  title: string;
}
export class QuestionTitle {
  static createNew (): IQuestionTitle {
    return {
      title: '',
    }
  }

  static fromParsedXml (question: IQuestionTitle, parsed: IParsedXmlTitle) {
    question.title = getXmlText(parsed)
  }

  static toMarkdown (json: IQuestionTitle & IQuestionDescription) {
    return `>>${stripHtml(json.title)}${json.description ? `||${stripHtml(json.description)}` : ''}<<`
  }

  static toXML (json: IQuestionTitle) {
    return `<label><bdi>${json.title}</bdi></label>`
  }
}
