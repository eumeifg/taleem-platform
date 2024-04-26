<template>
  <UiLabel :title="title" :description="description" class="q-multi-select">
    <b-form-select v-model="cValue"
                   :options="options.map(opt => ({ text: opt.label, value: opt.value }))"
                   multiple
                   :select-size="4"></b-form-select>
  </UiLabel>
</template>

<script>
import UiLabel from '@/app/components/uiLabel'

export default {
  name: 'UiMultiSelect',
  components: { UiLabel },
  props: {
    value: Array,
    title: String,
    description: String,
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
