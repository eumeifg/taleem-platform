<template>
  <QuestionTabs>
    <QuestionErrors/>
    <b-tab title="General">
      <QuestionTitle required :value="cValue.config"/>
      <QuestionDescription :value="cValue.config"/>
      <UiList v-model="cValue.config.options"
              required
              @add="onAddNewOption"
              title="Options">
        <template v-slot="{ item, index }">
          <UiSelect width="150px"
                    v-if="!cValue.config.hasCustomScript"
                    title="Is correct answer"
                    v-model="item.correct"
                    @input="onCorrectChange(item, index)"
                    :options="[{ label: 'true', value: 'true' }, { label: 'false', value: 'false' }, { label: 'partial', value: 'partial' }]"/>
          <UiInput class="flex-1" v-model="item.label" :title="`Option ${index+1}`" />
          <UiInput v-if="$store.getters.features.dropdown.optionHints" class="flex-1" v-model="item.hint"
                   title="Explanation if selected"/>
        </template>
      </UiList>
    </b-tab>
    <b-tab title="Configuration">
      <UiCheckbox title="Shuffle answers" v-model="cValue.config.isShuffled" />
    </b-tab>
    <QuestionExplanation v-model="cValue.config" />
    <QuestionHints v-model="cValue.config" />
    <QuestionPythonScriptView :value="cValue.config" v-if="$store.getters.features['multi-choice'].customScript"
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
  </QuestionTabs>
</template>

<script>
import UiList from '@/app/components/uiList'
import UiInput from '@/app/components/uiInput'
import UiTooltip from '@/app/components/uiTooltip'
import { MultiChoice } from '@/app/questions/multi-choice/MultiChoice'
import QuestionTabs from '@/components/QuestionTabs'
import UiSelect from '@/app/components/uiSelect'
import QuestionErrors from '@/app/components/question/QuestionErrors'
import QuestionTitle from '@/app/components/question/QuestionTitle'
import QuestionDescription from '@/app/components/question/QuestionDescription'
import QuestionExplanation from '@/app/components/question/QuestionExplanation'
import QuestionHints from '@/app/components/question/QuestionHints'
import UiCheckbox from '@/app/components/uiCheckbox'
import QuestionPythonScriptView from '@/app/components/question/QuestionPythonScriptView'

export default {
  components: { QuestionPythonScriptView, UiCheckbox, QuestionHints, QuestionExplanation, UiSelect, UiInput, UiTooltip, UiList, QuestionDescription, QuestionTitle, QuestionErrors, QuestionTabs },
  props: {
    value: Object,
    active: Boolean,
  },
  created () {
    if (!this.cValue.config.options) {
      this.cValue.config.options = [MultiChoice.makeNewOption()]
    }
  },
  methods: {
    onAddNewOption () {
      this.cValue.config.options.push(MultiChoice.makeNewOption())
    },
    onCorrectChange (item, index) {
      if (item.correct === 'true') {
        this.cValue.config.options.forEach((element, i) => {
          if (i !== index) {
            element.correct = 'false'
          }
        })
      }
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
