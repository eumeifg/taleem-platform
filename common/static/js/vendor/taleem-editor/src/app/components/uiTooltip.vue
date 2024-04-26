<template>
  <span class="ui-tooltip" v-if="enabled" @click="$emit('click')">
    <span class="tooltiptext bg-gray-600 text-white text-sm">
      {{ content }}
    </span>
    <slot></slot>
  </span>
  <span v-else @click="$emit('click')">
    <slot></slot>
  </span>
</template>

<script>
export default {
  name: 'UiTooltip',
  emits: ['click'],
  props: {
    enabled: {
      type: Boolean,
      default: true,
    },
    content: String,
  },
}
</script>

<style scoped lang="scss">
.ui-tooltip {
  position: relative;
  display: inline-block;

  &:hover {
    .tooltiptext {
      visibility: visible;
      opacity: 1;
    }
  }

  .tooltiptext {
    font-family: 'Nunito', sans-serif;;
    position: absolute;
    visibility: hidden;
    width: 120px;
    font-weight: 300;
    text-align: center;
    border-radius: 3px;
    box-shadow: 0px 0px 2px 0px rgba(0, 0, 0, 0.727);
    padding: 5px 0;
    z-index: 10;
    top: 105%;
    left: 50%;
    margin-left: -60px;
    opacity: 0;
    transition: opacity 0.3s;
  }
}
</style>
