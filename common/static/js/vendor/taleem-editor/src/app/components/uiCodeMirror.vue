<template>
  <UiLabel :title="title" :description="description" :required="required">
    <div ref="ref"></div>
  </UiLabel>
</template>
<script>
import CodeMirror from 'codemirror/lib/codemirror.js'
import 'codemirror/lib/codemirror.css'
import 'codemirror/theme/ayu-mirage.css'
import 'codemirror/mode/python/python'
import UiLabel from '@/app/components/uiLabel'

export default {
  components: { UiLabel },
  props: {
    title: String,
    description: String,
    required: Boolean,
    value: String,
    height: Number,
  },
  data () {
    return {
      instance: null,
    }
  },
  // instance
  updated () {
    if (this.instance) {
      this.instance.setValue(this.val)
    }
  },
  computed: {
    ref () {
      return this.$refs.ref
    },
    val () {
      return this.cValue || ''
    },
    cValue: {
      get () {
        return this.value
      },
      set (val) {
        this.$emit('input', val)
      },
    },
  },
  mounted () {
    this.initCodeMirror()
  },
  methods: {
    async initCodeMirror () {
      if (!this.instance && this.ref) {
        this.instance = CodeMirror(this.ref, {
          value: this.val,
          mode: 'python',
          theme: 'ayu-mirage',
        })
        this.instance.setSize(null, this.height || 300)
        this.instance.on('change', ins => {
          this.$emit('input', ins.getValue())
        })
        setTimeout(() => {
          this.instance.refresh()
        })
      }
    },
    getValue () {
      return this.instance.getValue()
    },
    submit () {
      this.$emit('submit', this.getValue())
    },
  },
}
</script>

<style scoped>

</style>
