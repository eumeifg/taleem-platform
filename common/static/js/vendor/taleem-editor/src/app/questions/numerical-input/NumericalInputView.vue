<template>
  <QuestionTabs>
    <QuestionErrors/>
    <b-tab title="General">
      <QuestionTitle required :value="cValue.config"/>
      <QuestionDescription :value="cValue.config"/>
      <NIAnswer v-model="cValue.config.answer" />
    </b-tab>
    <b-tab v-if="$store.getters.features['numerical-input'].tolerance"
           title="Tolerance" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
      <UiInput class="flex-1"
               v-model="cValue.config.tolerance"
               title="Tolerance"/>
    </b-tab>
    <b-tab v-if="$store.getters.features['numerical-input'].trailingText"
           title="Trailing text" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
      <UiInput class="flex-1"
               v-model="cValue.config.trailingText"
               title="Trailing text"/>
    </b-tab>
    <b-tab title="Additional answers" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
      <UiList v-model="cValue.config.additionalAnswers"
              @add="onAddNewOption"
              :active="active"
              title="Additional answers">
        <template v-slot="{ index }">
          <NIAnswer v-model="cValue.config.additionalAnswers[index]"/>
        </template>
      </UiList>
    </b-tab>
    <b-tab v-if="$store.getters.features['numerical-input'].partialCredit"
           title="Partial credit" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
      <div>
        <UiMultiSelect class="flex-1"
               title="Partial credit types"
               width="400px"
               v-model="cValue.config.partialCredit"
               :options="[{ label: 'Close', value: 'close' }, { label: 'List', value: 'list' }]"/>
        <UiInput v-if="cValue.config.partialCredit.includes('close')"
                 v-model="cValue.config.partialRange"
                 type="number"
                 title="Partial range"
        />
        <template v-if="cValue.config.partialCredit.includes('list')">
          <UiList v-model="cValue.config.partialAnswers"
                  @add="onAddNewPartialAnswer"
                  :active="active"
                  title="Additional answers">
            <template v-slot="{ index }">
              <UiInput v-model="cValue.config.partialAnswers[index]"
                       :title="`Partial answer #${index + 1}`"/>
            </template>
          </UiList>
        </template>
      </div>
    </b-tab>
    <QuestionPythonScriptView :value="cValue.config" v-if="$store.getters.features.checkboxes.customScript"
                          :description="`
    <p>Place instructions in python and then use created variables in Answers, e.g.</p>
    <code>
    computed_response = math.sqrt(math.fsum([math.pow(math.pi,2), math.pow(math.e,2)]))
    </code>
    Then use <code>$computed_response</code> in place of answer.`"/>
    <QuestionHints v-model="cValue.config" />
  </QuestionTabs>
</template>

<script>
import UiInput from '@/app/components/uiInput'
import UiList from '@/app/components/uiList'
import NIAnswer from '@/app/questions/numerical-input/internal/NIAnswer'
import { NumericalInput } from '@/app/questions/numerical-input/NumericalInput'
import UiMultiSelect from '@/app/components/uiMultiSelect'
import QuestionTabs from '@/components/QuestionTabs'
import QuestionErrors from '@/app/components/question/QuestionErrors'
import QuestionTitle from '@/app/components/question/QuestionTitle'
import QuestionDescription from '@/app/components/question/QuestionDescription'
import QuestionHints from '@/app/components/question/QuestionHints'
import QuestionPythonScriptView from '@/app/components/question/QuestionPythonScriptView'

export default {
  components: { QuestionPythonScriptView, QuestionHints, QuestionDescription, QuestionTitle, QuestionErrors, QuestionTabs, UiMultiSelect, NIAnswer, UiList, UiInput },
  props: {
    value: Object,
    active: Boolean,
  },
  methods: {
    onAddNewPartialAnswer () {
      this.cValue.config.partialAnswers.push('')
    },
    onAddNewOption () {
      this.cValue.config.additionalAnswers.push(NumericalInput.makeNewAnswer())
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
