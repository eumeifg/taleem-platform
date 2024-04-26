import DropdownView from '@/app/questions/dropdown/DropdownView.vue'
import shortid from 'shortid'
import { merge } from 'lodash'
import { IParsedXmlExplanation, IQuestionExplanation, QuestionExplanation } from '@/app/snippets/QuestionExplanation'
import { capitalize } from '@/app/utils/capitalize'
import { IParsedXmlTitle, IQuestionTitle, QuestionTitle } from '@/app/snippets/QuestionTitle'
import { IParsedXmlDescription, IQuestionDescription, QuestionDescription } from '@/app/snippets/QuestionDescription'
import { beautifyMarkdown } from '@/app/utils/beautifyMarkdown'
import { getXmlText, IXmlText } from '@/app/snippets/IXmlText'
import { createNewValidationError, IValidationError } from '@/app/snippets/createNewValidationError'
import { IParsedXmlHints, IQuestionHints, QuestionHints } from '@/app/snippets/QuestionHints'

interface IXmlOptionInputOptionHint {
  name: 'optionhint';
  elements: IXmlText[];
}

interface IXmlOptionInputOption {
  name: 'option';
  attributes: {
    correct: string;
  };
  elements: (IXmlOptionInputOptionHint & IXmlText)[];
}

interface IXmlOptionInput {
  name: 'optioninput';
  attributes?: {
    options?: string;
    correct?: string;
  };
  elements?: IXmlOptionInputOption[];
}

interface IParsedXmlDropdown {
  name: 'optionresponse';
  elements: (IParsedXmlTitle | IParsedXmlDescription | IParsedXmlExplanation | IXmlOptionInput)[];
}

interface IDropdownQuestionOption {
  id: string;
  text: string;
  hint: string;
  isCorrect: boolean;
}

export interface IDropdownQuestion extends IQuestionTitle, IQuestionDescription, IQuestionExplanation {
  options: IDropdownQuestionOption[];
}

export interface IDropdown {
  id: string;
  type: string;
  config: IQuestionHints & {
    dropdowns: IDropdownQuestion[];
  },
}

export class Dropdown {
  static xmlName = 'optionresponse'
  static id = 'dropdown'
  static label = 'Dropdown'
  static view = DropdownView

  static makeNew = (partial?): IDropdown => merge({
    type: Dropdown.id,
    config: {
      ...QuestionHints.createNew(),
      dropdowns: [],
    },
  }, partial)

  static fromParsedXml = (elements: (IParsedXmlDropdown | IParsedXmlHints)[]) => {
    const dropdown = Dropdown.makeNew()
    QuestionHints.augmentQuestion(dropdown.config, elements)
    const allDropdowns = elements.filter(element => element.name === Dropdown.xmlName) as IParsedXmlDropdown[]
    const dropdownItems = allDropdowns.map(dropdown => {
      const newDropdownItem = Dropdown.makeNewDropdownQuestion()
      dropdown.elements.forEach(el => {
        switch (el.name) {
          case 'label':
            QuestionTitle.fromParsedXml(newDropdownItem, el)
            break
          case 'description':
            QuestionDescription.fromParsedXml(newDropdownItem, el)
            break
          case 'solution':
            QuestionExplanation.fromParsedXml(newDropdownItem, el)
            break
          case 'optioninput':
            if (el.attributes) {
              if (el.attributes.options) {
                el.attributes.options.match(/'(\w+)'/g)!.map(val => val.replace(/'/g, '')).forEach(opt => {
                  newDropdownItem.options.push({
                    id: shortid.generate(),
                    text: opt,
                    isCorrect: el.attributes?.correct ? el.attributes?.correct === opt : false,
                    hint: '',
                  })
                })
              }
            } else if (el.elements) {
              el.elements.forEach(inputEl => {
                if (inputEl.name === 'option') {
                  newDropdownItem.options.push({
                    id: shortid.generate(),
                    text: getXmlText(inputEl),
                    isCorrect: inputEl.attributes?.correct?.toLowerCase() === 'true',
                    hint: getXmlText(inputEl.elements?.find(x => x.name === 'optionhint')),
                  })
                }
              })
            }
            break
        }
      })
      return newDropdownItem
    })
    dropdown.config.dropdowns = dropdownItems
    return dropdown
  }

  static toMarkdown = (question: IDropdown) => {
    const optionMarkdown = (option: IDropdownQuestionOption) => {
      if (option.isCorrect) {
        return `(${option.text})`
      }
      return option.text
    }

    return beautifyMarkdown(`
     ${question.config.dropdowns.map(singleDropdown => `
        ${QuestionTitle.toMarkdown(singleDropdown)}
        [[
        ${singleDropdown.options.map(opt => optionMarkdown(opt)).join('\n')}
        ]]
        ${QuestionExplanation.toMarkdown(singleDropdown)}
     `).join('\n---\n')}
    `)
  }

  static validate (question: IDropdown) {
    const errors = [] as IValidationError[]

    question.config.dropdowns.forEach(dropdown => {
      if (!dropdown.title) {
        errors.push(createNewValidationError('Title is required'))
      }
      if (dropdown.options.length < 2) {
        errors.push(createNewValidationError('Must have at least 2 options'))
      }
      if (dropdown.options.some(ans => !ans.text)) {
        errors.push(createNewValidationError('Options cannot be empty'))
      }
      if (dropdown.options.every(ans => ans.isCorrect === false)) {
        errors.push(createNewValidationError('One option must be correct'))
      }
    })
    return errors
  }

  static toXML = (question: IDropdown) => {
    return `<problem>
 ${question.config.dropdowns.map(singleDropdown => `<optionresponse>
    ${QuestionTitle.toXML(singleDropdown)}
    ${QuestionDescription.toXML(singleDropdown)}
    <optioninput>
      ${singleDropdown.options.map(opt => `
        <option correct="${capitalize(opt.isCorrect.toString())}">${opt.text}
          ${opt.hint ? `
            <optionhint>
              <bdi>
                ${opt.hint}
              </bdi>
            </optionhint>
          ` : ''}
        </option>
      `).join('\n')}
    </optioninput>
    ${QuestionExplanation.toXML(singleDropdown)}
  </optionresponse>`).join('\n')}
  ${QuestionHints.toXML(question.config)}
</problem>`
  }

  static makeNewDropdownQuestion = (partial?: Partial<IDropdownQuestion>): IDropdownQuestion => merge({
    id: shortid.generate(),
    ...QuestionTitle.createNew(),
    ...QuestionDescription.createNew(),
    ...QuestionExplanation.createNew(),
    options: [],
  } as IDropdownQuestion, partial)

  static makeNewDropdownQuestionOption = (partial?: Partial<IDropdownQuestionOption>): IDropdownQuestionOption => merge({
    id: shortid.generate(),
    text: '',
    hintTitle: '',
    isCorrect: false,
    hint: '',
  } as IDropdownQuestionOption, partial)

  static addNewOption (question: IDropdownQuestion) {
    question.options = [...question.options, this.makeNewDropdownQuestionOption()]
  }
}
