<template>
  <UiLabel :title="title" :description="description">
    <input type="checkbox" class="q-checkbox" :checked="value" @input="ev => onInput(ev.target.checked)" />
  </UiLabel>
</template>

<script>
import UiLabel from '@/app/components/uiLabel'
export default {
  name: 'UiCheckbox',
  components: { UiLabel },
  emits: ['input'],
  props: {
    value: String,
    title: String,
    description: String,
  },
  methods: {
    onInput (val) {
      this.$emit('input', val)
    },
  },
}
</script>

<style scoped lang="scss">
</style>
