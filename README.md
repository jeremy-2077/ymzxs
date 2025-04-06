# 自习室座位管理系统 (YMZXS)

一个现代化的自习室座位管理系统，提供用户管理、座位预约、智能签到与设施管理功能。

## 功能特点

### 用户管理
- 支持学生和管理员两类角色
- 基于邮箱的注册验证
- 完整的用户信息管理

### 座位预约管理
- 可视化自习室座位分布图
- 实时座位状态显示
- 灵活的时段预约功能

### 智能签到与释放
- 二维码签到验证
- 超时未签到自动释放座位
- 失信记录管理

### 设施管理
- 自习室和座位的可视化管理
- 座位维修状态标记
- 批量导入导出座位数据

## 技术栈

### 后端
- Flask (Python)
- SQLAlchemy ORM
- Flask-SocketIO (实时推送)
- JWT认证
- Redis (缓存和定时任务)

### 前端
- Vue.js 3
- Element Plus UI
- Vuex 状态管理
- Socket.IO 客户端

### 数据库
- MySQL

## 快速开始

### 使用Docker Compose

1. 克隆项目
```bash
git clone https://github.com/username/ymzxs.git
cd ymzxs
```

2. 启动服务
```bash
docker-compose up -d
```

3. 访问应用
   - 前端: http://localhost:8080
   - 后端API: http://localhost:5001

### 本地开发

#### 后端
```bash
cd backend
pip install -r requirements.txt
python run.py
```

#### 前端
```bash
cd frontend
npm install
npm run serve
```

## API文档

### 认证API
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 用户API
- `GET /api/users` - 获取用户列表（管理员）
- `GET /api/users/:id` - 获取用户详情
- `PUT /api/users/:id` - 更新用户信息

### 座位API
- `GET /api/seats/rooms` - 获取自习室列表
- `GET /api/seats/rooms/:id/seats` - 获取自习室座位
- `POST /api/seats/reserve` - 预约座位
- `POST /api/seats/checkin` - 签到
- `POST /api/seats/checkout` - 签退

### 设施API
- `GET /api/facilities/rooms` - 获取自习室列表
- `POST /api/facilities/rooms/:id/seats` - 添加座位
- `PATCH /api/facilities/seats/:id/status` - 更新座位状态

## 贡献

欢迎提交问题和功能请求！

## 许可证

MIT 