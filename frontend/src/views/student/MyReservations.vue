<template>
  <div class="reservations-container">
    <el-card class="reservation-card">
      <template #header>
        <div class="card-header">
          <h2>我的预约</h2>
          <el-button type="primary" size="small" @click="refreshReservations">刷新</el-button>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="当前预约" name="current">
          <el-table 
            :data="currentReservations" 
            style="width: 100%" 
            v-loading="loading"
            empty-text="暂无当前预约记录">
            <el-table-column label="自习室" prop="studyRoomName"></el-table-column>
            <el-table-column label="座位编号" prop="seatNumber"></el-table-column>
            <el-table-column label="预约日期">
              <template #default="scope">
                {{ formatDate(scope.row.date) }}
              </template>
            </el-table-column>
            <el-table-column label="开始时间">
              <template #default="scope">
                {{ formatTime(scope.row.startTime) }}
              </template>
            </el-table-column>
            <el-table-column label="结束时间">
              <template #default="scope">
                {{ formatTime(scope.row.endTime) }}
              </template>
            </el-table-column>
            <el-table-column label="状态">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button 
                  v-if="scope.row.status === 'reserved'" 
                  type="success" 
                  size="small" 
                  @click="handleCheckIn(scope.row)">
                  签到
                </el-button>
                <el-button 
                  v-if="scope.row.status === 'checked_in'" 
                  type="warning" 
                  size="small" 
                  @click="handleCheckOut(scope.row)">
                  签退
                </el-button>
                <el-button 
                  v-if="scope.row.status === 'reserved'" 
                  type="danger" 
                  size="small" 
                  @click="handleCancel(scope.row)">
                  取消
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="历史记录" name="history">
          <el-table 
            :data="historyReservations" 
            style="width: 100%" 
            v-loading="loading"
            empty-text="暂无历史预约记录">
            <el-table-column label="自习室" prop="studyRoomName"></el-table-column>
            <el-table-column label="座位编号" prop="seatNumber"></el-table-column>
            <el-table-column label="预约日期">
              <template #default="scope">
                {{ formatDate(scope.row.date) }}
              </template>
            </el-table-column>
            <el-table-column label="开始时间">
              <template #default="scope">
                {{ formatTime(scope.row.startTime) }}
              </template>
            </el-table-column>
            <el-table-column label="结束时间">
              <template #default="scope">
                {{ formatTime(scope.row.endTime) }}
              </template>
            </el-table-column>
            <el-table-column label="实际签到时间">
              <template #default="scope">
                {{ scope.row.checkInTime ? formatDateTime(scope.row.checkInTime) : '未签到' }}
              </template>
            </el-table-column>
            <el-table-column label="实际签退时间">
              <template #default="scope">
                {{ scope.row.checkOutTime ? formatDateTime(scope.row.checkOutTime) : '未签退' }}
              </template>
            </el-table-column>
            <el-table-column label="状态">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 签到对话框 -->
    <el-dialog
      title="扫码签到"
      v-model="checkInDialogVisible"
      width="400px"
      center>
      <div class="qrcode-container" v-if="selectedReservation">
        <p>请扫描自习室内的二维码进行签到</p>
        <div class="manual-checkin">
          <el-input 
            v-model="checkInCode" 
            placeholder="或手动输入签到码"
            style="margin-bottom: 15px;">
          </el-input>
          <el-button type="primary" @click="submitCheckIn">确认签到</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'MyReservations',
  data() {
    return {
      activeTab: 'current',
      loading: false,
      currentReservations: [],
      historyReservations: [],
      currentPage: 1,
      pageSize: 10,
      total: 0,
      selectedReservation: null,
      checkInDialogVisible: false,
      checkInCode: ''
    }
  },
  created() {
    this.fetchReservations()
  },
  methods: {
    fetchReservations() {
      this.loading = true
      const token = localStorage.getItem('token')
      
      console.log('开始获取当前预约...')
      
      // 获取当前预约 (状态为 pending 或 active)
      axios.get('/api/seats/reservations', {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        params: {
          status: 'pending,active'
        }
      })
        .then(response => {
          console.log('获取当前预约成功, 完整响应:', JSON.stringify(response.data))
          if (response.data.reservations && response.data.reservations.length > 0) {
            console.log(`找到 ${response.data.reservations.length} 条预约记录`)
            this.currentReservations = response.data.reservations.map((r, index) => {
              console.log(`处理预约数据 ${index+1}/${response.data.reservations.length}:`, r)
              // 检查seat嵌套对象
              console.log(`座位信息: ${r.seat ? JSON.stringify(r.seat) : '无'}`)
              if (r.seat && r.seat.room) {
                console.log(`自习室信息: ${JSON.stringify(r.seat.room)}`)
              }
              
              return {
                id: r.id,
                studyRoomName: r.seat?.room?.name || '未知',
                seatNumber: r.seat?.seat_number || '未知',
                date: this.formatDate(r.start_time),
                startTime: r.start_time,
                endTime: r.end_time,
                status: r.status
              }
            })
            console.log('处理后的当前预约:', this.currentReservations)
          } else {
            console.log('没有当前预约记录')
            this.currentReservations = []
          }
        })
        .catch(error => {
          console.error('获取当前预约失败', error)
          console.error('错误详情:', error.response ? error.response.data : 'No response data')
          this.$message.error('获取当前预约失败')
        })
        .finally(() => {
          if (this.activeTab === 'current') {
            this.loading = false
          }
        })
      
      // 获取历史预约
      if (this.activeTab === 'history') {
        this.fetchHistoryReservations()
      }
    },
    
    fetchHistoryReservations() {
      this.loading = true
      const token = localStorage.getItem('token')
      
      axios.get('/api/seats/reservations/history', {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        params: {
          page: this.currentPage,
          per_page: this.pageSize
        }
      })
        .then(response => {
          this.historyReservations = response.data.items.map(r => ({
             id: r.id,
            studyRoomName: r.seat?.room?.name || '未知',
            seatNumber: r.seat?.seat_number || '未知',
            startTime: r.start_time,
            endTime: r.end_time,
            checkInTime: r.checkin_time,
            checkOutTime: r.checkout_time,
            status: r.status
          }))
          this.total = response.data.total
        })
        .catch(error => {
          console.error('获取历史预约失败', error)
          this.$message.error('获取历史预约失败')
        })
         .finally(() => {
            this.loading = false
        })
    },
    
    refreshReservations() {
      this.fetchReservations()
    },
    
    handleSizeChange(size) {
      this.pageSize = size
      this.fetchHistoryReservations()
    },
    
    handleCurrentChange(page) {
      this.currentPage = page
      this.fetchHistoryReservations()
    },
    
    formatDate(isoString) {
      if (!isoString) return ''
      try {
        const d = new Date(isoString)
        if (isNaN(d.getTime())) return '无效日期';
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
      } catch (e) {
        return '日期解析错误';
      }
    },
    
    formatTime(isoString) {
      if (!isoString) return ''
       try {
        const d = new Date(isoString)
        if (isNaN(d.getTime())) return '无效时间';
        return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
      } catch (e) {
        return '时间解析错误';
      }
    },
    
    formatDateTime(isoString) {
       if (!isoString) return ''
       try {
        const d = new Date(isoString)
        if (isNaN(d.getTime())) return '无效时间';
        return `${this.formatDate(isoString)} ${this.formatTime(isoString)}`
      } catch (e) {
        return '日期时间解析错误';
      }
    },
    
    getStatusType(status) {
      switch (status) {
        case 'pending': return 'primary'
        case 'active': return 'success'
        case 'completed': return 'info'
        case 'cancelled': return 'danger'
        case 'expired': return 'warning'
        default: return 'info'
      }
    },
    
    getStatusText(status) {
      switch (status) {
        case 'pending': return '待签到'
        case 'active': return '使用中'
        case 'completed': return '已完成'
        case 'cancelled': return '已取消'
        case 'expired': return '已过期'
        default: return '未知状态'
      }
    },
    
    handleCheckIn(reservation) {
      if (reservation.status !== 'pending') {
        this.$message.warning('只有待签到的预约才能签到');
        return;
      }
      this.selectedReservation = reservation
      this.checkInDialogVisible = true
      this.checkInCode = ''
    },
    
    submitCheckIn() {
      if (!this.checkInCode) {
        this.$message.warning('请输入签到码')
        return
      }
      
      const token = localStorage.getItem('token')
      
      axios.post(`/api/seats/reservations/${this.selectedReservation.id}/check-in`, {
        check_in_code: this.checkInCode
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
        .then(response => {
          this.$message.success('签到成功')
          this.checkInDialogVisible = false
          this.fetchReservations()
        })
        .catch(error => {
          if (error.response && error.response.data && error.response.data.message) {
            this.$message.error(error.response.data.message)
          } else {
            this.$message.error('签到失败，请检查签到码是否正确')
          }
        })
    },
    
    handleCheckOut(reservation) {
      if (reservation.status !== 'active') {
        this.$message.warning('只有使用中的预约才能签退');
        return;
      }
      this.$confirm('确定要签退吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
        .then(() => {
          const token = localStorage.getItem('token')
          
          axios.post(`/api/seats/reservations/${reservation.id}/check-out`, {}, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
            .then(response => {
              this.$message.success('签退成功')
              this.fetchReservations()
            })
            .catch(error => {
              if (error.response && error.response.data && error.response.data.message) {
                this.$message.error(error.response.data.message)
              } else {
                this.$message.error('签退失败')
              }
            })
        })
        .catch(() => {})
    },
    
    handleCancel(reservation) {
      if (reservation.status !== 'pending') {
        this.$message.warning('只有待签到的预约才能取消');
        return;
      }
      this.$confirm('确定要取消该预约吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
        .then(() => {
          const token = localStorage.getItem('token')
          
          axios.post(`/api/seats/reservations/${reservation.id}/cancel`, {}, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
            .then(response => {
              this.$message.success('预约已取消')
              this.fetchReservations()
            })
            .catch(error => {
              if (error.response && error.response.data && error.response.data.message) {
                this.$message.error(error.response.data.message)
              } else {
                this.$message.error('取消预约失败')
              }
            })
        })
        .catch(() => {})
    }
  },
  watch: {
    activeTab(newVal) {
      if (newVal === 'history') {
        this.fetchHistoryReservations()
      }
    }
  }
}
</script>

<style scoped>
.reservations-container {
  padding: 20px;
}

.reservation-card {
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

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.qrcode-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
}

.manual-checkin {
  margin-top: 20px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}
</style> 