<template>
  <QuestionTabs>
    <QuestionErrors/>
    <b-tab title="General">
      <QuestionTitle required :value="cValue.config"/>
      <QuestionDescription :value="cValue.config"/>
      <UiInput required v-model="cValue.config.answer" title="Answer"/>
    </b-tab>
    <b-tab title="Configuration" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
      <UiCheckbox v-model="cValue.config.isCaseSensitive" title="Case sensitive"/>
      <UiCheckbox v-model="cValue.config.isRegexp" title="Regular expression"/>
      <UiInput v-model="cValue.config.textSize" title="Text input size"/>
    </b-tab>
    <b-tab title="Additional answers" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
      <UiList v-model="cValue.config.additionalAnswers"
              @add="onAddAdditionalAnswer"
              :active="active"
              title="Additional answers">
        <template v-slot="{ index }">
          <UiInput v-model="cValue.config.additionalAnswers[index].text" :title="`Additional answer ${index + 1}`"/>
        </template>
      </UiList>
    </b-tab>
    <b-tab v-if="$store.getters.features['text-input'].feedback"
           title="Feedback" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
      <UiList v-model="cValue.config.equalFeedbacks"
              @add="onAddNewEqFeedback"
              :active="active"
              title="Equal feedbacks">
        <template v-slot="{ item }">
          <UiInput v-model="item.answer" title="Answer"/>
          <UiInput v-model="item.feedback" title="Answer"/>
        </template>
      </UiList>
    </b-tab>
    <b-tab v-if="$store.getters.features['text-input'].trailingText"
           title="Trailing text" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
      <UiInput class="flex-1"
               v-model="cValue.config.trailingText"
               title="Trailing text"/>
    </b-tab>
  </QuestionTabs>
</template>

<script>

import UiInput from '@/app/components/uiInput'
import UiList from '@/app/components/uiList'
import { TextInput } from '@/app/questions/text-input/TextInput'
import QuestionTabs from '@/components/QuestionTabs'
import QuestionErrors from '@/app/components/question/QuestionErrors'
import QuestionTitle from '@/app/components/question/QuestionTitle'
import QuestionDescription from '@/app/components/question/QuestionDescription'
import UiCheckbox from '@/app/components/uiCheckbox'
export default {
  components: { UiCheckbox, QuestionDescription, QuestionTitle, QuestionErrors, QuestionTabs, UiList, UiInput },
  props: {
    value: Object,
    active: Boolean,
  },
  methods: {
    onAddAdditionalAnswer () {
      TextInput.addAdditionalAnswer(this.cValue)
    },
    onAddNewEqFeedback () {
      TextInput.addEqFeedback(this.cValue)
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
