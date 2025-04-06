import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import store from './store'
import axios from 'axios'

// 配置全局axios拦截器
axios.interceptors.request.use(
  config => {
    const token = store.state.token
    console.log('拦截器中的token:', token)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('添加Authorization头:', config.headers.Authorization)
    } else {
      console.log('没有找到token，不添加Authorization头')
    }
    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器，处理常见错误
axios.interceptors.response.use(
  response => {
    console.log('响应拦截器:', response.status)
    return response
  },
  error => {
    console.error('响应拦截器错误:', error)
    // 处理401未授权错误
    if (error.response && error.response.status === 401) {
      console.error('401未授权错误，执行登出操作')
      store.dispatch('logout')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)

app.use(ElementPlus)
app.use(router)
app.use(store)

// 全局注册axios，使其在组件中可通过this.$axios访问
app.config.globalProperties.$axios = axios

app.mount('#app') 