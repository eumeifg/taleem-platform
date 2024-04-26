<template>
  <UiInput title="Question title"
           :required="required"
           v-model="value.title"
           size="lg"
           class="q-title"/>
</template>

<script>
import UiInput from '@/app/components/uiInput'
export default {
  name: 'QuestionTitle',
  components: { UiInput },
  props: {
    value: String,
    required: Boolean,
  },
}
</script>

<style scoped>

</style>
