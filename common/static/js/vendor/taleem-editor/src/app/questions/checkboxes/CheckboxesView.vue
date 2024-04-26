<template>
  <QuestionTabs v-model="tabValue">
    <QuestionErrors />
    <b-tab title="General">
      <QuestionTitle required :value="cValue.config" />
      <QuestionDescription required :value="cValue.config" />
      <UiList v-model="cValue.config.possibleAnswers"
              required
              @add="onAddNewAnswer"
              title="Answers">
        <template v-slot="{ item }">
          <div>
            <div class="">
              <UiInput required title="Text" v-model="item.label" />
              <UiCheckbox title="Is correct answer" v-model="item.isCorrect" class="mr-3"/>
            </div>
          </div>
        </template>
      </UiList>
    </b-tab>
    <QuestionExplanation :value="cValue.config" v-if="$store.getters.features.checkboxes.explanation" />
    <CheckboxesSelectedHints :value="cValue.config" v-if="$store.getters.features.checkboxes.optionHints" />
    <CheckboxesCompoundFeedback :value="cValue.config" v-if="$store.getters.features.checkboxes.compoundFeedback" />
    <CheckboxesPartialCredit :value="cValue.config" v-if="$store.getters.features.checkboxes.partialCredit" />
    <QuestionPythonScriptView :value="cValue.config" v-if="$store.getters.features.checkboxes.customScript"
      :description="`
    <p>Place instructions in python and then use created variables in Answers, e.g.</p>
    <code>
    random.seed(anonymous_student_id)  # Use different random numbers for each student.
    a = random.randint(1,10)
    b = random.randint(1,10)
    c = a + b

    ok0 = c % 2 == 0 # check remainder modulo 2
    text0 = '$a + $b is divisible by 2'
    </code>
    Then use <code>$ok0</code> and <code>$text0</code> in answers to place correct values.`"/>
    <QuestionHints :value="cValue.config" />
  </QuestionTabs>
</template>

<script>
import UiList from '@/app/components/uiList'
import UiCheckbox from '@/app/components/uiCheckbox'
import UiInput from '@/app/components/uiInput'
import { Checkboxes } from '@/app/questions/checkboxes/Checkboxes'
import QuestionTabs from '@/components/QuestionTabs'
import QuestionErrors from '@/app/components/question/QuestionErrors'
import CheckboxesCompoundFeedback from '@/app/questions/checkboxes/internal/CheckboxesCompoundFeedback'
import CheckboxesPartialCredit from '@/app/questions/checkboxes/internal/CheckboxesPartialCredit'
import CheckboxesSelectedHints from '@/app/questions/checkboxes/internal/CheckboxesSelectedHints'
import QuestionExplanation from '@/app/components/question/QuestionExplanation'
import QuestionTitle from '@/app/components/question/QuestionTitle'
import QuestionDescription from '@/app/components/question/QuestionDescription'
import QuestionPythonScriptView from '@/app/components/question/QuestionPythonScriptView'
import QuestionHints from '@/app/components/question/QuestionHints'

export default {
  components: { QuestionHints, QuestionPythonScriptView, QuestionDescription, QuestionTitle, QuestionExplanation, CheckboxesSelectedHints, CheckboxesPartialCredit, CheckboxesCompoundFeedback, QuestionErrors, QuestionTabs, UiInput, UiCheckbox, UiList },
  data () {
    return {
      tabValue: 0,
    }
  },
  props: {
    value: Object,
  },
  methods: {
    onAddNewAnswer () {
      this.cValue.config.possibleAnswers = [...this.cValue.config.possibleAnswers, Checkboxes.makeNewAnswer(this.cValue.config.possibleAnswers.length)]
    },
  },
  computed: {
    cValue: {
      get () {
        return this.value
      },
      set (val) {
        this.$emit('input', val)
      },
    },
  },
}
</script>

<style scoped>

</style>
