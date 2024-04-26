/* eslint-disable camelcase */
import CheckboxesView from '@/app/questions/checkboxes/CheckboxesView.vue'
import shortid from 'shortid'
import { merge } from 'lodash'
import { beautifyXml } from '@/app/utils/beautifyXml'
import { IParsedXmlTitle, IQuestionTitle, QuestionTitle } from '@/app/snippets/QuestionTitle'
import { IParsedXmlDescription, IQuestionDescription, QuestionDescription } from '@/app/snippets/QuestionDescription'
import { IParsedXmlExplanation, IQuestionExplanation, QuestionExplanation } from '@/app/snippets/QuestionExplanation'
import { beautifyMarkdown } from '@/app/utils/beautifyMarkdown'
import { toBool } from '@/app/utils/toBool'
import { getXmlText, IXmlText } from '@/app/snippets/IXmlText'
import { createNewValidationError, IValidationError } from '@/app/snippets/createNewValidationError'
import { IParsedXmlHints, IQuestionHints, QuestionHints } from '@/app/snippets/QuestionHints'
import {
  QuestionPythonScript,
  IParsedXmlPythonScript,
  IPythonScript
} from '@/app/components/question/QuestionPythonScript'

export interface ICheckboxAnswer {
  id: string;
  isCorrect: boolean;
  label: string;
  selectedHint: string;
  notSelectedHint: string;
}

export interface ICheckboxCompoundFeedbackGroup {
  selected: string[];
  label: string;
}
interface XmlChoiceHint {
  name: 'choicehint';
  attributes: {
    selected: 'true' | 'false';
  };
  elements: IXmlText[];
}

interface XmlChoice {
  name: 'choice';
  attributes: { correct: 'true' | 'false' };
  elements: (IXmlText & XmlChoiceHint)[];
}

interface XmlCompoundHint {
  name: 'compoundhint';
  attributes: {
    value: string;
  };
  elements: IXmlText[];
}

interface IParsedXmlCheckboxCheckboxGroup {
  name: 'checkboxgroup';
  elements: (XmlChoice | XmlCompoundHint)[];
}

interface IParsedXmlCheckbox {
  name: string;
  attributes?: {
    partial_credit: string;
  };
  elements: (IParsedXmlTitle | IParsedXmlDescription | IParsedXmlCheckboxCheckboxGroup | IParsedXmlExplanation)[];
}

export interface ICheckbox {
  type: string;
  config: IQuestionTitle & IQuestionDescription & IQuestionExplanation & IQuestionHints & IPythonScript & {
    possibleAnswers: ICheckboxAnswer[];
    compoundFeedbackGroups: ICheckboxCompoundFeedbackGroup[];
    partialCredit: null | string;
  },
}

export class Checkboxes {
  static xmlName = 'choiceresponse'
  static id = 'checkboxes'
  static label = 'Checkboxes'
  static view = CheckboxesView
  static withScript = true

  static makeNew = (partial?): ICheckbox => merge({
    type: Checkboxes.id,
    config: {
      ...QuestionTitle.createNew(),
      ...QuestionDescription.createNew(),
      ...QuestionExplanation.createNew(),
      ...QuestionHints.createNew(),
      ...QuestionPythonScript.createNew(),
      hasCustomScript: false,
      script: '',
      possibleAnswers: [],
      compoundFeedbackGroups: [],
      partialCredit: null,
    },
  }, partial)

  static getIdByAnswerLetter (question: ICheckbox, letter: string) {
    const index = letter.charCodeAt(0) - 'A'.charCodeAt(0)
    return question.config.possibleAnswers[index].id
  }

  static getAnswerLetterById (questionConfig, answerId: string) {
    const index = questionConfig.possibleAnswers.findIndex(_ans => _ans.id === answerId)
    if (index === -1) {
      console.error('Checkbox: Invalid answer')
      throw new Error('123')
    }
    return String.fromCharCode(index + 'A'.charCodeAt(0))
  }

  static validate (question: ICheckbox) {
    const errors = [] as IValidationError[]
    if (!question.config.title) {
      errors.push(createNewValidationError('Title is required'))
    }
    if (question.config.possibleAnswers.length < 2) {
      errors.push(createNewValidationError('Must have at least 2 answers'))
    }
    if (question.config.possibleAnswers.some(ans => !ans.label)) {
      errors.push(createNewValidationError('Answers cannot be empty'))
    }
    return errors
  }

