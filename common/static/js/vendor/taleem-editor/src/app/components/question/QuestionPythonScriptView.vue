<template>
  <b-tab title="Python Script" nav-class="text-blue-600" nav-wrapper-class="text-blue-600">
    <UiCheckbox title="Custom Python script"
                v-model="value.hasCustomScript" />
    <UiCodeMirror v-if="value.hasCustomScript"
                  title="Python script"
                  :description="description"
                  v-model="value.script" class="w-full"/>
  </b-tab>
</template>

<script>
import UiCodeMirror from '@/app/components/uiCodeMirror'
import UiCheckbox from '@/app/components/uiCheckbox'
export default {
  name: 'QuestionPythonScriptView',
  components: { UiCheckbox, UiCodeMirror },
  props: ['value', 'description'],
}
</script>

<style scoped>

</style>
