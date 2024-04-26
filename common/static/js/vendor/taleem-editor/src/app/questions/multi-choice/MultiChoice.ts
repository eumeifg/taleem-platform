/* eslint-disable camelcase */
import DropdownView from '@/app/questions/multi-choice/MultiChoiceView.vue'
import { merge } from 'lodash'
import { IParsedXmlExplanation, IQuestionExplanation, QuestionExplanation } from '@/app/snippets/QuestionExplanation'
import { IParsedXmlTitle, IQuestionTitle, QuestionTitle } from '@/app/snippets/QuestionTitle'
import { IParsedXmlDescription, IQuestionDescription, QuestionDescription } from '@/app/snippets/QuestionDescription'
import { beautifyMarkdown } from '@/app/utils/beautifyMarkdown'
import { getXmlText, IXmlText } from '@/app/snippets/IXmlText'
import { createNewValidationError, IValidationError } from '@/app/snippets/createNewValidationError'
import { IParsedXmlHints, IQuestionHints, QuestionHints } from '@/app/snippets/QuestionHints'
import shortid from 'shortid'
import {
  IParsedXmlPythonScript,
  IPythonScript,
  QuestionPythonScript,
} from '@/app/components/question/QuestionPythonScript'
import { jsToXml } from '@/app/utils/jsToXML'

interface ChoiceHint {
  name: 'choicehint';
  elements: IXmlText[];
}

interface Choice {
  name: 'choice';
  attributes: {
    name: string;
    correct: 'true' | 'false' | 'partial';
    point_value: string;
  };
  elements: (ChoiceHint & IXmlText)[];
}

interface ChoiceGroup {
  name: 'choicegroup';
  elements: Choice[];
}

interface IParsedXmlMultiChoice {
  name: 'multiplechoiceresponse';
  attributes?: {
    partial_credit: 'points';
  };
  elements: (IParsedXmlTitle | IParsedXmlDescription | ChoiceGroup | IParsedXmlExplanation)[];
}

export interface IMultiChoiceOption {
  correct: 'true' | 'false' | 'partial';
  id: string;
  label: string;
  name: string;
  hint: string;
}

export interface IMultiChoice {
  type: string;
  config: IQuestionTitle & IPythonScript & IQuestionDescription & IQuestionExplanation & IQuestionHints & {
    options: IMultiChoiceOption[];
    partialCredit: null | 'points';
    isShuffled: boolean;
  },
}

export class MultiChoice {
  static xmlName = 'multiplechoiceresponse'
  static id = 'multi-choice'
  static label = 'Multi Choice'
  static view = DropdownView

  static makeNew = (partial?): IMultiChoice => merge({
    type: MultiChoice.id,
    config: {
      ...QuestionTitle.createNew(),
      ...QuestionDescription.createNew(),
      ...QuestionExplanation.createNew(),
      ...QuestionHints.createNew(),
      ...QuestionPythonScript.createNew(),
      options: [],
      partialCredit: null,
      isShuffled: false,
    },
  }, partial)

  static toMarkdown = (question: IMultiChoice) => {
    return beautifyMarkdown(`
      ${QuestionTitle.toMarkdown(question.config)}
      ${question.config.options.map((opt, index) => `(${opt.correct === 'true' ? 'x' : ' '}${index === 0 && question.config.isShuffled ? '!' : ''}) ${opt.label}`).join('\n')}
      ${QuestionExplanation.toMarkdown(question.config)}
    `)
  }

  static validate (question: IMultiChoice) {
    const errors = [] as IValidationError[]
    if (!question.config.title) {
      errors.push(createNewValidationError('Title is required'))
    }
    if (question.config.options.length < 2) {
      errors.push(createNewValidationError('Must have at least 2 choices'))
    }
    if (question.config.options.some(ans => !ans.label)) {
      errors.push(createNewValidationError('Choice cannot be empty'))
    }
    return errors
  }

  static fromParsedXml = (elements: (IParsedXmlMultiChoice | IParsedXmlPythonScript | IParsedXmlHints)[]) => {
    const multiChoice = MultiChoice.makeNew()
    const multiChoiceEl = elements.find(el => el.name === 'multiplechoiceresponse') as IParsedXmlMultiChoice

    QuestionHints.augmentQuestion(multiChoice.config, elements)
    if (multiChoiceEl.attributes?.partial_credit === 'points') {
      multiChoice.config.partialCredit = 'points'
    }

    multiChoiceEl.elements.forEach(el => {
      switch (el.name) {
        case 'label':
          QuestionTitle.fromParsedXml(multiChoice.config, el)
          break
        case 'description':
          QuestionDescription.fromParsedXml(multiChoice.config, el)
          break
        case 'solution':
          QuestionExplanation.fromParsedXml(multiChoice.config, el)
          break
        case 'choicegroup':
          el.elements.forEach(choice => {
            if (choice.name === 'choice') {
              multiChoice.config.options.push(MultiChoice.makeNewOption({
                correct: choice.attributes.correct,
                label: `${getXmlText(choice)}`,
                name: choice.attributes.name,
                hint: `${getXmlText(choice.elements.find(el => el.name === 'choicehint'))}`,
              }))
            }
          })
          break
      }
    })
    return multiChoice
  }

  static toXML = (question: IMultiChoice) => {
    return `<problem>
  ${QuestionPythonScript.toXML(question.config)}
  <multiplechoiceresponse>
    ${QuestionTitle.toXML(question.config)}
    ${QuestionDescription.toXML(question.config)}
    <choicegroup type="MultipleChoice" ${question.config.isShuffled ? 'shuffle="true"' : ''}>
      ${question.config.options.map(opt => `
        <choice correct="${opt.correct.toString()}" name="${opt.name}"><bdi>${opt.label}</bdi>
        ${opt.hint ? `\n<choicehint><bdi>${opt.hint}</bdi></choicehint>\n` : ''}
        </choice>
      `).join('\n')}
    </choicegroup>
    ${QuestionExplanation.toXML(question.config)}
  </multiplechoiceresponse>
  ${QuestionHints.toXML(question.config)}
</problem>`
  }

  static makeNewOption = (partial?: Partial<IMultiChoiceOption>): IMultiChoiceOption => merge({
    id: shortid.generate(),
    correct: 'false',
    label: '',
    name: shortid.generate(),
    hint: '',
  } as IMultiChoiceOption, partial)
}
