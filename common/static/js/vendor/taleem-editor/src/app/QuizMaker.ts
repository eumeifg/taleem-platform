import Vue from 'vue'
import QuizMakerView from './QuizMakerView.vue'
import store from './store'
import { questions } from '@/app/questions/questions'
import { BootstrapVue, IconsPlugin } from 'bootstrap-vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import '../assets/__generated.css'
import { xmlToJSON } from '@/app/utils/xmlToJSON'
import { Checkboxes } from '@/app/questions/checkboxes/Checkboxes'
import { merge, flatten } from 'lodash'
import { beautifyXml } from '@/app/utils/beautifyXml'
import { compile, serialize, stringify } from 'stylis'

function appendCssText (cssText, key?) {
  const _window = window as any
  if (key) {
    const existingStyle = document.querySelector(`style[data-key='${key}']`)
    if (existingStyle) {
      existingStyle!.parentNode!.removeChild(existingStyle)
    }
  }
  const styleEl = document.createElement('style')
  if (key) {
    styleEl.setAttribute('data-key', key)
  }
  styleEl.innerHTML = cssText
  document.head.appendChild(styleEl)
}

export class QuizMaker {
  static Questions = questions

  private listeners = {
    submit: [] as any[],
    cancel: [] as any[],
    'validation-errors-change': [] as any[],
  }

  app = null as any
  mounted = false
  containerId = null as null | string

  // eslint-disable-next-line no-useless-constructor
  constructor (private options: {
    shadowDom: boolean;
    ui?: {
      showFooter?: boolean;
      submitText?: string;
      cancelText?: string;
      showAddQuestionBtn?: boolean;
      addQuestionText?: string;
    };
    config?;
  } = {
    shadowDom: true,
  }) {
    options.ui = merge({
      showFooter: true,
      submitText: 'Submit',
      cancelText: 'Cancel',
      showAddQuestionBtn: true,
      addQuestionText: 'Add new question',
    }, options.ui)
    store.commit('SET_UI', options.ui)
    store.watch((state, getters) => getters.validationErrors, () => {
      this.listeners['validation-errors-change'].forEach(cb => cb(flatten(Object.values(store.getters.validationErrors))))
    }, { deep: true })
  }

  setQuestion (question): void {
    store.commit('SET_QUESTION', question)
  }

  on (event, cb) {
    this.listeners[event].push(cb)
  }

  getValidationErrors () {
    return store.getters.validationErrors
  }

  submit (json) {
    this.listeners.submit.forEach(cb => cb(json))
  }

  cancel () {
    this.listeners.cancel.forEach(cb => cb())
  }

  static toMarkdown (json) {
    const questions = json
    const htmlArr = [] as string[]
    questions.forEach(que => {
      htmlArr.push(QuizMaker.Questions[que.type].toMarkdown(que))
    })
    return htmlArr.join('\n')
  }

  static xmlToJSON (xml: string) {
    return xmlToJSON(xml)
  }

  addCssText (css: string) {
    if (this.mounted) {
      const style = document.createElement('style')
      style.innerHTML = css;
      (window as any).__appendStyle__(style)
    }
  }

  addStylesheet (url: string) {
    if (this.mounted) {
      const link = document.createElement('link')
      link.type = 'text/css'
      link.rel = 'stylesheet'
      link.href = url;
      (window as any).__appendStyle__(link)
    }
  }

  static toXML (question?) {
    if (!question) {
      question = JSON.parse(JSON.stringify(store.getters.question))
    }
    return beautifyXml(QuizMaker.Questions[question.type].toXML(question))
  }

  getValue () {
    return JSON.parse(JSON.stringify(store.getters.question))
  }

  setValue (question) {
    store.commit('SET_QUESTION', question)
  }

  private attachStyles (containerId) {
    const container = document.getElementById(containerId) as Element
    let hook = document.createElement('div')
    hook.id = 'hook'
    container.appendChild(hook)

    if (this.options.shadowDom) {
      const mountPoint = document.createElement('div')
      const container = document.getElementById(containerId)!
      if (container.shadowRoot) {
        container.shadowRoot.appendChild(mountPoint)
      } else {
        container!.attachShadow({ mode: 'open' }).appendChild(mountPoint)
      }

      const newEl = document.createElement('div')
      newEl.id = 'style-hook'
      container!.shadowRoot!.appendChild(newEl)
      store.state.rootEl = container!.shadowRoot!

      const _window = window as any
      _window.__appendStyle__ = (el) => {
        newEl.appendChild(el)
      }
      (_window.__stylesToAppend__ || []).forEach(style => {
        _window.__appendStyle__(style)
      })
      hook = mountPoint
    } else {
      const _window = window as any
      _window.__appendStyle__ = (el) => {
        appendCssText(`
          ${serialize(compile(`
            #quiz-maker {
              ${el.innerHTML}
            }
          `), stringify)}
        `)
      }
      (_window.__stylesToAppend__ || []).forEach(style => {
        _window.__appendStyle__(style)
      })
    }
    return hook
  }

  mount (containerId: string) {
    if (document.getElementById(containerId) === null) {
      return
    }
    this.containerId = containerId
    const hook = this.attachStyles(containerId)
    Vue.use(BootstrapVue)
    Vue.use(IconsPlugin)

    Vue.mixin({
      data () {
        return {
          QuizMaker,
        }
      },
    })
    store.commit('SET_FEATURES_CONFIG', this.options.config)
    this.app = new Vue({
      store,
      render: h => h(QuizMakerView),
    }).$mount(hook)
    store.commit('SET_LIB_INSTANCE', this)
    this.mounted = true
  }

  refresh () {
    if (this.mounted && this.containerId) {
      this.destroy()
      this.mount(this.containerId)
    }
  }

  destroy () {
    if (this.app) {
      this.app.$destroy()
      const el = document.getElementById(this.containerId!)
      if (el) {
        if (el.shadowRoot) {
          el!.shadowRoot!.innerHTML = ''
        } else {
          el.innerHTML = ''
        }
      }
      this.mounted = false
    }
  }
}
