<template>
  <QuestionTabs>
    <QuestionErrors/>
    <b-tab title="General">
      <QuestionTitle required :value="cValue.config"/>
      <QuestionDescription :value="cValue.config"/>
      <UiInput required v-model="cValue.config.answer" title="Answer"/>
      <UiInput required v-model="cValue.config.samples" title="Samples"/>
    </b-tab>
    <b-tab title="Configuration">
      <UiInput v-model="cValue.config.tolerance" title="Tolerance"/>
      <UiCheckbox v-model="cValue.config.isCaseSensitive" title="Is case sensitive" />
    </b-tab>
    <b-tab title="Python Script">
      <UiCodeMirror title="Python Script" v-model="cValue.config.script"
                    :description="`
    <p>Place instructions in python and then use created variables in answers, e.g.</p>
    <code>
    computed_response = PYTHON SCRIPT
    </code>
    Then place <code>$computed_response</code> in answer input.`"/>
    </b-tab>
  </QuestionTabs>
</template>

<script>
import QuestionTabs from '@/components/QuestionTabs'
import QuestionErrors from '@/app/components/question/QuestionErrors'
import QuestionTitle from '@/app/components/question/QuestionTitle'
import QuestionDescription from '@/app/components/question/QuestionDescription'
import UiInput from '@/app/components/uiInput'
import UiCheckbox from '@/app/components/uiCheckbox'
import UiCodeMirror from '@/app/components/uiCodeMirror'

export default {
  components: { UiCodeMirror, UiCheckbox, UiInput, QuestionDescription, QuestionTitle, QuestionErrors, QuestionTabs },
  data () {
    return {
      tabValue: 0,
    }
  },
  props: {
    value: Object,
    active: Boolean,
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
