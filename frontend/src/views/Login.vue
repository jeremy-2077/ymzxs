<template>
  <div class="login-container">
    <el-card class="login-card">
      <div class="logo">
        <h1>阳明自习室管理系统</h1>
      </div>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef">
            <el-form-item prop="email" label="邮箱">
              <el-input v-model="loginForm.email" prefix-icon="el-icon-user" placeholder="请输入邮箱"></el-input>
            </el-form-item>
            <el-form-item prop="password" label="密码">
              <el-input v-model="loginForm.password" prefix-icon="el-icon-lock" placeholder="请输入密码" show-password type="password"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" class="login-button" @click="handleLogin" :loading="loading">登录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef">
            <el-form-item prop="name" label="姓名">
              <el-input v-model="registerForm.name" placeholder="请输入姓名"></el-input>
            </el-form-item>
            <el-form-item prop="email" label="学校邮箱">
              <el-input v-model="registerForm.email" placeholder="请输入学校邮箱 (@xxx.edu.cn)"></el-input>
            </el-form-item>
            <el-form-item prop="studentId" label="学号">
              <el-input v-model="registerForm.studentId" placeholder="请输入学号 (可选)"></el-input>
            </el-form-item>
            <el-form-item prop="password" label="密码">
              <el-input v-model="registerForm.password" placeholder="请设置密码" show-password type="password"></el-input>
            </el-form-item>
            <el-form-item prop="confirmPassword" label="确认密码">
              <el-input v-model="registerForm.confirmPassword" placeholder="请确认密码" show-password type="password"></el-input>
            </el-form-item>
            <el-form-item prop="role" label="角色">
              <el-radio-group v-model="registerForm.role">
                <el-radio value="student">学生</el-radio>
                <el-radio value="admin">管理员</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" class="register-button" @click="handleRegister" :loading="registerLoading">注册</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'LoginPage',
  data() {
    // 验证密码一致性
    const validatePass = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请确认密码'));
      } else if (value !== this.registerForm.password) {
        callback(new Error('两次输入密码不一致'));
      } else {
        callback();
      }
    };
    
    // 验证邮箱是否符合学校域名
    const validateEmail = (rule, value, callback) => {
      if (!value) {
        callback(new Error('请输入邮箱'));
      } else if (!value.endsWith('edu.cn')) {
        callback(new Error('请使用学校邮箱注册 (@xxx.edu.cn)'));
      } else {
        callback();
      }
    };
    
    return {
      activeTab: 'login',
      loading: false,
      registerLoading: false,
      
      // 登录表单
      loginForm: {
        email: '',
        password: ''
      },
      loginRules: {
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
        ]
      },
      
      // 注册表单
      registerForm: {
        name: '',
        email: '',
        studentId: '',
        password: '',
        confirmPassword: '',
        role: 'student'
      },
      registerRules: {
        name: [
          { required: true, message: '请输入姓名', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
          { validator: validateEmail, trigger: 'blur' }
        ],
        studentId: [
          // { required: true, message: '请输入学号', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请确认密码', trigger: 'blur' },
          { validator: validatePass, trigger: 'blur' }
        ],
        role: [
          { required: true, message: '请选择角色', trigger: 'change' }
        ]
      },
    };
  },
  methods: {
    // 处理登录
    handleLogin() {
      this.$refs.loginFormRef.validate(async (valid) => {
        if (!valid) return;
        this.loading = true;
        try {
          console.log('开始登录请求...');
          // 登录时使用原始axios，因为此时还没有token
          const response = await axios.post('/api/auth/login', {
            email: this.loginForm.email,
            password: this.loginForm.password
          });
          console.log('登录响应:', response.data);
          
          // 正确解构 access_token 并重命名为 token
          const { user, access_token: token } = response.data; 
          
          if (!token) {
             console.error('Login successful but no token received!', response.data);
             this.$message.error('登录失败：未收到认证令牌');
             this.loading = false;
             return;
          }
          
          console.log('接收到的用户信息:', user);
          console.log('接收到的token:', token);

          this.$store.dispatch('login', { user, token });
          
          if (user && user.role) {
            this.$router.push(user.role === 'admin' ? '/admin/dashboard' : '/student/dashboard');
            this.$message.success('登录成功');
          } else {
            console.error('登录成功，但用户信息不完整:', user);
            this.$message.warning('登录成功，但无法确定用户角色，将跳转至首页');
            this.$router.push('/'); 
          }
        } catch (error) {
          console.error('登录失败:', error);
          let errorMessage = '登录失败，请检查邮箱和密码';
          if (error.response && error.response.data && (error.response.data.message || error.response.data.error) ) {
            errorMessage = error.response.data.message || error.response.data.error; 
          }
          this.$message.error(errorMessage);
        } finally {
          this.loading = false;
        }
      });
    },
    
    // 处理注册
    handleRegister() {
      this.$refs.registerFormRef.validate(async (valid) => {
        if (!valid) return;
        
        // 简单处理：不允许直接注册 admin，如果需要，应由后端或管理界面处理
        if (this.registerForm.role === 'admin') {
            this.$message.warning('不允许直接注册管理员账号');
            return;
        }
        
        this.registerLoading = true; // 使用独立的 loading 状态
        
        try {
          // 调用注册API
          const payload = {
            name: this.registerForm.name,
            email: this.registerForm.email,
            password: this.registerForm.password,
            role: this.registerForm.role, // 发送选择的角色 (虽然上面限制了admin)
            // 如果学号填写了才发送
            ...(this.registerForm.studentId && { student_id: this.registerForm.studentId })
          };
          console.log('注册信息 (Login.vue):', payload); // 确认发送的数据
          
          // 注册时使用原始axios，因为此时还没有token
          const response = await axios.post('/api/auth/register', payload);
          
          // 处理成功响应
          const responseData = response.data || {};
          this.$message.success(responseData.message || '注册成功！请返回登录');
          this.activeTab = 'login'; // 切换回登录 Tab
          // 可选：清空注册表单
          // this.$refs.registerFormRef.resetFields();
          
        } catch (error) {
          console.error('注册失败 (Login.vue):', error);
          let errorMessage = '注册失败，请稍后重试';
          if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error; // 使用后端返回的 error 信息
          }
          this.$message.error(errorMessage);
        } finally {
          this.registerLoading = false;
        }
      });
    }
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}

.login-card {
  width: 450px;
  padding: 20px 0;
}

.logo {
  text-align: center;
  margin-bottom: 20px;
}

.login-button, .register-button {
  width: 100%;
}
</style> 