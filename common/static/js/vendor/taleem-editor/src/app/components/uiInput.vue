<template>
  <UiLabel :title="title" :description="description" :required="required">
    <textarea v-if="type === 'text'"
              ref="input"
              rows="1"
              :value="value"
              @input="ev => onInput(ev.target.value)"
              class="q-input q-text rounded active flex-1 block w-full min-w-0 sm:text-sm outline-none auto_height ui-input__input"
              :class="{
                    'size-lg': size === 'lg',
                    'size-md': size === 'md',
                    'size-sm': size === 'sm',
                 }"
    />
    <input v-if="type === 'number'"
           type="number"
           :value="value"
           @input="ev => onInput(ev.target.value)"
           class="q-input q-input-number rounded active flex-1 block w-full min-w-0 sm:text-sm outline-none auto_height ui-input__input"
           :class="{
                    'size-lg': size === 'lg',
                    'size-md': size === 'md',
                    'size-sm': size === 'sm',
                 }"
    />
  </UiLabel>
</template>

<script>
import UiLabel from '@/app/components/uiLabel'
export default {
  name: 'UiInput',
  components: { UiLabel },
  emits: ['input'],
  props: {
    required: Boolean,
    color: String,
    type: {
      type: String,
      default: 'text',
    },
    showLabel: {
      type: Boolean,
      default: true,
    },
    title: String,
    description: String,
    value: String,
    textArea: Boolean,
    placeholder: String,
    size: {
      type: String,
      default: 'md',
      validator: (val) => ['sm', 'md', 'lg'].includes(val),
    },
  },
  async mounted () {
    if (this.type === 'text') {
      await this.$nextTick()
      this.onInput(this.value) // fix height
    }
    if (this.$refs.input) {
      this.respondToVisibility(this.$refs.input, () => {
        this.onInput(this.value)
      })
    }
  },
  methods: {
    onInput (val) {
      if (this.$refs.input && this.$refs.input.scrollHeight) {
        this.$refs.input.style.height = '1px'
        this.$refs.input.style.height = (this.$refs.input.scrollHeight) + 5 + 'px'
      }
      this.$emit('input', val)
    },
    respondToVisibility (element, fn) {
      const options = {
        root: document.documentElement,
      }

      const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          fn(entry.intersectionRatio > 0)
        })
      }, options)

      observer.observe(element)
    },
  },
  computed: {
    tag () {
      return 'input'
    },
  },
}
</script>

<style scoped lang="scss">
.auto_height {
  width: 100%;
}

label {
  margin-bottom: 0;
  text-align: left;
  &.size-sm {
    color: #666;
    font-size: 12px;
    text-transform: uppercase;
  }
  &.size-md {
    color: #444;
    font-size: 12px;
    text-transform: uppercase;
  }
  &.size-lg {
    font-size: 12px;
    font-weight: bold;
    color: #333;
    text-transform: uppercase;
  }
}

textarea {
  color: #000;
  border-width: 0;
  padding: 6px 0px;
  resize: none;
  &:focus {
    outline: none;
    box-shadow: none;
    border: 1px solid #ddd;
  }
  &.active {
    padding: 12px;
  }
}
textarea::-webkit-input-placeholder {
  color: #222;
}
.ui-input__input.size-lg {
  font-size: 22px;
  color: #111;
  &.active {
    font-size: 18px;
    border: 1px solid #ddd;
  }

  &:focus {
    outline: none;
    box-shadow: none;
  }
  &::-webkit-input-placeholder {
    color: #222;
    font-weight: 500;
  }
}

.ui-input__input.size-md {
  font-size: 14px;

  &.active {
    border: 1px solid #ddd;
  }

  &::-webkit-input-placeholder {
    color: #888;
  }
}

.ui-input__input.size-sm {
  font-size: 14px;
  color: #333;
  &.active {
    border: 1px solid #ddd;
  }
  &::-webkit-input-placeholder {
    color: #888;
  }
}
</style>