  static fromParsedXml = (elements: (IParsedXmlCheckbox | IParsedXmlPythonScript | IParsedXmlHints)[]) => {
    const checkbox = Checkboxes.makeNew()
    const checkboxXml = elements.find(el => el.name === 'choiceresponse')! as IParsedXmlCheckbox

    QuestionHints.augmentQuestion(checkbox.config, elements)
    QuestionPythonScript.augmentQuestion(checkbox.config, elements)

    if (checkboxXml.attributes?.partial_credit) {
      checkbox.config.partialCredit = checkboxXml.attributes?.partial_credit
    }

    checkboxXml.elements.forEach(el => {
      switch (el.name) {
        case 'label':
          QuestionTitle.fromParsedXml(checkbox.config, el)
          break
        case 'description':
          QuestionDescription.fromParsedXml(checkbox.config, el)
          break
        case 'solution':
          QuestionExplanation.fromParsedXml(checkbox.config, el)
          break
        case 'checkboxgroup':
          el.elements.forEach(checkboxGroupEl => {
            switch (checkboxGroupEl.name) {
              case 'choice':
                checkbox.config.possibleAnswers.push(Checkboxes.makeNewAnswer({
                  label: getXmlText(checkboxGroupEl),
                  isCorrect: toBool(checkboxGroupEl.attributes.correct),
                  selectedHint: getXmlText(checkboxGroupEl.elements.find(el => el.name === 'choicehint' && el.attributes.selected === 'true') as any) || undefined,
                  notSelectedHint: getXmlText(checkboxGroupEl.elements.find(el => el.name === 'choicehint' && el.attributes.selected === 'false') as any) || undefined,
                }))
                break
              case 'compoundhint':
                checkbox.config.compoundFeedbackGroups.push(({
                  selected: checkboxGroupEl.attributes.value.split(' ').map(x => x.trim()).map(answerLetter => Checkboxes.getIdByAnswerLetter(checkbox, answerLetter)),
                  label: getXmlText(checkboxGroupEl),
                }))
                break
            }
          })
          break
      }
    })
    return checkbox
  }

  static toMarkdown = (question: ICheckbox) => {
    const makeHints = (ans) => {
      const arr = [ans.selectedHint ? `{ selected: ${ans.selectedHint} }` : '',
        ans.notSelectedHint ? `{ unselected: ${ans.notSelectedHint} }` : ''].filter(x => x)
      if (!arr.length) {
        return ''
      }
      return `{${arr.join(',')}}`
    }

    return beautifyMarkdown(`
      ${QuestionTitle.toMarkdown(question.config)}
      ${question.config.possibleAnswers.map(ans => `[${ans.isCorrect ? 'x' : ' '}] ${ans.label} ${makeHints(ans)}`).join('\n')}
      
      ${QuestionExplanation.toMarkdown(question.config)}
    `)
  }

  static toXML = (question: ICheckbox) => {
    return `<problem>
  ${QuestionPythonScript.toXML(question.config)}
  <choiceresponse ${question.config.partialCredit ? `partial_credit="${question.config.partialCredit}"` : ''}>
    ${QuestionTitle.toXML(question.config)}
    ${QuestionDescription.toXML(question.config)}
    <checkboxgroup>
      ${question.config.possibleAnswers.map(ans => `
        <choice correct="${ans.isCorrect.toString()}"><bdi>${ans.label}</bdi>
          ${ans.selectedHint ? `<choicehint selected="true"><bdi>${ans.selectedHint}</bdi></choicehint>` : ''}
          ${ans.notSelectedHint ? `<choicehint selected="false"><bdi>${ans.notSelectedHint}</bdi></choicehint>` : ''}
        </choice>
      `).join('')}
      ${question.config.compoundFeedbackGroups.filter(group => group.selected.length).map(cfg => `
          <compoundhint value="${cfg.selected.map(id => Checkboxes.getAnswerLetterById(question.config, id)).sort().join(' ')}"><bdi>${cfg.label}</bdi></compoundhint>
        `)}
    </checkboxgroup>
    ${QuestionExplanation.toXML(question.config)}
  </choiceresponse>
  ${QuestionHints.toXML(question.config)}
</problem>`
  }

  static makeNewAnswer = (partial?): ICheckboxAnswer => merge({
    id: shortid.generate(),
    isCorrect: false,
    label: '',
    selectedHint: '',
    notSelectedHint: '',
  }, partial)

  static makeNewCompoundFeedbackGroup = (): ICheckboxCompoundFeedbackGroup => ({
    selected: [],
    label: '',
  })
}
