/* eslint-disable camelcase */
import NumericalInputView from '@/app/questions/numerical-input/NumericalInputView.vue'
import { IParsedXmlTitle, IQuestionTitle, QuestionTitle } from '@/app/snippets/QuestionTitle'
import { IParsedXmlDescription, IQuestionDescription, QuestionDescription } from '@/app/snippets/QuestionDescription'
import { IParsedXmlExplanation, IQuestionExplanation, QuestionExplanation } from '@/app/snippets/QuestionExplanation'
import { IQuestionCorrectFeedback, QuestionCorrectFeedback } from '@/app/snippets/QuestionCorrectFeeback'
import { merge, uniq } from 'lodash'
import { beautifyMarkdown } from '@/app/utils/beautifyMarkdown'
import { IParsedXmlText } from '@/app/questions/text-input/TextInput'
import { getXmlText } from '@/app/snippets/IXmlText'
import { createNewValidationError, IValidationError } from '@/app/snippets/createNewValidationError'
import { IParsedXmlHints, IQuestionHints, QuestionHints } from '@/app/snippets/QuestionHints'
import { QuestionLoncapaPythonScript } from '@/app/components/question/QuestionLoncapaPythonScript'
import { IParsedXmlPythonScript, IPythonScript } from '@/app/components/question/QuestionPythonScript'

interface IFormulaEq {
  name: 'formulaequationinput';
  attributes?: {
    trailing_text?: string;
  };
}

interface IParsedXmlResponseParam {
  name: 'responseparam';
  attributes: {
    type?: 'tolerance';
    default?: string;
    partial_answers?: string;
    partial_range?: string;
  };
}

interface IParsedXmlCorrectHint {
  name: 'correcthint';
  elements: IParsedXmlText[];
}

export interface IParsedXmlNumericalResponse {
  name: string;
  attributes: {
    answer: string;
    partial_credit: string;
  };
  elements: (IParsedXmlTitle | IFormulaEq |IParsedXmlDescription | IParsedXmlCorrectHint | IParsedXmlResponseParam | IParsedXmlExplanation)[];
}

interface INumericalInputAnswer {
  type: 'equal' | 'range';
  value: string;
  rangeFromType: 'gt' | 'gte'
  rangeFrom: string;
  rangeToType: 'lt' | 'lte'
  rangeTo: string;
}

export interface INumericalInput {
  type: string;
  config: IQuestionTitle & IPythonScript & IQuestionDescription & IQuestionExplanation & IQuestionCorrectFeedback & IQuestionHints & {
    answer: INumericalInputAnswer;
    tolerance: string | null;
    additionalAnswers: INumericalInputAnswer[];
    trailingText: string;
    partialCredit: ('close' | 'list')[];
    partialAnswers: string[];
    partialRange: number | null;
  },
}

export class NumericalInput {
  static xmlName = 'numericalresponse'
  static id = 'numerical-input'
  static label = 'Numerical input'
  static view = NumericalInputView
  static makeNew = (partial?): INumericalInput => merge({
    type: NumericalInput.id,
    config: {
      ...QuestionTitle.createNew(),
      ...QuestionDescription.createNew(),
      ...QuestionExplanation.createNew(),
      ...QuestionCorrectFeedback.createNew(),
      ...QuestionHints.createNew(),
      answer: NumericalInput.makeNewAnswer(),
      additionalAnswers: [],
      tolerance: null,
      trailingText: '',
      partialCredit: [],
      partialAnswers: [],
      partialRange: null,
    },
  }, partial)

  static makeNewAnswer = (partial?: Partial<INumericalInputAnswer>): INumericalInputAnswer => merge({
    type: 'equal',
    value: '',
    rangeFromType: 'gt',
    rangeFrom: '',
    rangeToType: 'lt',
    rangeTo: '',
  }, partial)

  static toMarkdown = (question: INumericalInput) => {
    return beautifyMarkdown(`
      ${QuestionTitle.toMarkdown(question.config)}
      =${question.config.answer.value} ${question.config.explanation ? `{{${question.config.explanation}}}` : ''}
      ${question.config.additionalAnswers.map(ans => `or= ${ans.value}`).join('\n')}
    `)
  }

