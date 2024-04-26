import { getXmlText, IXmlText } from '@/app/snippets/IXmlText'
import { beautifyXml } from '@/app/utils/beautifyXml'

export interface IParsedXmlHints {
  name: string;
  elements: {
    name: 'hint';
    elements: IXmlText[];
  }[];
}

export interface IQuestionHints {
  hints: { text: string }[];
}

export class QuestionHints {
  static createNew () {
    return {
      hints: [],
    }
  }

  static augmentQuestion (question: IQuestionHints, elements: any[]) {
    const hintsEl = elements.find(el => el.name === 'demandhint')
    if (hintsEl) {
      question.hints = hintsEl.elements.map(hintEl => ({ text: getXmlText(hintEl) }))
    } else {
      question.hints = []
    }
  }

  static toXML (json: IQuestionHints) {
    if ((json.hints || []).length) {
      return beautifyXml(`<demandhint>
      ${json.hints.map(h => `<hint><bdi>${h.text}</bdi></hint>`).join('\n')}
  </demandhint>`)
    } else {
      return ''
    }
  }
}
