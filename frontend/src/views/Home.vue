<template>
  <div class="home">
    <div class="content">
      <h1>阳明自习室管理系统</h1>
      <el-button type="primary" @click="$router.push('/login')">登录/注册</el-button>
    </div>
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
  min-height: 100vh;
  width: 100%;
  /* 当前使用的是在线图片URL，如果您想使用本地图片，请将图片放入assets/images目录，
     然后将下面的URL改为: url('@/assets/images/your-image.jpg') */
  background-image: url('@/assets/images/top-image.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.content {
  padding: 30px;
  background-color: rgba(255, 255, 255, 0.8);
  border-radius: 10px;
  text-align: center;
}

h1 {
  margin-bottom: 20px;
}
</style> 