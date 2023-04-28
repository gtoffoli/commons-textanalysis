import Plugin from './Plugin.js'

export { default as Modal } from './components/Modal.js'
export { default as Dialog } from './components/Dialog.js'
// export { default as ModalsContainer } from './components/ModalsContainer.vue'

export const version = '__VERSION__'

// Install by default if using the script tag
// if (typeof window !== 'undefined' && window.Vue) {
//   window.Vue.use(install)
// }

export default Plugin
