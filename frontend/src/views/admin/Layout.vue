<template>
  <div class="app-container">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside width="230px">
        <div class="logo-container">
          <h3>自习室管理后台</h3>
        </div>
        <el-menu 
          :default-active="activeMenu" 
          router 
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF">
          
          <el-menu-item index="/admin">
            <i class="el-icon-s-home"></i>
            <template #title>控制台</template>
          </el-menu-item>
          
          <el-menu-item index="/admin/users">
            <i class="el-icon-user"></i>
            <template #title>用户管理</template>
          </el-menu-item>
          
          <el-submenu index="facility">
            <template #title>
              <i class="el-icon-office-building"></i>
              <span>设施管理</span>
            </template>
            <el-menu-item index="/admin/study-rooms">
              <i class="el-icon-house"></i>
              <span>自习室管理</span>
            </el-menu-item>
            <el-menu-item index="/admin/facility">
              <i class="el-icon-chair"></i>
              <span>座位管理</span>
            </el-menu-item>
          </el-submenu>
          
          <el-menu-item index="/admin/reports">
            <i class="el-icon-data-analysis"></i>
            <template #title>数据报表</template>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主体区域 -->
      <el-container>
        <!-- 头部区域 -->
        <el-header>
          <div class="header-left">
            <i class="el-icon-s-fold" @click="toggleSidebar"></i>
          </div>
          
          <div class="header-right">
            <el-badge :value="3" class="notification-badge">
              <i class="el-icon-bell"></i>
            </el-badge>
            
            <el-dropdown trigger="click" @command="handleCommand">
              <span class="user-dropdown">
                {{ currentUser.name }}
                <i class="el-icon-arrow-down"></i>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                  <el-dropdown-item command="settings">系统设置</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 内容区域 -->
        <el-main>
          <div class="content-header">
            <h2>{{ $route.meta.title || '管理后台' }}</h2>
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
export default {
  name: 'AdminLayout',
  data() {
    return {
      sidebarCollapsed: false
    };
  },
  computed: {
    activeMenu() {
      return this.$route.path;
    },
    currentUser() {
      return this.$store.getters.currentUser || { name: '管理员' };
    }
  },
  methods: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
    },
    handleCommand(command) {
      if (command === 'logout') {
        this.$store.dispatch('logout');
        this.$router.push('/login');
        this.$message.success('已退出登录');
      } else if (command === 'profile') {
        // 跳转到个人信息页
        this.$message.info('个人信息页面正在开发中');
      } else if (command === 'settings') {
        // 跳转到系统设置页
        this.$message.info('系统设置页面正在开发中');
      }
    }
  }
};
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  color: white;
  height: 100%;
  transition: width 0.3s;
}

.logo-container {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: white;
  font-size: 18px;
  background-color: #263445;
}

.el-header {
  background-color: #fff;
  color: #333;
  line-height: 60px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-left i {
  font-size: 20px;
  cursor: pointer;
}

.header-right {
  display: flex;
  align-items: center;
}

.notification-badge {
  margin-right: 20px;
  cursor: pointer;
}

.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
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