<template>
  <UiLabel :title="title" :description="description" :required="required" class="w-full q-rich-text">
    <div class="ui-rich-text-editor">
      <div class="quill-container">
        <div ref="hook"></div>
      </div>
    </div>
  </UiLabel>
</template>

<script>
import Quill from 'quill'
import 'quill/dist/quill.snow.css'
import UiLabel from '@/app/components/uiLabel'

export default {
  name: 'uiRichTextEditor',
  components: { UiLabel },
  props: ['title', 'description', 'value', 'placeholder', 'required'],
  data () {
    return {
      quill: null,
    }
  },
  computed: {
    cValue: {
      get () {
        return this.value
      },
      set (val) {
        this.$emit('input', val)
      },
    },
  },
  watch: {
    value () {
      this.onValueChange()
    },
  },
  methods: {
    onValueChange () {
      if (this.quill.root.innerHTML !== this.value) {
        const delta = this.quill.clipboard.convert(this.value)
        this.quill.setContents(delta, 'silent')
      }
    },
  },
  async mounted () {
    await this.$nextTick()
    this.quill = new Quill(this.$refs.hook, {
      height: 300,
      modules: {
        clipboard: {
          matchVisual: false
        },
        toolbar: [
          [{ size: ['small', false, 'large', 'huge'] }],
          ['bold', 'italic', 'underline', 'strike'],
          [{ list: 'ordered' }, { list: 'bullet' }],
          ['image'],
        ],
      },
      theme: 'snow',
      placeholder: this.placeholder,
    })
    this.onValueChange()
    this.quill.on('text-change', (delta, oldDelta, source) => {
      var value = this.quill.root.innerHTML
      if (value === '<p><br></p>') {
        value = this.quill.root.innerHTML.replace('<p><br></p>', '')
      }
      this.cValue = value
    })
  },
}
</script>

<style>

.quill-container {
  height: 300px;
  position: relative;
  background: #fff;
  overflow: auto;
}

.ql-container {
  height: calc(100% - 50px);
}
</style>
