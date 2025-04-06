<template>
  <div class="reports-container">
    <!-- 时间范围选择 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <div class="date-picker">
          <span class="label">统计时间：</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :picker-options="pickerOptions"
            @change="handleDateChange">
          </el-date-picker>
        </div>
        
        <div class="preset-dates">
          <el-button size="small" @click="setDateRange('today')">今日</el-button>
          <el-button size="small" @click="setDateRange('yesterday')">昨日</el-button>
          <el-button size="small" @click="setDateRange('week')">本周</el-button>
          <el-button size="small" @click="setDateRange('month')">本月</el-button>
          <el-button size="small" @click="setDateRange('quarter')">本季度</el-button>
        </div>
        
        <div class="export-btn">
          <el-button type="primary" icon="el-icon-download" @click="exportReport">导出报表</el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 数据概览 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="6">
        <el-card shadow="hover" class="data-card">
          <div class="data-card-content">
            <div class="data-value">{{ statisticsData.totalReservations }}</div>
            <div class="data-label">总预约数</div>
          </div>
          <div class="data-trend">
            <span class="trend-text">同比增长</span>
            <span class="trend-value up">+15.2%</span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="data-card">
          <div class="data-card-content">
            <div class="data-value">{{ statisticsData.averageUsage }}%</div>
            <div class="data-label">平均使用率</div>
          </div>
          <div class="data-trend">
            <span class="trend-text">同比增长</span>
            <span class="trend-value up">+5.8%</span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="data-card">
          <div class="data-card-content">
            <div class="data-value">{{ statisticsData.checkInRate }}%</div>
            <div class="data-label">签到率</div>
          </div>
          <div class="data-trend">
            <span class="trend-text">同比增长</span>
            <span class="trend-value up">+2.3%</span>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="data-card">
          <div class="data-card-content">
            <div class="data-value">{{ statisticsData.violationRate }}%</div>
            <div class="data-label">违约率</div>
          </div>
          <div class="data-trend">
            <span class="trend-text">同比下降</span>
            <span class="trend-value down">-3.5%</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表展示 -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="clearfix">
              <span>每日预约量</span>
              <el-radio-group v-model="dailyReservationUnit" size="mini" style="float: right;">
                <el-radio-button label="day">按日</el-radio-button>
                <el-radio-button label="week">按周</el-radio-button>
                <el-radio-button label="month">按月</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div class="chart-container">
            <div ref="dailyReservationChart" style="width: 100%; height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="clearfix">
              <span>自习室使用率对比</span>
            </div>
          </template>
          <div class="chart-container">
            <div ref="roomUsageChart" style="width: 100%; height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="clearfix">
              <span>时段分布</span>
            </div>
          </template>
          <div class="chart-container">
            <div ref="timeDistributionChart" style="width: 100%; height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="clearfix">
              <span>用户类型分布</span>
            </div>
          </template>
          <div class="chart-container">
            <div ref="userTypeChart" style="width: 100%; height: 350px;"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 详细数据表格 -->
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="clearfix">
          <span>数据详情</span>
          <el-tabs v-model="activeTab" style="margin-top: 15px;">
            <el-tab-pane label="自习室统计" name="roomStats"></el-tab-pane>
            <el-tab-pane label="预约数据" name="reservationStats"></el-tab-pane>
            <el-tab-pane label="用户活跃度" name="userStats"></el-tab-pane>
          </el-tabs>
        </div>
      </template>
      
      <!-- 自习室统计 -->
      <div v-if="activeTab === 'roomStats'" class="table-container">
        <el-table :data="roomStatsData" border stripe style="width: 100%">
          <el-table-column prop="roomName" label="自习室名称"></el-table-column>
          <el-table-column prop="totalSeats" label="座位数" width="100"></el-table-column>
          <el-table-column prop="reservationCount" label="预约数" width="100"></el-table-column>
          <el-table-column prop="usageRate" label="使用率" width="120">
            <template v-slot="scope">
              <el-progress 
                :percentage="scope.row.usageRate" 
                :status="getUsageRateStatus(scope.row.usageRate)">
              </el-progress>
            </template>
          </el-table-column>
          <el-table-column prop="checkInRate" label="签到率" width="120">
            <template v-slot="scope">
              <el-progress :percentage="scope.row.checkInRate" color="#67C23A"></el-progress>
            </template>
          </el-table-column>
          <el-table-column prop="violationRate" label="违约率" width="120">
            <template v-slot="scope">
              <el-progress :percentage="scope.row.violationRate" color="#F56C6C"></el-progress>
            </template>
          </el-table-column>
          <el-table-column prop="peakHours" label="高峰时段" width="150"></el-table-column>
        </el-table>
      </div>
      
      <!-- 预约数据 -->
      <div v-if="activeTab === 'reservationStats'" class="table-container">
        <el-table :data="reservationStatsData" border stripe style="width: 100%">
          <el-table-column prop="date" label="日期" width="120"></el-table-column>
          <el-table-column prop="reservationCount" label="预约数" width="100"></el-table-column>
          <el-table-column prop="checkInCount" label="签到数" width="100"></el-table-column>
          <el-table-column prop="cancelCount" label="取消数" width="100"></el-table-column>
          <el-table-column prop="violationCount" label="违约数" width="100"></el-table-column>
          <el-table-column prop="checkInRate" label="签到率" width="120">
            <template v-slot="scope">
              <el-progress :percentage="scope.row.checkInRate" color="#67C23A"></el-progress>
            </template>
          </el-table-column>
          <el-table-column prop="peakTime" label="高峰时段" width="150"></el-table-column>
        </el-table>
      </div>
      
      <!-- 用户活跃度 -->
      <div v-if="activeTab === 'userStats'" class="table-container">
        <el-table :data="userStatsData" border stripe style="width: 100%">
          <el-table-column prop="userType" label="用户类型" width="120">
            <template v-slot="scope">
              <el-tag :type="getUserTypeColor(scope.row.userType)">{{ scope.row.userType }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="userCount" label="用户数" width="100"></el-table-column>
          <el-table-column prop="activeUsers" label="活跃用户" width="120"></el-table-column>
          <el-table-column prop="reservationCount" label="预约总数" width="120"></el-table-column>
          <el-table-column prop="avgReservation" label="人均预约" width="120"></el-table-column>
          <el-table-column prop="activeRate" label="活跃率" width="150">
            <template v-slot="scope">
              <el-progress :percentage="scope.row.activeRate" color="#409EFF"></el-progress>
            </template>
          </el-table-column>
          <el-table-column prop="preferredRoom" label="偏好自习室"></el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'Reports',
  data() {
    return {
      // 日期选择
      dateRange: [new Date(new Date().getTime() - 30 * 24 * 60 * 60 * 1000), new Date()],
      pickerOptions: {
        shortcuts: [
          {
            text: '最近一周',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
              picker.$emit('pick', [start, end]);
            }
          },
          {
            text: '最近一个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 30);
              picker.$emit('pick', [start, end]);
            }
          },
          {
            text: '最近三个月',
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 90);
              picker.$emit('pick', [start, end]);
            }
          }
        ]
      },
      
      // 统计数据
      statisticsData: {
        totalReservations: 3258,
        averageUsage: 72,
        checkInRate: 89,
        violationRate: 4.5
      },
      
      // 图表选项
      dailyReservationUnit: 'day',
      
      // 表格数据
      activeTab: 'roomStats',
      
      // 自习室统计数据
      roomStatsData: [
        {
          roomName: '一号自习室（静音区）',
          totalSeats: 120,
          reservationCount: 856,
          usageRate: 78,
          checkInRate: 92,
          violationRate: 3.5,
          peakHours: '13:00-17:00'
        },
        {
          roomName: '二号自习室（讨论区）',
          totalSeats: 80,
          reservationCount: 623,
          usageRate: 65,
          checkInRate: 85,
          violationRate: 5.2,
          peakHours: '15:00-19:00'
        },
        {
          roomName: '三号自习室（电源区）',
          totalSeats: 60,
          reservationCount: 712,
          usageRate: 83,
          checkInRate: 90,
          violationRate: 4.1,
          peakHours: '14:00-18:00'
        },
        {
          roomName: '四号自习室（综合区）',
          totalSeats: 150,
          reservationCount: 1067,
          usageRate: 86,
          checkInRate: 88,
          violationRate: 4.8,
          peakHours: '10:00-16:00'
        }
      ],
      
      // 预约统计数据
      reservationStatsData: [
        {
          date: '2023-06-10',
          reservationCount: 327,
          checkInCount: 298,
          cancelCount: 18,
          violationCount: 11,
          checkInRate: 91.1,
          peakTime: '14:00-16:00'
        },
        {
          date: '2023-06-09',
          reservationCount: 315,
          checkInCount: 279,
          cancelCount: 21,
          violationCount: 15,
          checkInRate: 88.6,
          peakTime: '15:00-17:00'
        },
        {
          date: '2023-06-08',
          reservationCount: 308,
          checkInCount: 275,
          cancelCount: 23,
          violationCount: 10,
          checkInRate: 89.3,
          peakTime: '13:00-15:00'
        },
        {
          date: '2023-06-07',
          reservationCount: 331,
          checkInCount: 301,
          cancelCount: 17,
          violationCount: 13,
          checkInRate: 91.0,
          peakTime: '14:00-16:00'
        },
        {
          date: '2023-06-06',
          reservationCount: 318,
          checkInCount: 282,
          cancelCount: 20,
          violationCount: 16,
          checkInRate: 88.7,
          peakTime: '15:00-17:00'
        }
      ],
      
      // 用户活跃度数据
      userStatsData: [
        {
          userType: '学生',
          userCount: 980,
          activeUsers: 725,
          reservationCount: 2856,
          avgReservation: 2.9,
          activeRate: 74,
          preferredRoom: '一号自习室（静音区）'
        },
        {
          userType: '教师',
          userCount: 210,
          activeUsers: 135,
          reservationCount: 402,
          avgReservation: 1.9,
          activeRate: 64,
          preferredRoom: '三号自习室（电源区）'
        },
        {
          userType: '研究生',
          userCount: 180,
          activeUsers: 155,
          reservationCount: 580,
          avgReservation: 3.2,
          activeRate: 86,
          preferredRoom: '四号自习室（综合区）'
        }
      ]
    };
  },
  mounted() {
    this.initCharts();
  },
  methods: {
    // 初始化图表
    initCharts() {
      this.$nextTick(() => {
        // 实际应用中应该使用真实的图表库，如echarts
        console.log('初始化图表');
      });
    },
    
    // 日期范围变化
    handleDateChange(dates) {
      console.log('日期范围变化:', dates);
      // 更新统计数据和图表
    },
    
    // 设置预定义的日期范围
    setDateRange(type) {
      const end = new Date();
      const start = new Date();
      
      // 避免在case中直接声明变量
      let day, month, quarterStartMonth;
      
      switch (type) {
        case 'today':
          // 设置为今天的开始和结束
          start.setHours(0, 0, 0, 0);
          end.setHours(23, 59, 59, 999);
          break;
        case 'yesterday':
          // 设置为昨天的开始和结束
          start.setDate(start.getDate() - 1);
          start.setHours(0, 0, 0, 0);
          end.setDate(end.getDate() - 1);
          end.setHours(23, 59, 59, 999);
          break;
        case 'week':
          // 设置为本周的开始和结束
          day = start.getDay() || 7; // 如果是周日，getDay()返回0，我们将其视为7
          start.setDate(start.getDate() - day + 1);
          start.setHours(0, 0, 0, 0);
          end.setHours(23, 59, 59, 999);
          break;
        case 'month':
          // 设置为本月的开始和结束
          start.setDate(1);
          start.setHours(0, 0, 0, 0);
          end.setHours(23, 59, 59, 999);
          break;
        case 'quarter':
          // 设置为本季度的开始和结束
          month = start.getMonth();
          quarterStartMonth = Math.floor(month / 3) * 3;
          start.setMonth(quarterStartMonth, 1);
          start.setHours(0, 0, 0, 0);
          end.setHours(23, 59, 59, 999);
          break;
      }
      
      this.dateRange = [start, end];
      this.handleDateChange(this.dateRange);
    },
    
    // 导出报表
    exportReport() {
      this.$message.info('正在导出报表，请稍候...');
      
      // 模拟导出过程
      setTimeout(() => {
        this.$message.success('报表导出成功');
      }, 1500);
    },
    
    // 获取使用率状态
    getUsageRateStatus(rate) {
      if (rate >= 90) {
        return 'exception';
      } else if (rate >= 70) {
        return 'warning';
      } else {
        return 'success';
      }
    },
    
    // 获取用户类型颜色
    getUserTypeColor(type) {
      const typeMap = {
        '学生': 'primary',
        '教师': 'success',
        '研究生': 'warning'
      };
      return typeMap[type] || 'info';
    }
  },
  watch: {
    // 监听图表单位变化
    dailyReservationUnit(newValue) {
      console.log('图表单位变化:', newValue);
      // 重新渲染图表
      this.initCharts();
    },
    
    // 监听标签页变化
    activeTab(newValue) {
      console.log('标签页变化:', newValue);
    }
  }
};
</script>

<style scoped>
.reports-container {
  padding: 20px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.date-picker {
  display: flex;
  align-items: center;
}

.label {
  margin-right: 10px;
}

.preset-dates {
  display: flex;
  gap: 5px;
}

.data-card {
  height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.data-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.data-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.data-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.data-trend {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.trend-value.up {
  color: #67C23A;
}

.trend-value.down {
  color: #F56C6C;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 350px;
}

.table-container {
  margin-top: 20px;
}
</style> 