<template>
  <div class="user-management">
    <!-- 搜索和工具栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="请输入用户名" clearable></el-input>
        </el-form-item>
        
        <el-form-item label="用户类型">
          <el-select v-model="searchForm.userType" placeholder="请选择" clearable>
            <el-option label="学生" value="student"></el-option>
            <el-option label="教师" value="teacher"></el-option>
            <el-option label="管理员" value="admin"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择" clearable>
            <el-option label="正常" value="active"></el-option>
            <el-option label="禁用" value="disabled"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" @click="handleSearch">搜索</el-button>
          <el-button icon="el-icon-refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
      
      <div class="action-buttons">
        <el-button type="primary" icon="el-icon-plus" @click="showAddUserDialog">添加用户</el-button>
        <el-button type="warning" icon="el-icon-download" @click="exportUsers">导出数据</el-button>
        <el-button type="info" icon="el-icon-upload2" @click="showImportDialog">批量导入</el-button>
      </div>
    </el-card>
    
    <!-- 用户列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="clearfix">
          <span>用户列表</span>
          <el-button style="float: right; padding: 3px 0" type="text" @click="refreshUserList">刷新</el-button>
        </div>
      </template>
      
      <el-table
        :data="paginatedUsers"
        border
        style="width: 100%"
        v-loading="loading">
        <el-table-column type="selection" width="55"></el-table-column>
        
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        
        <el-table-column prop="username" label="用户名" width="120"></el-table-column>
        
        <el-table-column prop="name" label="姓名" width="120"></el-table-column>
        
        <el-table-column prop="userType" label="用户类型" width="100">
          <template v-slot="scope">
            <el-tag :type="getUserTypeTag(scope.row.userType)">
              {{ getUserTypeLabel(scope.row.userType) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="email" label="邮箱" width="180"></el-table-column>
        
        <el-table-column prop="phone" label="手机号" width="130"></el-table-column>
        
        <el-table-column prop="status" label="状态" width="100">
          <template v-slot="scope">
            <el-switch
              v-model="scope.row.status"
              :active-value="'active'"
              :inactive-value="'disabled'"
              @change="handleStatusChange(scope.row)"
              active-color="#13ce66"
              inactive-color="#ff4949">
            </el-switch>
          </template>
        </el-table-column>
        
        <el-table-column prop="loginTime" label="最后登录" width="180"></el-table-column>
        
        <el-table-column label="操作" width="200">
          <template v-slot="scope">
            <el-button
              size="mini"
              type="primary"
              icon="el-icon-edit"
              @click="handleEdit(scope.row)">
              编辑
            </el-button>
            
            <el-button
              size="mini"
              type="danger"
              icon="el-icon-delete"
              @click="handleDelete(scope.row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          :current-page="pagination.currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pagination.pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredUsers.length">
        </el-pagination>
      </div>
    </el-card>
    
    <!-- 添加/编辑用户对话框 -->
    <el-dialog
      :title="editMode ? '编辑用户' : '添加用户'"
      v-model:visible="userDialogVisible"
      width="500px">
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        
        <el-form-item label="姓名" prop="name">
          <el-input v-model="userForm.name" placeholder="请输入姓名"></el-input>
        </el-form-item>
        
        <el-form-item label="用户类型" prop="userType">
          <el-select v-model="userForm.userType" placeholder="请选择用户类型">
            <el-option label="学生" value="student"></el-option>
            <el-option label="教师" value="teacher"></el-option>
            <el-option label="管理员" value="admin"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item v-if="userForm.userType === 'student'" label="学号" prop="studentId">
          <el-input v-model="userForm.studentId" placeholder="请输入学号"></el-input>
        </el-form-item>
        
        <el-form-item v-if="userForm.userType === 'teacher'" label="工号" prop="teacherId">
          <el-input v-model="userForm.teacherId" placeholder="请输入工号"></el-input>
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱"></el-input>
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userForm.phone" placeholder="请输入手机号"></el-input>
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!editMode">
          <el-input v-model="userForm.password" placeholder="请输入密码" show-password></el-input>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="userForm.status">
            <el-radio label="active">正常</el-radio>
            <el-radio label="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="备注" prop="remark">
          <el-input type="textarea" v-model="userForm.remark" placeholder="选填"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="userDialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="submitUserForm" :loading="submitting">确 定</el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 导入用户对话框 -->
    <el-dialog title="批量导入用户" v-model:visible="importDialogVisible" width="500px">
      <div class="import-tips">
        <p>请按照模板格式上传Excel文件，包含以下字段：</p>
        <ul>
          <li>用户名（必填）</li>
          <li>姓名（必填）</li>
          <li>用户类型（必填，student/teacher/admin）</li>
          <li>学号/工号（学生和教师必填）</li>
          <li>邮箱（必填）</li>
          <li>手机号（必填）</li>
          <li>密码（必填，建议设置初始密码）</li>
        </ul>
      </div>
      
      <el-upload
        action="#"
        :auto-upload="false"
        accept=".xlsx,.xls"
        :limit="1"
        :file-list="importFile"
        :on-change="handleFileChange">
        <template #trigger>
          <el-button size="small" type="primary">选择文件</el-button>
        </template>
        <template #tip>
          <div class="el-upload__tip">只能上传Excel文件，且不超过5MB</div>
        </template>
      </el-upload>
      
      <div class="download-template">
        <a href="#" @click.prevent="downloadTemplate">下载导入模板</a>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="importDialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="submitImport" :loading="importing">开始导入</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'UserManagement',
  data() {
    // 邮箱验证规则
    const validateEmail = (rule, value, callback) => {
      const emailRegex = /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/;
      if (value && !emailRegex.test(value)) {
        callback(new Error('请输入正确的邮箱格式'));
      } else {
        callback();
      }
    };
    
    // 手机号验证规则
    const validatePhone = (rule, value, callback) => {
      const phoneRegex = /^1[3456789]\d{9}$/;
      if (value && !phoneRegex.test(value)) {
        callback(new Error('请输入正确的手机号格式'));
      } else {
        callback();
      }
    };
    
    return {
      // 搜索表单
      searchForm: {
        username: '',
        userType: '',
        status: ''
      },
      
      // 用户数据
      users: [],
      filteredUsers: [],
      loading: false,
      
      // 分页
      pagination: {
        currentPage: 1,
        pageSize: 10
      },
      
      // 用户表单
      userDialogVisible: false,
      editMode: false,
      userForm: {
        id: null,
        username: '',
        name: '',
        userType: 'student',
        studentId: '',
        teacherId: '',
        email: '',
        phone: '',
        password: '',
        status: 'active',
        remark: ''
      },
      userRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
        ],
        name: [
          { required: true, message: '请输入姓名', trigger: 'blur' }
        ],
        userType: [
          { required: true, message: '请选择用户类型', trigger: 'change' }
        ],
        studentId: [
          { required: true, message: '请输入学号', trigger: 'blur' }
        ],
        teacherId: [
          { required: true, message: '请输入工号', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' },
          { validator: validateEmail, trigger: 'blur' }
        ],
        phone: [
          { required: true, message: '请输入手机号', trigger: 'blur' },
          { validator: validatePhone, trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度不能少于6个字符', trigger: 'blur' }
        ]
      },
      submitting: false,
      
      // 导入对话框
      importDialogVisible: false,
      importFile: [],
      importing: false
    };
  },
  computed: {
    // 分页后的数据
    paginatedUsers() {
      const start = (this.pagination.currentPage - 1) * this.pagination.pageSize;
      const end = start + this.pagination.pageSize;
      return this.filteredUsers.slice(start, end);
    }
  },
  mounted() {
    this.loadUsers();
  },
  methods: {
    // 获取用户类型标签样式
    getUserTypeTag(type) {
      const typeMap = {
        'student': 'primary',
        'teacher': 'success',
        'admin': 'danger'
      };
      return typeMap[type] || 'info';
    },
    
    // 获取用户类型标签文本
    getUserTypeLabel(type) {
      const typeMap = {
        'student': '学生',
        'teacher': '教师',
        'admin': '管理员'
      };
      return typeMap[type] || type;
    },
    
    // 加载用户数据
    loadUsers() {
      this.loading = true;
      
      // 模拟API请求
      setTimeout(() => {
        // 生成模拟用户数据
        this.users = [
          {
            id: 1,
            username: 'admin',
            name: '系统管理员',
            userType: 'admin',
            email: 'admin@example.com',
            phone: '13800138000',
            status: 'active',
            loginTime: '2023-06-10 12:30:45',
            remark: '超级管理员账号'
          },
          {
            id: 2,
            username: 'teacher1',
            name: '张教授',
            userType: 'teacher',
            teacherId: 'T2023001',
            email: 'teacher1@example.com',
            phone: '13900139001',
            status: 'active',
            loginTime: '2023-06-09 09:15:30',
            remark: '计算机学院教师'
          },
          {
            id: 3,
            username: 'student1',
            name: '李明',
            userType: 'student',
            studentId: 'S20230001',
            email: 'student1@example.com',
            phone: '13800138001',
            status: 'active',
            loginTime: '2023-06-10 08:45:20',
            remark: '计算机学院学生'
          },
          {
            id: 4,
            username: 'student2',
            name: '王华',
            userType: 'student',
            studentId: 'S20230002',
            email: 'student2@example.com',
            phone: '13800138002',
            status: 'active',
            loginTime: '2023-06-09 16:20:10',
            remark: '物理学院学生'
          },
          {
            id: 5,
            username: 'student3',
            name: '张三',
            userType: 'student',
            studentId: 'S20230003',
            email: 'student3@example.com',
            phone: '13800138003',
            status: 'disabled',
            loginTime: '2023-06-08 14:35:25',
            remark: '违规使用，暂时禁用'
          },
          {
            id: 6,
            username: 'teacher2',
            name: '王教授',
            userType: 'teacher',
            teacherId: 'T2023002',
            email: 'teacher2@example.com',
            phone: '13900139002',
            status: 'active',
            loginTime: '2023-06-10 10:20:15',
            remark: '文学院教师'
          },
          {
            id: 7,
            username: 'student4',
            name: '李四',
            userType: 'student',
            studentId: 'S20230004',
            email: 'student4@example.com',
            phone: '13800138004',
            status: 'active',
            loginTime: '2023-06-10 11:50:40',
            remark: ''
          },
          {
            id: 8,
            username: 'student5',
            name: '王五',
            userType: 'student',
            studentId: 'S20230005',
            email: 'student5@example.com',
            phone: '13800138005',
            status: 'active',
            loginTime: '2023-06-09 18:30:55',
            remark: ''
          },
          {
            id: 9,
            username: 'manager1',
            name: '李管理',
            userType: 'admin',
            email: 'manager1@example.com',
            phone: '13900139003',
            status: 'active',
            loginTime: '2023-06-10 09:05:30',
            remark: '设施管理员'
          },
          {
            id: 10,
            username: 'student6',
            name: '赵六',
            userType: 'student',
            studentId: 'S20230006',
            email: 'student6@example.com',
            phone: '13800138006',
            status: 'active',
            loginTime: '2023-06-10 07:25:10',
            remark: ''
          }
        ];
        
        this.filterUsers();
        this.loading = false;
      }, 500);
    },
    
    // 筛选用户
    filterUsers() {
      this.filteredUsers = this.users.filter(user => {
        // 用户名筛选
        if (this.searchForm.username && !user.username.includes(this.searchForm.username)) {
          return false;
        }
        
        // 用户类型筛选
        if (this.searchForm.userType && user.userType !== this.searchForm.userType) {
          return false;
        }
        
        // 状态筛选
        if (this.searchForm.status && user.status !== this.searchForm.status) {
          return false;
        }
        
        return true;
      });
      
      // 重置分页
      this.pagination.currentPage = 1;
    },
    
    // 搜索
    handleSearch() {
      this.filterUsers();
    },
    
    // 重置搜索
    resetSearch() {
      this.searchForm = {
        username: '',
        userType: '',
        status: ''
      };
      this.filterUsers();
    },
    
    // 刷新用户列表
    refreshUserList() {
      this.loadUsers();
    },
    
    // 分页相关方法
    handleSizeChange(val) {
      this.pagination.pageSize = val;
    },
    
    handleCurrentChange(val) {
      this.pagination.currentPage = val;
    },
    
    // 显示添加用户对话框
    showAddUserDialog() {
      this.editMode = false;
      this.userForm = {
        id: null,
        username: '',
        name: '',
        userType: 'student',
        studentId: '',
        teacherId: '',
        email: '',
        phone: '',
        password: '',
        status: 'active',
        remark: ''
      };
      
      this.userDialogVisible = true;
      this.$nextTick(() => {
        this.$refs.userFormRef.clearValidate();
      });
    },
    
    // 编辑用户
    handleEdit(row) {
      this.editMode = true;
      this.userForm = {
        id: row.id,
        username: row.username,
        name: row.name,
        userType: row.userType,
        studentId: row.studentId || '',
        teacherId: row.teacherId || '',
        email: row.email,
        phone: row.phone,
        status: row.status,
        remark: row.remark || ''
      };
      
      this.userDialogVisible = true;
      this.$nextTick(() => {
        this.$refs.userFormRef.clearValidate();
      });
    },
    
    // 改变用户状态
    handleStatusChange(row) {
      const statusText = row.status === 'active' ? '启用' : '禁用';
      this.$message.success(`已${statusText}用户：${row.username}`);
      
      // 实际应用中应该调用API
    },
    
    // 删除用户
    handleDelete(row) {
      this.$confirm(`确定要删除用户"${row.username}"吗？此操作不可恢复！`, '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }).then(() => {
        // 模拟API请求
        // 从本地数据中删除
        this.users = this.users.filter(u => u.id !== row.id);
        this.filterUsers();
        this.$message.success(`用户"${row.username}"已删除`);
      }).catch(() => {});
    },
    
    // 提交用户表单
    submitUserForm() {
      this.$refs.userFormRef.validate(valid => {
        if (!valid) return;
        
        this.submitting = true;
        
        // 模拟API请求
        setTimeout(() => {
          if (this.editMode) {
            // 更新用户
            const index = this.users.findIndex(u => u.id === this.userForm.id);
            if (index !== -1) {
              this.users[index] = { ...this.users[index], ...this.userForm };
              this.$message.success(`用户"${this.userForm.username}"更新成功`);
            }
          } else {
            // 添加用户
            const newId = Math.max(...this.users.map(u => u.id), 0) + 1;
            const newUser = {
              ...this.userForm,
              id: newId,
              loginTime: '从未登录'
            };
            
            this.users.push(newUser);
            this.$message.success(`用户"${this.userForm.username}"添加成功`);
          }
          
          this.filterUsers();
          this.userDialogVisible = false;
          this.submitting = false;
        }, 1000);
      });
    },
    
    // 导出用户数据
    exportUsers() {
      this.$message.info('正在导出用户数据，请稍候...');
      
      // 模拟导出过程
      setTimeout(() => {
        this.$message.success('用户数据导出成功');
      }, 1000);
    },
    
    // 显示导入对话框
    showImportDialog() {
      this.importDialogVisible = true;
      this.importFile = [];
    },
    
    // 文件变更处理
    handleFileChange(file) {
      this.importFile = [file];
    },
    
    // 下载模板
    downloadTemplate() {
      this.$message.info('模板下载功能正在开发中');
    },
    
    // 提交导入
    submitImport() {
      if (this.importFile.length === 0) {
        this.$message.warning('请选择Excel文件');
        return;
      }
      
      this.importing = true;
      
      // 模拟导入过程
      setTimeout(() => {
        this.importing = false;
        this.importDialogVisible = false;
        this.$message.success('已成功导入50个用户');
        this.loadUsers();
      }, 1500);
    }
  },
  watch: {
    // 监听用户类型变化，重置相关字段
    'userForm.userType': function(newVal) {
      if (newVal === 'student') {
        this.userForm.teacherId = '';
      } else if (newVal === 'teacher') {
        this.userForm.studentId = '';
      } else {
        this.userForm.studentId = '';
        this.userForm.teacherId = '';
      }
    }
  }
};
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.search-form {
  margin-bottom: 15px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.import-tips {
  margin-bottom: 20px;
}

.import-tips ul {
  padding-left: 20px;
  color: #606266;
}

.download-template {
  margin-top: 10px;
  text-align: right;
}
</style> 