<template>
  <QuestionTabs v-model="tabValue">
    <QuestionErrors/>
    <b-tab title="General">
      <UiList v-model="cValue.config.dropdowns"
              @add="() => onAddNewDropdown()"
              :item-label-fn="(item, index) => `Dropdown ${index + 1}`"
              add-new-label="Add new question"
              title="Questions">
        <template v-slot="{ item: dropdown }">
          <div>
            <QuestionTabs>
              <b-tab title="General">
                <QuestionTitle required :value="dropdown"/>
                <QuestionDescription :value="dropdown"/>
                <UiList v-model="dropdown.options"
                        required
                        @add="() => onAddNewOption(dropdown)"
                        background-color="#fff"
                        :item-label-fn="(item, index) => `Answer ${index + 1}`"
                        add-new-label="Add new answer"
                        title="Answers">
                  <template v-slot="{ item: dropdownOption, index }">
                    <div>
                      <div class="flex items-center">
                        <UiCheckbox :value="dropdownOption.isCorrect"
                                    title="Is correct"
                                    @input="selectCorrectAnswer(dropdown, dropdownOption)"
                                    class="mr-3"/>
                        <UiInput class="flex-1"
                                 required
                                 :title="`Option ${index + 1}`"
                                 v-model="dropdownOption.text" />
                      </div>
                      <UiInput class="flex-1"
                               v-if="$store.getters.features.dropdown.optionHints"
                               title="Explanation if selected"
                               v-model="dropdownOption.hint"/>
                    </div>
                  </template>
                </UiList>
              </b-tab>
              <QuestionExplanation :value="dropdown"/>
            </QuestionTabs>
          </div>
        </template>
      </UiList>
    </b-tab>
    <QuestionHints :value="cValue.config"/>
  </QuestionTabs>
</template>

<script>
import { Dropdown } from '@/app/questions/dropdown/Dropdown'
import QuestionTabs from '@/components/QuestionTabs'
import QuestionErrors from '@/app/components/question/QuestionErrors'
import UiList from '@/app/components/uiList'
import QuestionTitle from '@/app/components/question/QuestionTitle'
import QuestionDescription from '@/app/components/question/QuestionDescription'
import QuestionExplanation from '@/app/components/question/QuestionExplanation'
import QuestionHints from '@/app/components/question/QuestionHints'
import UiCheckbox from '@/app/components/uiCheckbox'
import UiInput from '@/app/components/uiInput'

export default {
  components: { UiInput, UiCheckbox, QuestionHints, QuestionExplanation, QuestionDescription, QuestionTitle, UiList, QuestionErrors, QuestionTabs },
  data () {
    return {
      tabValue: 0,
      tabValue2: 0,
    }
  },
  props: {
    value: Object,
    active: Boolean,
  },
  methods: {
    onAddNewDropdown () {
      this.cValue.config.dropdowns.push(Dropdown.makeNewDropdownQuestion())
    },
    onAddNewOption (question) {
      Dropdown.addNewOption(question)
    },
    selectCorrectAnswer (question, option) {
      question.options.forEach(opt => opt.isCorrect = false)
      option.isCorrect = true
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
