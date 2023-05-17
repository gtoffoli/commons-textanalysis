/* FROM project https://github.com/fabiofranchino/vue-drop-image-and-preview/
   and https://www.fabiofranchino.com/blog/build-drag-drop-image-component-vue/ */

/* USE
<template>
  <div id="app">
      <DropAnImage />
  </div>
</template>
*/

export default {
  name: 'DropAnImage',
  template: `
  <div class="drop" 
    :class="getClasses" 
    @dragover.prevent="dragOver" 
    @dragleave.prevent="dragLeave"
    @drop.prevent="drop($event)">

      <img :src="imageSource" v-if="imageSource" />
      <h1 v-if="wrongFile">Wrong file type</h1>
      <h1 v-if="!imageSource && !isDragging && !wrongFile" style="text-align: center;">{{ drop_prompt }}</h1>

  </div>
`,
  props: {
	drop_prompt: '',
	file_type: '',
  },
  data(){
    return{
      isDragging:false,
      wrongFile:false,
      imageSource:null
    }
  },
  computed:{
    getClasses(){
      return {isDragging: this.isDragging}
    }
  },
  methods:{
    dragOver(){
      this.isDragging = true
    },
    dragLeave(){
      this.isDragging = false
    },
    drop(e){
      let files = e.dataTransfer.files
      this.wrongFile = false
      // allows only 1 file
      if (files.length === 1) {
        let file = files[0]
        // allows image only
        // if (file.type.indexOf('image/') >= 0) {
        if (file.type.indexOf(file_type) >= 0) {
          var reader = new FileReader()
          reader.onload = f => {
            // this.imageSource = f.target.result
            this.imageSource = f.target.result
            this.isDragging = false
          }
          reader.readAsDataURL(file)
        }else{
          this.wrongFile = true
          this.imageSource = null
          this.isDragging = false
        }
      }
    },
    onRequestUploadFiles(){
      
    }
  }
}
