<template>
  <div class="dashboard-container">
    <!-- 统计卡片区 -->
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-header">
            <div class="stat-title">今日预约</div>
            <i class="el-icon-date stat-icon"></i>
          </div>
          <div class="stat-number">{{ stats.todayReservations }}</div>
          <div class="stat-footer">
            <span>查看详情</span>
            <i class="el-icon-right"></i>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-header">
            <div class="stat-title">待签到</div>
            <i class="el-icon-s-check stat-icon"></i>
          </div>
          <div class="stat-number">{{ stats.pendingReservations }}</div>
          <div class="stat-footer">
            <span>立即签到</span>
            <i class="el-icon-right"></i>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-header">
            <div class="stat-title">本月学习时长</div>
            <i class="el-icon-timer stat-icon"></i>
          </div>
          <div class="stat-number">{{ stats.studyHours }}小时</div>
          <div class="stat-footer">
            <span>查看统计</span>
            <i class="el-icon-right"></i>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8" :lg="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-header">
            <div class="stat-title">失信记录</div>
            <i class="el-icon-warning-outline stat-icon"></i>
          </div>
          <div class="stat-number">{{ stats.failedCheckins }}</div>
          <div class="stat-footer">
            <span>良好信用</span>
            <i class="el-icon-right"></i>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近预约 -->
    <el-card class="recent-card">
      <template #header>
        <div class="recent-header">
          <span>最近预约</span>
          <el-button type="text" @click="$router.push('/student/my-reservations')">查看全部</el-button>
        </div>
      </template>
      
      <el-table :data="recentReservations" stripe style="width: 100%" v-loading="loading.reservations">
        <el-table-column prop="room" label="自习室" width="180"></el-table-column>
        <el-table-column prop="seat" label="座位号" width="120"></el-table-column>
        <el-table-column prop="date" label="日期" width="180"></el-table-column>
        <el-table-column prop="time" label="时间段"></el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button 
              v-if="scope.row.status === 'pending'" 
              type="primary" 
              size="mini" 
              @click="handleCheckIn(scope.row)">
              签到
            </el-button>
            <el-button 
              v-if="scope.row.status === 'active'" 
              type="danger" 
              size="mini" 
              @click="handleCheckOut(scope.row)">
              签退
            </el-button>
            <el-button 
              v-if="scope.row.status === 'pending'" 
              type="danger" 
              size="mini" 
              @click="handleCancel(scope.row)">
              取消
            </el-button>
            <span v-if="scope.row.status === 'completed' || scope.row.status === 'cancelled' || scope.row.status === 'expired'">
              --
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 自习室状态 -->
    <el-card class="room-card">
      <template #header>
        <div class="room-header">
          <span>自习室状态</span>
          <el-button type="text" @click="$router.push('/student/seat-map')">预约座位</el-button>
        </div>
      </template>
      
      <el-row :gutter="20" v-loading="loading.rooms">
        <el-col :span="8" v-for="room in rooms" :key="room.id">
          <el-card shadow="hover" class="inner-card">
            <h3>{{ room.name }}</h3>
            <div class="room-stats">
              <div class="stat-item">
                <div class="label">总座位</div>
                <div class="value">{{ room.totalSeats }}</div>
              </div>
              <div class="stat-item">
                <div class="label">空闲</div>
                <div class="value available">{{ room.availableSeats }}</div>
              </div>
              <div class="stat-item">
                <div class="label">使用中</div>
                <div class="value occupied">{{ room.occupiedSeats }}</div>
              </div>
            </div>
            <div class="room-footer">
              <el-button type="primary" @click="goToRoom(room.id)">查看详情</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'StudentDashboard',
  data() {
    return {
      // 统计数据
      stats: {
        todayReservations: 0,
        pendingReservations: 0,
        studyHours: 0,
        failedCheckins: 0
      },
      
      // 最近预约
      recentReservations: [],
      
      // 自习室数据
      rooms: [],
      
      // 加载状态
      loading: {
        stats: false,
        reservations: false,
        rooms: false
      }
    };
  },
  mounted() {
    this.fetchDashboardStats();
    this.fetchRecentReservations();
    this.fetchRoomsStatus();
  },
  methods: {
    // 获取仪表板统计数据
    async fetchDashboardStats() {
      this.loading.stats = true;
      try {
        const response = await axios.get('/api/seats/dashboard/stats');
        this.stats.todayReservations = response.data.today_reservations;
        this.stats.pendingReservations = response.data.pending_reservations;
        this.stats.studyHours = response.data.study_hours;
        this.stats.failedCheckins = response.data.failed_checkins;
      } catch (error) {
        console.error('获取仪表板统计数据失败:', error);
        this.$message.error('获取统计数据失败，请稍后重试');
      } finally {
        this.loading.stats = false;
      }
    },
    
    // 获取最近预约
    async fetchRecentReservations() {
      this.loading.reservations = true;
      try {
        const response = await axios.get('/api/seats/dashboard/recent_reservations');
        this.recentReservations = response.data;
      } catch (error) {
        console.error('获取最近预约失败:', error);
        this.$message.error('获取最近预约失败，请稍后重试');
      } finally {
        this.loading.reservations = false;
      }
    },
    
    // 获取自习室状态
    async fetchRoomsStatus() {
      this.loading.rooms = true;
      try {
        const response = await axios.get('/api/seats/dashboard/rooms_status');
        this.rooms = response.data;
      } catch (error) {
        console.error('获取自习室状态失败:', error);
        this.$message.error('获取自习室状态失败，请稍后重试');
      } finally {
        this.loading.rooms = false;
      }
    },
    
    // 根据状态获取标签类型
    getStatusType(status) {
      const types = {
        'pending': 'warning',
        'active': 'success',
        'completed': 'info',
        'cancelled': 'danger',
        'expired': 'warning'
      };
      return types[status] || 'info';
    },
    
    // 获取状态文本
    getStatusText(status) {
      const texts = {
        'pending': '待签到',
        'active': '使用中',
        'completed': '已完成',
        'cancelled': '已取消',
        'expired': '已过期'
      };
      return texts[status] || '未知状态';
    },
    
    // 签到
    handleCheckIn(reservation) {
      // 跳转到签到页面
      this.$router.push('/student/check-in');
    },
    
    // 签退
    handleCheckOut(reservation) {
      // 跳转到签退页面
      this.$router.push('/student/check-in');
    },
    
    // 取消预约
    handleCancel(reservation) {
      this.$confirm('确定要取消该预约吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await axios.post(`/api/seats/reservations/${reservation.id}/cancel`);
          this.$message.success('预约已取消');
          // 刷新数据
          this.fetchRecentReservations();
          this.fetchDashboardStats();
        } catch (error) {
          console.error('取消预约失败:', error);
          this.$message.error('取消预约失败，请稍后重试');
        }
      }).catch(() => {
        this.$message.info('已取消操作');
      });
    },
    
    // 前往自习室详情
    goToRoom(roomId) {
      this.$router.push(`/student/seat-map?room=${roomId}`);
    }
  }
};
</script>

<style scoped>
.dashboard-container {
  padding: 20px 0;
}

.stat-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.stat-title {
  font-size: 16px;
  color: #606266;
}

.stat-icon {
  font-size: 22px;
  color: #409EFF;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  margin: 10px 0;
}

.stat-footer {
  margin-top: 10px;
  color: #409EFF;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.recent-card, .room-card {
  margin-bottom: 20px;
}

.recent-header, .room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.inner-card {
  text-align: center;
  margin-bottom: 20px;
}

.room-stats {
  display: flex;
  justify-content: space-around;
  margin: 15px 0;
}

.stat-item {
  text-align: center;
}

.label {
  font-size: 12px;
  color: #909399;
}

.value {
  font-size: 18px;
  font-weight: bold;
  margin-top: 5px;
}

.available {
  color: #67C23A;
}

.occupied {
  color: #F56C6C;
}

.room-footer {
  margin-top: 15px;
}
</style> 