<template>
  <div>
    <UiSelect class="flex-1"
              :options="[{ label: 'Equal', value: 'equal' }, { label: 'Range', value: 'range' }]"
              v-model="cValue.type"
              title="Type"/>
    <template v-if="cValue.type === 'equal'">
      <UiInput class="flex-1" v-model="cValue.value"
               required
               title="Answer"/>
    </template>
    <template v-else-if="cValue.type === 'range'">
      <UiSelect class="flex-1"
                :options="[{ label: 'Greater than', value: 'gt' }, { label: 'Greater than or equal', value: 'gte' }]"
                v-model="cValue.rangeFromType"
                required
                title="Range from type"/>
      <UiInput class="flex-1" v-model="cValue.rangeFrom"
               required
               title="Range from"/>
      <UiSelect class="flex-1"
                required
                :options="[{ label: 'Less than', value: 'lt' }, { label: 'Less than or equal', value: 'lte' }]"
                v-model="cValue.rangeToType"
                title="Range to type"/>
      <UiInput class="flex-1" v-model="cValue.rangeTo"
               required
               title="Range to"/>
    </template>
  </div>
</template>

<script>
import UiInput from '@/app/components/uiInput'
import UiSelect from '@/app/components/uiSelect'

export default {
  components: { UiSelect, UiInput },
  props: {
    value: Object,
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
