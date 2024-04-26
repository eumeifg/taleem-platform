<template>
  <b-tab title="Explanation">
    <UiRichTextEditor title="Explanation"
                      class="explanation-input"
                      v-model="value.explanation"/>
  </b-tab>
</template>

<script>
import UiRichTextEditor from '@/app/components/uiRichTextEditor'
export default {
  name: 'QuestionExplanation',
  components: { UiRichTextEditor },
  props: ['value'],
}
</script>

<style scoped>

</style>
