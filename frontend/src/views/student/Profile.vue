<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <h2>个人信息</h2>
        </div>
      </template>
      
      <el-form :model="userForm" :rules="rules" ref="userForm" label-width="80px" v-loading="loading">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" disabled></el-input>
        </el-form-item>
        
        <el-form-item label="学号" prop="studentId">
          <el-input v-model="userForm.studentId" disabled></el-input>
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email"></el-input>
        </el-form-item>
        
        <el-form-item label="姓名" prop="name">
          <el-input v-model="userForm.name"></el-input>
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userForm.phone"></el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="saveProfile">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="password-card">
      <template #header>
        <div class="card-header">
          <h2>修改密码</h2>
        </div>
      </template>
      
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordForm" label-width="100px" v-loading="passwordLoading">
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password"></el-input>
        </el-form-item>
        
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password"></el-input>
        </el-form-item>
        
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password"></el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="changePassword">修改密码</el-button>
          <el-button @click="resetPasswordForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'StudentProfile',
  data() {
    // 验证密码
    const validateNewPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入新密码'))
      } else if (value.length < 6) {
        callback(new Error('密码长度不能小于6位'))
      } else {
        if (this.passwordForm.confirmPassword !== '') {
          this.$refs.passwordForm.validateField('confirmPassword')
        }
        callback()
      }
    }
    
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入新密码'))
      } else if (value !== this.passwordForm.newPassword) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    }
    
    return {
      loading: false,
      passwordLoading: false,
      userForm: {
        username: '',
        studentId: '',
        email: '',
        name: '',
        phone: ''
      },
      passwordForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      rules: {
        email: [
          { required: true, message: '请输入邮箱地址', trigger: 'blur' },
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ],
        name: [
          { required: true, message: '请输入姓名', trigger: 'blur' }
        ],
        phone: [
          { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
        ]
      },
      passwordRules: {
        currentPassword: [
          { required: true, message: '请输入当前密码', trigger: 'blur' }
        ],
        newPassword: [
          { required: true, validator: validateNewPassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, validator: validateConfirmPassword, trigger: 'blur' }
        ]
      }
    }
  },
  created() {
    this.fetchUserProfile()
  },
  methods: {
    fetchUserProfile() {
      this.loading = true
      axios.get('/api/user/profile')
        .then(response => {
          const data = response.data
          this.userForm = {
            username: data.username,
            studentId: data.student_id,
            email: data.email || '',
            name: data.name || '',
            phone: data.phone || ''
          }
          this.loading = false
        })
        .catch(error => {
          this.loading = false
          console.error('获取用户信息失败', error)
          this.$message.error('获取用户信息失败')
        })
    },
    saveProfile() {
      this.$refs.userForm.validate(valid => {
        if (valid) {
          this.loading = true
          axios.put('/api/user/profile', {
            email: this.userForm.email,
            name: this.userForm.name,
            phone: this.userForm.phone
          })
            .then(response => {
              this.loading = false
              this.$message.success('个人信息更新成功')
            })
            .catch(error => {
              this.loading = false
              console.error('更新用户信息失败', error)
              this.$message.error('更新个人信息失败')
            })
        }
      })
    },
    changePassword() {
      this.$refs.passwordForm.validate(valid => {
        if (valid) {
          this.passwordLoading = true
          axios.put('/api/user/change-password', {
            current_password: this.passwordForm.currentPassword,
            new_password: this.passwordForm.newPassword
          })
            .then(response => {
              this.passwordLoading = false
              this.$message.success('密码修改成功')
              this.resetPasswordForm()
            })
            .catch(error => {
              this.passwordLoading = false
              if (error.response && error.response.data && error.response.data.message) {
                this.$message.error(error.response.data.message)
              } else {
                this.$message.error('密码修改失败')
              }
            })
        }
      })
    },
    resetPasswordForm() {
      this.$refs.passwordForm.resetFields()
    }
  }
}
</script>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.profile-card, .password-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}
</style> 