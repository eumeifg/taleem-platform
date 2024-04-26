<template>
  <b-tab title="Hints">
    <UiList v-model="value.hints"
            empty-state-text="No hints created"
            @add="onAddNewHint"
            title="Hints">
      <template v-slot="{ item }">
        <UiInput title="Hint" v-model="item.text" />
      </template>
    </UiList>
  </b-tab>
</template>

<script>
import UiList from '@/app/components/uiList'
import UiInput from '@/app/components/uiInput'

export default {
  name: 'QuestionHints',
  components: { UiInput, UiList },
  props: ['value'],
  methods: {
    onAddNewHint () {
      this.value.hints = [...this.value.hints, { text: '' }]
    },
  },
}
</script>

<style scoped>

</style>
