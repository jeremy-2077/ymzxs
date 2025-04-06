<template>
  <div class="home">
    <h1>自习室座位管理系统</h1>
    <el-button type="primary" @click="$router.push('/login')">登录/注册</el-button>
  </div>
</template>

<script>
export default {
  name: 'HomePage'
}
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 70vh;
}
</style> 