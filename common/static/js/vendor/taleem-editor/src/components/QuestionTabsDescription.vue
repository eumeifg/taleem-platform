<template>
  <div v-if="!active" class="text-sm text-gray-700 mt-4 border-t border-gray-200 pt-3">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'QuestionTabsDescription',
  props: ['active'],
}
</script>

<style scoped>

</style>
