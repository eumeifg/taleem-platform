<template>
  <UiRichTextEditor title="Description" :required="required" v-model="value.description" class="description-input"/>
</template>

<script>
import UiRichTextEditor from '@/app/components/uiRichTextEditor'

export default {
  name: 'QuestionDescription',
  props: {
    value: String,
    required: Boolean,
  },
  components: { UiRichTextEditor },
}
</script>

<style scoped>

</style>
