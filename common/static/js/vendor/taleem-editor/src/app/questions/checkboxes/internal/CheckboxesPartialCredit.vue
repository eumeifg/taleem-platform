<template>
  <b-tab title="Partial credit" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
    <div>
      <UiSelect v-model="value.partialCredit"
                title="Partial credit"
                :options="[{ label: 'EDC', value: 'EDC' }, { label: 'Halves', value: 'halves' }]"
      />
    </div>
  </b-tab>
</template>

<script>
import UiSelect from '@/app/components/uiSelect'

export default {
  name: 'CheckboxesPartialCredit',
  components: { UiSelect },
  props: ['value'],
}
</script>

<style scoped>

</style>
