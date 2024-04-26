export interface IQuestionCorrectFeedback {
  feedback: string;
}
export class QuestionCorrectFeedback {
  static createNew (): IQuestionCorrectFeedback {
    return {
      feedback: '',
    }
  }

  static toMarkdown (json: IQuestionCorrectFeedback) {
    return ''
  }

  static toXML (json: IQuestionCorrectFeedback) {
    if (!json.feedback) {
      return ''
    }
    return `<correcthint><bdi>${json.feedback}</bdi></correcthint>`
  }

  static accessControl () {
    return []
  }
}
