import { beautifyXml } from '@/app/utils/beautifyXml'

export interface IParsedXmlPythonScript {
  name: string;
  elements: {
    type: 'cdata';
    cdata: string;
  }[];
}

export interface IPythonScript {
  hasCustomScript: boolean;
  script: string;
}

export class QuestionPythonScript {
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
      question.script = scriptEl.elements.find(el => el.type === 'cdata')!.cdata.trim()
    } else {
      question.hasCustomScript = false
      question.script = ''
    }
  }

  static toXML (json: IPythonScript) {
    if (json.script) {
      return beautifyXml(`<script type="text/python">
  <![CDATA[
  ${json.script}
  ]]>
  </script>`)
    } else {
      return ''
    }
  }
}