  static validate (question: INumericalInput) {
    const errors = [] as IValidationError[]
    if (!question.config.title) {
      errors.push(createNewValidationError('Title is required'))
    }
    if (question.config.answer == null) {
      errors.push(createNewValidationError('Must have answer'))
    }
    return errors
  }

  static fromParsedXml = (elements: (IParsedXmlNumericalResponse | IParsedXmlPythonScript | IParsedXmlHints)[]) => {
    const numericalInput = NumericalInput.makeNew()
    const numericalInputElement = elements.find(el => el.name === NumericalInput.xmlName) as IParsedXmlNumericalResponse
    QuestionLoncapaPythonScript.augmentQuestion(numericalInput.config, numericalInputElement.elements)
    QuestionHints.augmentQuestion(numericalInput.config, elements)
    numericalInput.config.answer = NumericalInput.makeNewAnswer({
      value: numericalInputElement.attributes.answer,
    })
    if (numericalInputElement.attributes.partial_credit) {
      numericalInput.config.partialCredit = numericalInputElement.attributes.partial_credit.split(',').map(x => x.trim()) as any
    }
    numericalInputElement.elements.forEach(el => {
      switch (el.name) {
        case 'label':
          QuestionTitle.fromParsedXml(numericalInput.config, el)
          break
        case 'description':
          QuestionDescription.fromParsedXml(numericalInput.config, el)
          break
        case 'solution':
          QuestionExplanation.fromParsedXml(numericalInput.config, el)
          break
        case 'correcthint':
          numericalInput.config.feedback = getXmlText(el)
          break
        case 'formulaequationinput':
          if (el.attributes?.trailing_text) {
            numericalInput.config.trailingText = el.attributes?.trailing_text
          }
          break
        case 'responseparam':
          if (el.attributes.type === 'tolerance') {
            if (el.attributes.default) {
              numericalInput.config.tolerance = el.attributes.default
            }
          }
          if (el.attributes.partial_answers) {
            numericalInput.config.partialCredit = uniq([...numericalInput.config.partialCredit, 'list'])
            numericalInput.config.partialAnswers.push(el.attributes.partial_answers)
          }
          if (el.attributes.partial_range) {
            numericalInput.config.partialRange = parseInt(el.attributes.partial_range)
          }
          break
      }
    })
    return numericalInput
  }

  static toXML = (question: INumericalInput) => {
    const makeAnswerValue = (answer: INumericalInputAnswer) => {
      if (answer.type === 'equal') {
        return answer.value
      }
      if (answer.type === 'range') {
        let res = ''
        if (answer.rangeFromType === 'gt') {
          res += '('
        }
        if (answer.rangeFromType === 'gte') {
          res += '['
        }
        res += answer.rangeFrom
        res += ','
        res += answer.rangeTo

        if (answer.rangeToType === 'lt') {
          res += ')'
        }
        if (answer.rangeToType === 'lte') {
          res += ']'
        }
        return res
      }
      throw new Error('Invalid numerical input answer type')
    }

    return `<problem>
    <numericalresponse answer="${makeAnswerValue(question.config.answer)}" ${question.config.partialCredit.length ? `partial_credit="${question.config.partialCredit.join(',')}"` : ''}>
      ${QuestionTitle.toXML(question.config)}
      ${QuestionDescription.toXML(question.config)}
      <responseparam ${question.config.tolerance ? `type="tolerance" default="${question.config.tolerance}"` : ''}
        ${question.config.partialCredit.includes('close') && question.config.partialRange ? `partial_range="${question.config.partialRange}"` : ''}
        ${question.config.partialCredit.includes('list') ? `partial_answers="${question.config.partialAnswers.join(',')}"` : ''} />
${QuestionLoncapaPythonScript.toXML(question.config)}
      <formulaequationinput ${question.config.trailingText ? `trailing_text="${question.config.trailingText}"` : ''} />
      ${question.config.additionalAnswers.map(ans => ans.value ? `<additional_answer answer="${ans.value}"/>` : '').join('\n')}
      ${QuestionCorrectFeedback.toXML(question.config)}
      ${QuestionExplanation.toXML(question.config)}
    </numericalresponse>
    ${QuestionHints.toXML(question.config)}
</problem>`
  }
}
