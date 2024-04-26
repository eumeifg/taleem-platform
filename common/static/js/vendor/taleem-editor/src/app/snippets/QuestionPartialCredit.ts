export interface IParsedXmlPartialCredit {
  _attributes?: {
    'partial_credit': string;
  };
}

export interface IQuestionPartialCredit {
  partialCredit: string;
}
export class QuestionPartialCredit {
  static createNew (): IQuestionPartialCredit {
    return {
      partialCredit: '',
    }
  }

  static fromParsedXml (question: IQuestionPartialCredit, parsed: IParsedXmlPartialCredit) {
    if (parsed._attributes?.partial_credit) {
      question.partialCredit = parsed._attributes?.partial_credit
    }
  }

  static toMarkdown (json: IQuestionPartialCredit) {
    throw new Error('Cannot be implemented here')
  }

  static toXML (json: IQuestionPartialCredit) {
    if (!json.partialCredit) {
      return ''
    }
    return `partial_credit="${json.partialCredit}"`
  }
}
