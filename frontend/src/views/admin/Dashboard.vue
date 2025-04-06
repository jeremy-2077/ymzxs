<template>
  <div class="dashboard-container">
    <!-- 数据概览卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="data-card" shadow="hover">
          <template #header>
            <div class="clearfix">
              <span>总用户数</span>
            </div>
          </template>
          <div class="data-content">
            <div class="data-number">1,208</div>
            <div class="data-icon">
              <i class="el-icon-user"></i>
            </div>
          </div>
          <div class="data-footer">
            <span class="data-trend up">
              <i class="el-icon-top"></i> 12% 本周
            </span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="data-card" shadow="hover">
          <template #header>
            <div class="clearfix">
              <span>当前在线人数</span>
            </div>
          </template>
          <div class="data-content">
            <div class="data-number">328</div>
            <div class="data-icon" style="background-color: #67C23A;">
              <i class="el-icon-connection"></i>
            </div>
          </div>
          <div class="data-footer">
            <span class="data-trend up">
              <i class="el-icon-top"></i> 5% 同比昨日
            </span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="data-card" shadow="hover">
          <template #header>
            <div class="clearfix">
              <span>今日预约数</span>
            </div>
          </template>
          <div class="data-content">
            <div class="data-number">156</div>
            <div class="data-icon" style="background-color: #E6A23C;">
              <i class="el-icon-tickets"></i>
            </div>
          </div>
          <div class="data-footer">
            <span class="data-trend down">
              <i class="el-icon-bottom"></i> 3% 同比昨日
            </span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="data-card" shadow="hover">
          <template #header>
            <div class="clearfix">
              <span>座位使用率</span>
            </div>
          </template>
          <div class="data-content">
            <div class="data-number">68%</div>
            <div class="data-icon" style="background-color: #F56C6C;">
              <i class="el-icon-data-line"></i>
            </div>
          </div>
          <div class="data-footer">
            <span class="data-trend up">
              <i class="el-icon-top"></i> 8% 同比昨日
            </span>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表与数据分析 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="clearfix">
              <span>自习室使用统计</span>
              <el-radio-group v-model="chartView" size="mini" style="float: right;">
                <el-radio-button label="daily">日视图</el-radio-button>
                <el-radio-button label="weekly">周视图</el-radio-button>
                <el-radio-button label="monthly">月视图</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container">
            <div ref="roomUsageChart" style="width: 100%; height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="clearfix">
              <span>预约时段分布</span>
            </div>
          </template>
          <div class="chart-container">
            <div ref="timeDistChart" style="width: 100%; height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最新动态与预约记录 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="clearfix">
              <span>最新预约</span>
              <el-button style="float: right; padding: 3px 0" type="text">查看全部</el-button>
            </div>
          </template>
          <div class="table-container">
            <el-table :data="latestBookings" stripe style="width: 100%">
              <el-table-column prop="username" label="用户" width="120"></el-table-column>
              <el-table-column prop="studyRoom" label="自习室" width="180"></el-table-column>
              <el-table-column prop="seatNumber" label="座位号" width="100"></el-table-column>
              <el-table-column prop="timeSlot" label="时间段"></el-table-column>
              <el-table-column prop="status" label="状态" width="100">
                <template v-slot="scope">
                  <el-tag :type="getStatusType(scope.row.status)">{{ scope.row.status }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="clearfix">
              <span>系统日志</span>
              <el-button style="float: right; padding: 3px 0" type="text">查看全部</el-button>
            </div>
          </template>
          <div class="timeline-container">
            <el-timeline>
              <el-timeline-item
                v-for="(activity, index) in systemLogs"
                :key="index"
                :type="activity.type"
                :color="getLogColor(activity.type)"
                :timestamp="activity.timestamp">
                {{ activity.content }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 自习室占用情况 -->
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="clearfix">
          <span>自习室占用情况</span>
          <el-button style="float: right; padding: 3px 0" type="text" @click="refreshRoomStatus">刷新</el-button>
        </div>
      </template>
      <div class="room-status-container">
        <el-table :data="roomsStatus" stripe style="width: 100%">
          <el-table-column prop="roomName" label="自习室名称"></el-table-column>
          <el-table-column prop="totalSeats" label="总座位数" width="120"></el-table-column>
          <el-table-column prop="occupiedSeats" label="已占用" width="120"></el-table-column>
          <el-table-column prop="availableSeats" label="可用" width="120"></el-table-column>
          <el-table-column prop="maintenanceSeats" label="维护中" width="120"></el-table-column>
          <el-table-column label="使用率" width="200">
            <template v-slot="scope">
              <el-progress 
                :percentage="Math.round(scope.row.occupiedSeats / scope.row.totalSeats * 100)" 
                :status="getOccupancyStatus(scope.row.occupiedSeats, scope.row.totalSeats)">
              </el-progress>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template v-slot="scope">
              <el-tag :type="scope.row.status === 'open' ? 'success' : 'danger'">
                {{ scope.row.status === 'open' ? '开放中' : '已关闭' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'AdminDashboard',
  data() {
    return {
      chartView: 'daily',
      // 最新预约数据
      latestBookings: [
        { username: '张三', studyRoom: '一号自习室（静音区）', seatNumber: 'A12', timeSlot: '09:00-12:00', status: '已签到' },
        { username: '李四', studyRoom: '二号自习室（讨论区）', seatNumber: 'D05', timeSlot: '13:00-17:00', status: '已预约' },
        { username: '王五', studyRoom: '三号自习室（电源区）', seatNumber: 'G08', timeSlot: '18:00-22:00', status: '已预约' },
        { username: '赵六', studyRoom: '一号自习室（静音区）', seatNumber: 'B15', timeSlot: '08:00-12:00', status: '已取消' },
        { username: '钱七', studyRoom: '四号自习室（综合区）', seatNumber: 'I10', timeSlot: '14:00-18:00', status: '已预约' }
      ],
      // 系统日志
      systemLogs: [
        { type: 'primary', timestamp: '今天 10:32', content: '管理员添加了新的自习室：四号自习室（综合区）' },
        { type: 'success', timestamp: '今天 09:15', content: '系统成功处理了120个预约请求' },
        { type: 'warning', timestamp: '今天 08:45', content: '系统检测到座位A12可能存在故障，已标记为维护状态' },
        { type: 'danger', timestamp: '昨天 22:10', content: '系统检测到异常登录尝试，IP: 192.168.1.34' },
        { type: 'info', timestamp: '昨天 16:30', content: '系统自动备份完成' }
      ],
      // 自习室状态
      roomsStatus: [
        { roomName: '一号自习室（静音区）', totalSeats: 120, occupiedSeats: 87, availableSeats: 31, maintenanceSeats: 2, status: 'open' },
        { roomName: '二号自习室（讨论区）', totalSeats: 80, occupiedSeats: 35, availableSeats: 42, maintenanceSeats: 3, status: 'open' },
        { roomName: '三号自习室（电源区）', totalSeats: 60, occupiedSeats: 45, availableSeats: 12, maintenanceSeats: 3, status: 'open' },
        { roomName: '四号自习室（综合区）', totalSeats: 150, occupiedSeats: 132, availableSeats: 15, maintenanceSeats: 3, status: 'open' },
        { roomName: '五号自习室（临时关闭）', totalSeats: 90, occupiedSeats: 0, availableSeats: 0, maintenanceSeats: 90, status: 'closed' }
      ]
    };
  },
  mounted() {
    this.initRoomUsageChart();
    this.initTimeDistChart();
  },
  methods: {
    // 获取占用率状态
    getOccupancyStatus(occupied, total) {
      const percentage = occupied / total * 100;
      if (percentage >= 90) {
        return 'exception';
      } else if (percentage >= 70) {
        return 'warning';
      } else {
        return 'success';
      }
    },
    
    // 获取预约状态类型
    getStatusType(status) {
      const statusMap = {
        '已签到': 'success',
        '已预约': 'primary',
        '已取消': 'info',
        '已过期': 'warning',
        '已违约': 'danger'
      };
      return statusMap[status] || 'info';
    },
    
    // 获取日志颜色
    getLogColor(type) {
      const colorMap = {
        'primary': '#409EFF',
        'success': '#67C23A',
        'warning': '#E6A23C',
        'danger': '#F56C6C',
        'info': '#909399'
      };
      return colorMap[type] || '#909399';
    },
    
    // 刷新自习室状态
    refreshRoomStatus() {
      this.$message.success('自习室状态已更新');
    },
    
    // 初始化自习室使用统计图表
    initRoomUsageChart() {
      // 这里应该使用真实的图表库，如 echarts 或 chart.js
      // 以下是简单的模拟，实际应用中需要引入图表库并正确配置
      console.log('自习室使用统计图表已初始化');
    },
    
    // 初始化预约时段分布图表
    initTimeDistChart() {
      // 同上，需要引入实际图表库
      console.log('预约时段分布图表已初始化');
    }
  },
  watch: {
    // 监听图表视图变化
    chartView(newValue) {
      console.log('图表视图已切换到：', newValue);
      this.initRoomUsageChart(); // 重新初始化图表
    }
  }
};
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.data-card {
  height: 160px;
  display: flex;
  flex-direction: column;
}

.data-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.data-number {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.data-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: #409EFF;
  display: flex;
  align-items: center;
  justify-content: center;
}

.data-icon i {
  font-size: 30px;
  color: white;
}

.data-footer {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.data-trend {
  display: inline-flex;
  align-items: center;
}

.data-trend.up {
  color: #67C23A;
}

.data-trend.down {
  color: #F56C6C;
}

.chart-container, .table-container, .timeline-container, .room-status-container {
  width: 100%;
  overflow: hidden;
}

.timeline-container {
  max-height: 350px;
  overflow-y: auto;
}

.el-timeline-item {
  padding-bottom: 15px;
}
</style> 