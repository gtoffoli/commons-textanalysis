import { inRange, windowWidthWithoutScrollbar } from '../utils/index.js'

export default {
  name: 'VueJsModalResizer',
  template: `
  <div>
    <div v-if="this.resizeEdges.includes('t')" class="vue-modal-top"></div>
    <div v-if="this.resizeEdges.includes('b')" class="vue-modal-bottom"></div>
    <div v-if="this.resizeEdges.includes('l')" class="vue-modal-left"></div>
    <div v-if="this.resizeEdges.includes('r')" class="vue-modal-right"></div>
    <div v-if="this.resizeEdges.includes('tr')" class="vue-modal-topRight"></div>
    <div v-if="this.resizeEdges.includes('tl')" class="vue-modal-topLeft"></div>
    <div v-if="this.resizeEdges.includes('br')" :id="getID" :class="className"></div>
    <div v-if="this.resizeEdges.includes('bl')" class="vue-modal-bottomLeft"></div>
  </div>
 `,
  props: {
    minHeight: {
      type: Number,
      default: 0
    },
    minWidth: {
      type: Number,
      default: 0
    },
    maxWidth: {
      type: Number,
      default: Number.MAX_SAFE_INTEGER
    },
    maxHeight: {
      type: Number,
      default: Number.MAX_SAFE_INTEGER
    },
    viewportWidth: {
      type: Number,
      required: true
    },
    viewportHeight: {
      type: Number,
      required: true
    },
    resizeIndicator: {
      type: Boolean,
      default: true
    },
    resizeEdges: {
      type: Array,
      required: true
    }
  },
  data() {
    return {
      clicked: false,
      targetClass: '',
      size: {},
      initialX: 0,
      initialY: 0
    }
  },
  mounted() {
    this.$el.addEventListener('mousedown', this.start, false)
  },
  computed: {
    className() {
      const { clicked } = this
      return ['vue-modal-bottomRight', { clicked }]
    },
    getID() {
      if (this.resizeIndicator) return 'vue-modal-triangle'
      else return ''
    }
  },
  methods: {
    start(event) {
      this.targetClass = event.target.className
      this.clicked = true
      this.initialX = event.clientX
      this.initialY = event.clientY

      window.addEventListener('mousemove', this.mousemove, false)
      window.addEventListener('mouseup', this.stop, false)

      event.stopPropagation()
      event.preventDefault()
    },

    stop() {
      this.clicked = false
      this.clicked = false
      this.targetClass = ''
      this.initialX = 0
      this.initialY = 0

      window.removeEventListener('mousemove', this.mousemove, false)
      window.removeEventListener('mouseup', this.stop, false)

      this.$emit('resize-stop', {
        element: this.$el.parentElement,
        size: this.size
      })
    },

    mousemove(event) {
      this.resize(event)
    },
    resize(event) {
      var el = this.$el.parentElement

      var width = event.clientX
      var height = event.clientY
      var styleWidth = parseInt(el.style.width.replace('px', ''))
      var styleHeight = parseInt(el.style.height.replace('px', ''))

      //Block Resize if mouse outside visable space.
      if (event.clientX > this.viewportWidth || event.clientX < 0) return
      if (event.clientY > this.viewportHeight || event.clientY < 0) return

      //Calcualte new  Widht/Height based on direction
      if (el) {
        switch (this.targetClass) {
          case 'vue-modal-right':
            width = width - el.offsetLeft
            height = styleHeight
            break
          case 'vue-modal-left':
            height = styleHeight
            width = styleWidth + (this.initialX - event.clientX)
            break
          case 'vue-modal-top':
            width = styleWidth
            height = styleHeight + (this.initialY - event.clientY)
            break
          case 'vue-modal-bottom':
            width = styleWidth
            height = height - el.offsetTop
            break
          case 'vue-modal-bottomRight':
            width = width - el.offsetLeft
            height = height - el.offsetTop
            break
          case 'vue-modal-topRight':
            width = width - el.offsetLeft
            height = styleHeight + (this.initialY - event.clientY)
            break
          case 'vue-modal-bottomLeft':
            width = styleWidth + (this.initialX - event.clientX)
            height = height - el.offsetTop
            break
          case 'vue-modal-topLeft':
            width = styleWidth + (this.initialX - event.clientX)
            height = styleHeight + (this.initialY - event.clientY)
            break
          default:
            console.error('Incorrrect/no resize direction.')
        }

        const maxWidth = Math.min(windowWidthWithoutScrollbar(), this.maxWidth)
        const maxHeight = Math.min(window.innerHeight, this.maxHeight)
        width = inRange(this.minWidth, maxWidth, width)
        height = inRange(this.minHeight, maxHeight, height)
        this.initialX = event.clientX
        this.initialY = event.clientY

        this.size = { width, height }

        //Calculate growth in each dimension to be used when shifting the modal.
        const dimGrowth = {
          width: width - styleWidth,
          height: height - styleHeight
        }

        el.style.width = width + 'px'
        el.style.height = height + 'px'
        this.$emit('resize', {
          element: el,
          size: this.size,
          direction: this.targetClass,
          dimGrowth: dimGrowth
        })
      }
    }
  }
}