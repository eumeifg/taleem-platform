<template>
  <b-tab title="Selected hints">
    <div v-for="(item, index) in value.possibleAnswers" :key="index" class="w-full">
      <UiInput class="flex-1"
               v-model="item.selectedHint"
               :title="`Explanation if selected ${item.label.slice(0, 100)}`"
               size="sm"/>
      <UiInput class="flex-1"
               v-model="item.notSelectedHint"
               :title="`Explanation if not selected ${item.label.slice(0, 100)}`"
               size="sm"/>
    </div>
  </b-tab>
</template>

<script>
import UiInput from '@/app/components/uiInput'
export default {
  name: 'CheckboxesSelectedHints',
  components: { UiInput },
  props: ['value'],
}
</script>

<style scoped>

</style>
