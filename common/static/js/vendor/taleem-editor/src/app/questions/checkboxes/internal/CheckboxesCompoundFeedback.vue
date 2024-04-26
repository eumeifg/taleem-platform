<template>
  <b-tab title="Compound feedback">
    <div>
      <UiList v-model="value.compoundFeedbackGroups"
              @add="onAddNewCompoundFeedbackGroup"
              title="Compound Feedback Groups">
        <template v-slot="{ item }">
          <div>
            <div class="flex items-center">
              <UiTooltip content="Answers" class="mr-3">
                <button
                    type="button"
                    class="btn btn-primary"
                    v-b-modal.modal-standard
                >
                  {{ item.selected.length ? item.selected.map(x => getAnswerLetter(x)).sort().join(', ') : 'Standard modal'}}
                </button>
              </UiTooltip>
              <UiInput class="flex-1" v-model="item.label"
                       :title="`Hint which will show up when selected answers will be chosen`"
                       :show-label="false"/>

              <b-modal
                  static
                  hide-footer
                  id="modal-standard"
                  title="Choose answers"
                  title-class="font-18"
              >
                <b-form-checkbox-group
                    id="checkbox-group-1"
                    v-model="item.selected"
                    :options="value.possibleAnswers.map(ans => ({ text: ans.label, value: ans.id }))"
                    name="flavour-1"
                ></b-form-checkbox-group>
              </b-modal>
            </div>
          </div>
        </template>
      </UiList>
    </div>
  </b-tab>
</template>

<script>
import { Checkboxes } from '@/app/questions/checkboxes/Checkboxes'
import UiTooltip from '@/app/components/uiTooltip'
import UiInput from '@/app/components/uiInput'
import UiList from '@/app/components/uiList'

export default {
  name: 'CheckboxesCompoundFeedback',
  components: { UiList, UiInput, UiTooltip },
  props: ['value'],
  watch: {
    'value.possibleAnswers' (possibleAnswers) {
      this.value.compoundFeedbackGroups = this.value.compoundFeedbackGroups.filter(cfg => cfg.selected.every(id => possibleAnswers.find(ans => ans.id === id)))
    },
  },
  methods: {
    getAnswerLetter (answerId) {
      return Checkboxes.getAnswerLetterById(this.value, answerId)
    },
    onAddNewCompoundFeedbackGroup () {
      this.value.compoundFeedbackGroups = [...this.value.compoundFeedbackGroups, Checkboxes.makeNewCompoundFeedbackGroup()]
    },
  },
}
</script>

<style scoped>

</style>
