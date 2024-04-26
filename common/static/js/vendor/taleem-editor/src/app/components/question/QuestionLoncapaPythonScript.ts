import { getXmlText, IXmlText } from '@/app/snippets/IXmlText'
import { IPythonScript } from '@/app/components/question/QuestionPythonScript'

export interface IParsedLoncapaXmlPythonScript {
  name: string;
  elements: IXmlText[];
}

export class QuestionLoncapaPythonScript {
  static createNew () {
    return {
      hasCustomScript: false,
      script: '',
    }
  }

  static augmentQuestion (question: IPythonScript, elements: any[]) {
    const scriptEl = elements.find(el => el.name === 'script')
    if (scriptEl) {
      question.hasCustomScript = true
      question.script = getXmlText(scriptEl).trim()
    } else {
      question.hasCustomScript = false
      question.script = ''
    }
  }

  static toXML (json: IPythonScript) {
    if (json.script) {
      return `<script type="loncapa/python">
${json.script}
</script>`
    } else {
      return ''
    }
  }
}
