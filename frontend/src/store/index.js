import { createStore } from 'vuex'

export default createStore({
  state: {
    user: null,
    token: localStorage.getItem('token') || null
  },
  mutations: {
    setUser(state, user) {
      state.user = user
    },
    setToken(state, token) {
      state.token = token
      localStorage.setItem('token', token)
      console.log('Token已存储:', token)
    },
    logout(state) {
      state.user = null
      state.token = null
      localStorage.removeItem('token')
      console.log('Token已移除')
    }
  },
  actions: {
    login({ commit }, { user, token }) {
      commit('setUser', user)
      commit('setToken', token)
    },
    logout({ commit }) {
      commit('logout')
    }
  },
  getters: {
    isAuthenticated: state => !!state.token,
    currentUser: state => state.user
  }
}) 