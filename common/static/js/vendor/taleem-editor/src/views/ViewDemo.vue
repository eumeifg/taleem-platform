<template>
  <div>
    <div class="bg-gray-200 min-h-screen">
      <button @click="setQuestion('getValue')">getValue()</button>
      <button @click="setQuestion('checkbox')">Checkbox question</button>
      <button @click="setQuestion('dropdown')">Dropdown question</button>
      <button @click="setQuestion('multi-choice')">Multi choice question</button>
      <button @click="setQuestion('numerical-input')">Numerical input question</button>
      <button @click="setQuestion('text-input')">Text input question</button>
      <button @click="setQuestion('math-expression')">Math expression question</button>
      <button @click="refresh">Refresh</button>
      <div style="width: 1100px; margin: 0 auto;">
        <div id="quiz-maker-hook"></div>
      </div>
    </div>
  </div>
</template>

<script>
import { QuizMaker } from '../app/QuizMaker'
import { checkboxProblemXml } from '@/views/configs/checkboxProblemXml'
import { dropdownProblemXml } from '@/views/configs/dropdownProblemXml'
import { multiChoiceProblemXml } from '@/views/configs/multiChoiceProblemXml'
import { numericalInputProblemXml } from '@/views/configs/numericalInputProblemXml'
import { textInputProblemXml } from '@/views/configs/textInputProblemXml'
import { mathExpressionProblemXml } from '@/views/configs/mathExpressionProblemXml'

export default {
  name: 'Demo',
  data () {
    return {
      val: 0,
      quizMaker: null,
    }
  },
  mounted () {
    this.mountApp()
  },
  watch: {
    visible: {
      async handler (isVisible) {
        if (!isVisible) {
          this.destroyApp()
        } else {
          await this.$nextTick()
          this.mountApp()
        }
      },
    },
  },
  methods: {
    refresh () {
      this.quizMaker.refresh()
    },
    destroyApp () {
      this.quizMaker.destroy()
    },
    mountApp () {
      this.quizMaker = new QuizMaker({
        shadowDom: false,
        config: {
          checkboxes: {
            explanation: true,
            customScript: true,
            optionHints: true,
            compoundFeedback: true,
            partialCredit: true,
          },
          dropdown: {
            optionHints: true,
          },
          'multi-choice': {
            optionHints: true,
          },
          'numerical-input': {
            tolerance: true,
            trailingText: true,
            partialCredit: true,
          },
          'text-input': {
            feedback: true,
            trailingText: true,
          },
        },
      })
      this.quizMaker.on('validation-errors-change', errs => {
        console.log('Errors: ', errs)
      })
      this.quizMaker.mount('quiz-maker-hook')
      this.setQuestion('checkbox')
      this.quizMaker.on('submit', json => {
        console.log(json)
        console.log(QuizMaker.toXML(json))
        console.log(QuizMaker.toMarkdown(json))
      })
      this.quizMaker.on('cancel', () => {
        console.log('cancelled')
      })
      this.quizMaker.addCssText(`
          .test {
            background-color: red;
          }
        `)
    },
    setQuestion (type) {
      switch (type) {
        case 'getValue':
          console.log(this.quizMaker.getValue())
          console.log(QuizMaker.toXML(this.quizMaker.getValue()))
          break
        case 'checkbox':
          this.quizMaker.setQuestion(QuizMaker.xmlToJSON(checkboxProblemXml))
          break
        case 'dropdown':
          this.quizMaker.setQuestion(QuizMaker.xmlToJSON(dropdownProblemXml))
          break
        case 'multi-choice':
          this.quizMaker.setQuestion(QuizMaker.xmlToJSON(multiChoiceProblemXml))
          break
        case 'numerical-input':
          this.quizMaker.setQuestion(QuizMaker.xmlToJSON(numericalInputProblemXml))
          break
        case 'text-input':
          this.quizMaker.setQuestion(QuizMaker.xmlToJSON(textInputProblemXml))
          break
        case 'math-expression':
          this.quizMaker.setQuestion(QuizMaker.xmlToJSON(mathExpressionProblemXml))
          break
      }
    },
  },
}
</script>

<style scoped>

</style>
