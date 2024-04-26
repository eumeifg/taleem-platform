<template>
  <b-tabs content-class="mt-3" pills v-model="cValue" :key="tabValue">
    <slot></slot>
  </b-tabs>
</template>

<script>
export default {
  name: 'QuestionTabs',
  props: ['value'],
  data () {
    return {
      tabValue: 0,
    }
  },
  computed: {
    cValue: {
      get () {
        return this.value !== undefined ? this.value : this.tabValue
      },
      set (val) {
        this.tabValue = val
        this.$emit('input', val)
      },
    },
  },
}
</script>

<style scoped>

</style>
