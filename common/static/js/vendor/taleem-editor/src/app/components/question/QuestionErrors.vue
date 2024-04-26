<template>
  <b-alert :show="!!$store.getters.validationErrors.length"
           class="validation-err"
           variant="danger">
    <p class="alert-header font-bold">Validation errors</p>
    <ul>
      <li v-for="(valErr, index) in $store.getters.validationErrors" :key="index">
        {{ valErr.message }}
      </li>
    </ul>
  </b-alert>
</template>

<script>
export default {
  name: 'QuestionErrors',
}
</script>

<style scoped>

</style>
