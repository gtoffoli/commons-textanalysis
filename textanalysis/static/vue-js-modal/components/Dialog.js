export default {
  name: 'VueJsDialog',
  template: `
  <component
    :is="$modal.context.componentName"
    name="dialog"
    height="auto"
    :classes="['vue-dialog', params.class]"
    :width="width"
    :shift-y="0.3"
    :adaptive="true"
    :focus-trap="true"
    :clickToClose="clickToClose"
    :transition="transition"
    @before-open="beforeOpened"
    @before-close="beforeClosed"
    @opened="$emit('opened', $event)"
    @closed="$emit('closed', $event)"
  >
    <div class="vue-dialog-content">
      <div class="vue-dialog-content-title" v-if="params.title" v-html="params.title || ''" />

      <component v-if="params.component" v-bind="params.props" :is="params.component" />
      <div v-else v-html="params.text || ''" />
    </div>
    <div class="vue-dialog-buttons" v-if="buttons">
      <button
        v-for="(button, index) in buttons"
        :class="button.class || 'vue-dialog-button'"
        type="button"
        tabindex="0"
        :style="buttonStyle"
        :key="index"
        v-html="button.title"
        @click.stop="click(index, $event)"
      >{{ button.title }}</button>
    </div>
    <div v-else class="vue-dialog-buttons-none" />
  </component>
`,
  props: {
    width: {
      type: [Number, String],
      default: 400
    },
    clickToClose: {
      type: Boolean,
      default: true
    },
    transition: {
      type: String
    }
  },
  data() {
    return {
      params: {}
    }
  },
  computed: {
    buttons() {
      return this.params.buttons || []
    },
    /**
     * Returns FLEX style with correct width for arbitrary number of
     * buttons.
     */
    buttonStyle() {
      return {
        flex: `1 1 ${100 / this.buttons.length}%`
      }
    }
  },
  methods: {
    beforeOpened(event) {
      // window.addEventListener('keyup', this.onKeyUp)

      this.params = event.params || {}
      this.$emit('before-opened', event)
    },

    beforeClosed(event) {
      // window.removeEventListener('keyup', this.onKeyUp)

      this.params = {}
      this.$emit('before-closed', event)
    },

    click(buttonIndex, event, source = 'click') {
      const button = this.buttons[buttonIndex]
      const handler = button?.handler

      if (typeof handler === 'function') {
        handler(buttonIndex, event, { source })
      }
    }
  }
}