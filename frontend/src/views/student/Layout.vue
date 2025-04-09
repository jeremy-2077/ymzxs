<template>
  <div class="app-container">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="220px">
        <div class="logo-container">
          <h3>阳明自习室管理系统</h3>
        </div>
        <el-menu 
          :default-active="activeMenu" 
          router 
          background-color="#001529"
          text-color="#fff"
          active-text-color="#ffd04b">
          
          <el-menu-item index="/student/dashboard">
            <i class="el-icon-s-home"></i>
            <span>首页</span>
          </el-menu-item>
          
          <el-menu-item index="/student/seat-map">
            <i class="el-icon-s-grid"></i>
            <span>座位预约</span>
          </el-menu-item>
          
          <el-menu-item index="/student/my-reservations">
            <i class="el-icon-tickets"></i>
            <span>我的预约</span>
          </el-menu-item>
          
          <el-menu-item index="/student/checkin">
            <i class="el-icon-s-check"></i>
            <span>签到/签退</span>
          </el-menu-item>
          
          <el-menu-item index="/student/profile">
            <i class="el-icon-user"></i>
            <span>个人信息</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主体区域 -->
      <el-container>
        <!-- 头部区域 -->
        <el-header>
          <div class="header-right">
            <el-dropdown trigger="click" @command="handleCommand">
              <span class="user-dropdown">
                {{ currentUser.name }}
                <i class="el-icon-arrow-down"></i>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 内容区域 -->
        <el-main>
          <div class="content-header">
            <h2>{{ $route.meta.title || '首页' }}</h2>
          </div>
          <div class="content-body">
            <router-view></router-view>
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';

export default {
  name: 'StudentLayout',
  setup() {
    const store = useStore();
    const router = useRouter();
    const route = useRoute();

    const activeMenu = computed(() => route.path);
    const currentUser = computed(() => store.getters.currentUser || { name: '未登录' });

    const handleCommand = (command) => {
      if (command === 'logout') {
        store.dispatch('logout');
        router.push('/login');
        ElMessage.success('已退出登录');
      } else if (command === 'profile') {
        router.push('/student/profile');
      }
    };

    return {
      activeMenu,
      currentUser,
      handleCommand,
    };
  }
};
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.el-aside {
  background-color: #001529;
  color: white;
  height: 100%;
}

.logo-container {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: white;
  font-size: 16px;
  border-bottom: 1px solid #1f2d3d;
}

.el-header {
  background-color: #fff;
  color: #333;
  line-height: 60px;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 0 20px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  cursor: pointer;
  color: #333;
}

.content-header {
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.content-body {
  padding: 0;
  margin: 0;
}
</style> 