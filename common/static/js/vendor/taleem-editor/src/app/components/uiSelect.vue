<template>
  <UiLabel :title="title" :description="description" class="q-select">
    <select v-model="cValue"
            :style="{ width }"
            class="w-full py-2 px-3 rounded border border-gray-300 text-xs">
      <option v-for="(option, index) in options" :key="index" :value="option.value">{{ option.label }}</option>
    </select>
  </UiLabel>
</template>

<script>
import UiLabel from '@/app/components/uiLabel'
export default {
  name: 'UiSelect',
  components: { UiLabel },
  props: {
    value: Array,
    title: String,
    description: String,
    width: String,
    options: {
      type: Array,
      required: true,
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

<style scoped lang="scss">
</style>
