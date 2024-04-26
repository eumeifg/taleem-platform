import { merge } from 'lodash'
import { IParsedXmlExplanation, IQuestionExplanation, QuestionExplanation } from '@/app/snippets/QuestionExplanation'
import { IParsedXmlTitle, IQuestionTitle, QuestionTitle } from '@/app/snippets/QuestionTitle'
import { IParsedXmlDescription, IQuestionDescription, QuestionDescription } from '@/app/snippets/QuestionDescription'
import { getXmlText, IXmlText } from '@/app/snippets/IXmlText'
import { createNewValidationError, IValidationError } from '@/app/snippets/createNewValidationError'
import MathExpressionView from './MathExpressionView.vue'
import { IParsedXmlHints, IQuestionHints, QuestionHints } from '@/app/snippets/QuestionHints'
import {
  IParsedLoncapaXmlPythonScript,
  QuestionLoncapaPythonScript
} from '@/app/components/question/QuestionLoncapaPythonScript'
import { IPythonScript } from '@/app/components/question/QuestionPythonScript'

interface Iformulaequationinput {
  name: 'formulaequationinput';
  attributes: {
    size: string;
  };
}

interface IResponseParam {
  name: 'responseparam';
  attributes: {
    type: string;
    default: string;
  };
}

interface IMathExpressionScript {
  name: 'script';
  elements: IXmlText[];
}

interface IParsedMathExpressionsXml {
  name: 'formularesponse';
  attributes: {
    type: 'cs' | 'ci';
    answer: string;
    samples: string;
  }
  elements: (IParsedXmlTitle | IParsedXmlDescription | IParsedXmlExplanation | Iformulaequationinput | IResponseParam | IMathExpressionScript)[];
}

export interface IMathExpression {
  type: string;
  config: IQuestionTitle & IQuestionDescription & IPythonScript & IQuestionHints & IQuestionExplanation & {
    isCaseSensitive: boolean;
    tolerance: string;
    answer: string;
    size: number | null;
    script: string;
    samples: string;
  },
}

export class MathExpression {
  static xmlName = 'formularesponse'
  static id = 'math-expression'
  static label = 'MathExpression'
  static view = MathExpressionView

  static makeNew = (partial?): IMathExpression => merge({
    type: MathExpression.id,
    config: {
      ...QuestionTitle.createNew(),
      ...QuestionDescription.createNew(),
      ...QuestionExplanation.createNew(),
      ...QuestionHints.createNew(),
      tolerance: '1%',
      script: '',
      size: null,
      samples: '',
      answer: '',
      isCaseSensitive: false,
    },
  }, partial)

  static fromParsedXml = (elements: (IParsedMathExpressionsXml | IParsedLoncapaXmlPythonScript | IParsedXmlHints)[]) => {
    const mathExpression = MathExpression.makeNew()
    QuestionHints.augmentQuestion(mathExpression.config, elements)
    const mathExpressionElement = elements.find(el => el.name === MathExpression.xmlName)! as IParsedMathExpressionsXml
    mathExpression.config.isCaseSensitive = mathExpressionElement.attributes.type === 'cs'
    mathExpression.config.samples = mathExpressionElement.attributes.samples
    mathExpression.config.answer = mathExpressionElement.attributes.answer
    mathExpressionElement.elements.forEach(el => {
      switch (el.name) {
        case 'label':
          QuestionTitle.fromParsedXml(mathExpression.config, el)
          break
        case 'description':
          QuestionDescription.fromParsedXml(mathExpression.config, el)
          break
        case 'solution':
          QuestionExplanation.fromParsedXml(mathExpression.config, el)
          break
        case 'script':
          mathExpression.config.script = getXmlText(el).trim()
          break
        case 'formulaequationinput':
          mathExpression.config.size = parseInt(el.attributes.size)
          break
        case 'responseparam':
          mathExpression.config.tolerance = el.attributes.default
      }
    })
    return mathExpression
  }

  static toMarkdown = (question: IMathExpression) => {
    return ''
  }

  static validate (question: IMathExpression) {
    const errors = [] as IValidationError[]
    if (!question.config.title) {
      errors.push(createNewValidationError('Title is required'))
    }
    if (!question.config.samples) {
      errors.push(createNewValidationError('Samples required'))
    }
    if (!question.config.answer) {
      errors.push(createNewValidationError('Answer required'))
    }
    return errors
  }

  static toXML = (mathExpression: IMathExpression) => {
    return `<problem>
  <formularesponse type="${mathExpression.config.isCaseSensitive ? 'cs' : 'ci'}" samples="${mathExpression.config.samples}" answer="${mathExpression.config.answer}">
    ${QuestionTitle.toXML(mathExpression.config)}
    ${QuestionDescription.toXML(mathExpression.config)}
    <responseparam type="tolerance" default="${mathExpression.config.tolerance}" />
    <formulaequationinput ${mathExpression.config.size ? `size="${mathExpression.config.size}"` : ''}/>
    ${QuestionLoncapaPythonScript.toXML(mathExpression.config)}
    ${QuestionExplanation.toXML(mathExpression.config)}
  </formularesponse>
</problem>`
  }
}
