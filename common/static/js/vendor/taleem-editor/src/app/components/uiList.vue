<template>
  <UiLabel :required="required" class="my-2 q-list" :title="title" :description="description">
    <div class="flex rounded-md">
      <div v-if="value.length === 0" class="py-5 rounded border border-gray-200 flex flex-column bg-gray-50 items-center justify-center w-full">
        <h2 class="text-xl mb-3">{{ emptyStateText }}</h2>
        <b-button @click="$emit('add')">Add new</b-button>
      </div>
      <ul v-else class="w-full">
        <li v-for="(item, index) in value" :key="index"
            :style="{
              'backgroundColor': backgroundColor,
            }"
            class="mb-3 rounded p-3 border border-gray-200">
          <div>
            <div class="flex items-center mb-3">
              <h3 class="q-list-item-title text-xl font-bold mr-2">{{ itemLabelFn(item, index) }}</h3>
              <b-button class="q-list-item-delete" @click="onRemove(item)" size="sm" variant="danger">Delete</b-button>
            </div>
            <div class="w-full q-list-item-content">
              <slot :item="item" :index="index" :on-remove="() => onRemove(item)"></slot>
            </div>
          </div>
        </li>
        <div class="text-center">
          <b-button class="q-list-item-add-new" @click="$emit('add')">Add new</b-button>
        </div>
      </ul>
    </div>
  </UiLabel>
</template>

<script>

import UiLabel from '@/app/components/uiLabel'
export default {
  name: 'uiList',
  components: { UiLabel },
  emits: ['input', 'add'],
  props: {
    required: Boolean,
    backgroundColor: {
      type: String,
      default: 'rgba(249, 250, 251, 1)',
    },
    emptyStateText: {
      type: String,
      default: 'No items added.',
    },
    itemLabelFn: {
      type: Function,
      default: (item, index) => `Item ${index + 1}`,
    },
    title: String,
    description: String,
    value: Array,
    addNewLabel: {
      type: String,
      default: 'Add new',
    },
  },
  methods: {
    onRemove (item) {
      this.$emit('input', this.value.filter(_item => _item !== item))
    },
  },
}
</script>

<style scoped>

</style>
