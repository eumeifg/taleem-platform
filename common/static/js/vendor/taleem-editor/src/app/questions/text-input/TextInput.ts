/* eslint-disable camelcase */
import TextInputView from '@/app/questions/text-input/TextInputView.vue'
import shortid from 'shortid'
import { IParsedXmlTitle, IQuestionTitle, QuestionTitle } from '@/app/snippets/QuestionTitle'
import { IParsedXmlDescription, IQuestionDescription, QuestionDescription } from '@/app/snippets/QuestionDescription'
import { IParsedXmlExplanation, IQuestionExplanation, QuestionExplanation } from '@/app/snippets/QuestionExplanation'
import { beautifyXml } from '@/app/utils/beautifyXml'
import { IQuestionCorrectFeedback, QuestionCorrectFeedback } from '@/app/snippets/QuestionCorrectFeeback'
import { beautifyMarkdown } from '@/app/utils/beautifyMarkdown'
import { getXmlText, IXmlText } from '@/app/snippets/IXmlText'
import { createNewValidationError, IValidationError } from '@/app/snippets/createNewValidationError'
import { merge } from 'lodash'
import { IParsedXmlHints, IQuestionHints, QuestionHints } from '@/app/snippets/QuestionHints'

interface IParsedXmlCorrectHint {
  name: 'correcthint';
  elements: IXmlText[];
}

interface IParsedXmlAdditionalAnswer {
  name: 'additional_answer';
  attributes: {
    answer: string;
  };
}

interface IParsedXmlStringEqualHint {
  name: 'stringequalhint';
  attributes: {
    answer: string;
  };
  elements: IXmlText[];
}

interface IParsedXmlTextTextline {
  name: 'textline';
  attributes: {
    size?: string;
    trailing_text?: string;
  };
}

export interface IParsedXmlText {
  name: 'text-input';
  attributes: {
    answer: string;
    type: string;
  };
  elements: (IParsedXmlTitle
    | IParsedXmlDescription
    | IParsedXmlExplanation
    | IParsedXmlCorrectHint
    | IParsedXmlAdditionalAnswer
    | IParsedXmlStringEqualHint
    | IParsedXmlTextTextline)[];
}

export interface IEqualFeedback {
  answer: string;
  feedback: string;
}

export interface ITextInput {
  type: string;
  config: IQuestionTitle
    & IQuestionDescription
    & IQuestionExplanation
    & IQuestionCorrectFeedback
    & IQuestionHints
    & {
    answer: string;
    additionalAnswers: { text: string }[];
    textSize: number | null;
    equalFeedbacks: IEqualFeedback[];
    trailingText: string;
    isCaseSensitive: boolean;
    isRegexp: boolean;
  },
}

export class TextInput {
  static xmlName = 'stringresponse'
  static id = 'text-input'
  static label = 'Text input'
  static view = TextInputView
  static makeNew = (partial?): ITextInput => merge({
    type: TextInput.id,
    config: {
      ...QuestionTitle.createNew(),
      ...QuestionDescription.createNew(),
      ...QuestionExplanation.createNew(),
      ...QuestionCorrectFeedback.createNew(),
      ...QuestionHints.createNew(),
      answer: '',
      additionalAnswers: [],
      textSize: null,
      equalFeedbacks: [],
      trailingText: '',
      isCaseSensitive: false,
      isRegexp: false,
    },
  }, partial)

  static addAdditionalAnswer = (question: ITextInput) => {
    question.config.additionalAnswers.push({ text: '' })
  }

  static addEqFeedback = (question: ITextInput) => {
    question.config.equalFeedbacks.push({
      answer: '',
      feedback: '',
    })
  }

  static validate (question: ITextInput) {
    const errors = [] as IValidationError[]
    if (!question.config.title) {
      errors.push(createNewValidationError('Title is required'))
    }
    if (question.config.answer == null) {
      errors.push(createNewValidationError('Must have answer'))
    }
    return errors
  }

  static fromParsedXml = (elements: (IParsedXmlText | IParsedXmlHints)[]) => {
    const text = TextInput.makeNew()
    QuestionHints.augmentQuestion(text.config, elements)
    const textInputResponse = elements.find(el => el.name === TextInput.xmlName) as IParsedXmlText

    if (textInputResponse.attributes) {
      text.config.answer = textInputResponse.attributes.answer
      text.config.isRegexp = textInputResponse.attributes.type.includes('regexp')
      text.config.isCaseSensitive = textInputResponse.attributes.type.includes('cs')
    }

    textInputResponse.elements.forEach(el => {
      switch (el.name) {
        case 'textline':
          if (el.attributes.size) {
            text.config.textSize = parseInt(el.attributes.size)
          }
          if (el.attributes.trailing_text) {
            text.config.trailingText = el.attributes.trailing_text
          }
          break
        case 'stringequalhint':
          text.config.equalFeedbacks.push({
            answer: el.attributes.answer,
            feedback: getXmlText(el),
          })
          break
        case 'additional_answer':
          text.config.additionalAnswers.push({
            text: el.attributes.answer,
          })
          break
        case 'correcthint':
          text.config.feedback = getXmlText(el)
          break
        case 'label':
          QuestionTitle.fromParsedXml(text.config, el)
          break
        case 'description':
          QuestionDescription.fromParsedXml(text.config, el)
          break
        case 'solution':
          QuestionExplanation.fromParsedXml(text.config, el)
          break
      }
    })
    return text
  }

  static toMarkdown = (question: ITextInput) => {
    return beautifyMarkdown(`
      ${QuestionTitle.toMarkdown(question.config)}
      =${question.config.answer} ${question.config.explanation ? `{{${question.config.explanation}}}` : ''}
      ${question.config.additionalAnswers.map(ans => `or= ${ans.text}`).join('\n')}
      ${QuestionExplanation.toMarkdown(question.config)}
    `)
  }

  static toXML = (question: ITextInput) => {
    return `<problem>
  <stringresponse answer="${question.config.answer}" type="${question.config.isCaseSensitive ? 'cs ' : 'ci '}${question.config.isRegexp ? 'regexp' : ''}">
    ${QuestionTitle.toXML(question.config)}
    ${QuestionDescription.toXML(question.config)}
    ${QuestionCorrectFeedback.toXML(question.config)}
    ${question.config.additionalAnswers.map(ans => `
      <additional_answer answer="${ans.text}" />
    `).join('\n')}
    ${question.config.equalFeedbacks.map(eqf => `
        <stringequalhint answer="${eqf.answer}"><bdi>${eqf.feedback}</bdi></stringequalhint>
      `).join('\n')}
    <textline size="${question.config.textSize}" ${question.config.trailingText ? `trailing_text="${question.config.trailingText}"` : ''}/>
    ${QuestionExplanation.toXML(question.config)}
  </stringresponse>
  ${QuestionHints.toXML(question.config)}
</problem>`
  }

  static makeEqualFeedback = (): IEqualFeedback => {
    return {
      answer: '',
      feedback: '',
    }
  }
}
