<template>
  <div class="form-item-label" v-if="title">
    <div class="form-item-label--title text-xl font-bold">
      {{ title }}
      <span v-if="required" class="text-red-600">*</span>
    </div>
    <div v-if="description" class="form-item-label--desc" v-html="description" style="white-space: pre-wrap;"></div>
    <slot/>
  </div>
  <label v-else>
    <slot/>
  </label>
</template>

<script>
export default {
  name: 'uiLabel',
  props: ['title', 'description', 'required'],
}
</script>

<style scoped lang="scss">

.form-item-label {
  display: block;
}

.form-item-label + .form-item-label {
  margin-top: 15px;
}

.form-item-label--title {
  font-size: 14px;
  margin-bottom: 4px;
}

.form-item-label--desc {
  font-size: 12px;
  color: #666;
  margin-bottom: 10px;
}
</style>
