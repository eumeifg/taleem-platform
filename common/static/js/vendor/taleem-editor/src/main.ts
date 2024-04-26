import App from './App.vue'
import store from './app/store/index'
import Vue from 'vue'

Vue.config.silent = true

new Vue({
  store,
  render: h => h(App),
}).$mount('#app')
