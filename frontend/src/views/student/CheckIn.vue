<template>
  <div class="checkin-container">
    <el-row :gutter="20">
      <!-- 签到区域 -->
      <el-col :xs="24" :md="12">
        <el-card class="checkin-card">
          <template #header>
            <div class="card-header">
              <h3>扫码签到</h3>
            </div>
          </template>
          
          <!-- 相机区域 -->
          <div class="camera-container">
            <div class="camera-box">
              <div class="camera-placeholder">
                <i class="el-icon-camera"></i>
                <p>摄像头未启动</p>
                <el-button type="primary" @click="startCamera">开启摄像头</el-button>
              </div>
              
              <!-- 真实相机将替换此处 -->
              <div v-if="cameraActive" class="camera-active">
                <img src="https://dummyimage.com/400x300/000/fff" alt="相机预览" />
                <div class="scan-overlay">
                  <div class="scan-line"></div>
                </div>
              </div>
            </div>
            
            <div class="scan-tips">
              <p>请将座位上的二维码对准摄像头</p>
              <p>系统将自动识别并完成签到</p>
            </div>
          </div>
          
          <!-- 手动签到 -->
          <div class="manual-checkin">
            <div class="divider">
              <span>或者</span>
            </div>
            
            <el-form :model="manualForm" :rules="manualRules" ref="manualFormRef" label-width="0px">
              <el-form-item prop="code">
                <el-input
                  v-model="manualForm.code"
                  placeholder="输入预约码进行签到"
                  prefix-icon="el-icon-s-check">
                  <template #append>
                    <el-button type="primary" @click="handleManualCheckIn">签到</el-button>
                  </template>
                </el-input>
              </el-form-item>
            </el-form>
          </div>
          
          <!-- 签到结果 -->
          <el-dialog
            title="签到结果"
            v-model="checkInResult.visible"
            width="400px"
            center>
            <div class="result-content" :class="checkInResult.success ? 'success' : 'error'">
              <i :class="checkInResult.success ? 'el-icon-success' : 'el-icon-error'" class="result-icon"></i>
              <h3>{{ checkInResult.success ? '签到成功' : '签到失败' }}</h3>
              <p>{{ checkInResult.message }}</p>
            </div>
            <template #footer>
              <span class="dialog-footer">
                <el-button @click="checkInResult.visible = false">关闭</el-button>
                <el-button v-if="checkInResult.success" type="primary" @click="checkInResult.visible = false">确定</el-button>
              </span>
            </template>
          </el-dialog>
        </el-card>
      </el-col>
      
      <!-- 签退区域 -->
      <el-col :xs="24" :md="12">
        <el-card class="checkout-card">
          <template #header>
            <div class="card-header">
              <h3>当前使用中座位</h3>
            </div>
          </template>
          
          <div v-if="activeReservations.length === 0" class="empty-reservations">
            <i class="el-icon-info"></i>
            <p>您当前没有使用中的座位</p>
            <el-button type="primary" @click="$router.push('/student/seat-map')">前往预约</el-button>
          </div>
          
          <div v-else class="active-reservations">
            <el-card 
              v-for="reservation in activeReservations" 
              :key="reservation.id" 
              shadow="hover" 
              class="reservation-item">
              <div class="reservation-info">
                <div class="info-row">
                  <span class="label">自习室:</span>
                  <span class="value">{{ reservation.room }}</span>
                </div>
                
                <div class="info-row">
                  <span class="label">座位号:</span>
                  <span class="value">{{ reservation.seat }}</span>
                </div>
                
                <div class="info-row">
                  <span class="label">时间段:</span>
                  <span class="value">{{ reservation.date }} {{ reservation.time }}</span>
                </div>
                
                <div class="remaining-time">
                  <span class="label">剩余时间:</span>
                  <span class="value">{{ reservation.remainingTime }}</span>
                </div>
                
                <div class="checkout-action">
                  <el-button type="danger" @click="handleCheckOut(reservation)" :loading="reservation.loading">
                    签退座位
                  </el-button>
                  <el-button @click="handleExtendTime(reservation)" :disabled="reservation.canExtend === false">
                    延长时间
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>
          
          <!-- 延长时间对话框 -->
          <el-dialog
            title="延长使用时间"
            v-model="extendTimeDialog.visible"
            width="400px"
            center>
            <div v-if="extendTimeDialog.reservation">
              <div class="extend-info">
                <p>自习室: {{ extendTimeDialog.reservation.room }}</p>
                <p>座位号: {{ extendTimeDialog.reservation.seat }}</p>
                <p>当前结束时间: {{ extendTimeDialog.reservation.endTime }}</p>
              </div>
              
              <div class="extend-form">
                <el-form :model="extendTimeDialog.form" label-width="100px">
                  <el-form-item label="延长时间">
                    <el-select v-model="extendTimeDialog.form.duration" placeholder="请选择延长时间">
                      <el-option label="30分钟" value="30"></el-option>
                      <el-option label="1小时" value="60"></el-option>
                      <el-option label="2小时" value="120"></el-option>
                    </el-select>
                  </el-form-item>
                </el-form>
              </div>
            </div>
            <template #footer>
              <span class="dialog-footer">
                <el-button @click="extendTimeDialog.visible = false">取消</el-button>
                <el-button type="primary" @click="confirmExtendTime" :loading="extendTimeDialog.loading">
                  确定延长
                </el-button>
              </span>
            </template>
          </el-dialog>
          
          <!-- 签退确认对话框 -->
          <el-dialog
            title="签退确认"
            v-model="checkOutDialog.visible"
            :close-on-click-modal="false"
            :close-on-press-escape="false"
            width="400px"
            center>
            <div v-if="checkOutDialog.reservation" class="checkout-confirm">
              <p>确定要签退以下座位吗？</p>
              <div class="checkout-info">
                <p>自习室: {{ checkOutDialog.reservation.room }}</p>
                <p>座位号: {{ checkOutDialog.reservation.seat }}</p>
                <p>时间段: {{ checkOutDialog.reservation.date }} {{ checkOutDialog.reservation.time }}</p>
              </div>
              <div class="checkout-warning">
                <i class="el-icon-warning"></i>
                <span>签退后座位将释放，如需继续使用请重新预约</span>
              </div>
            </div>
            <template #footer>
              <span class="dialog-footer">
                <el-button @click="checkOutDialog.visible = false">取消</el-button>
                <el-button type="danger" @click="confirmCheckOut" :loading="checkOutDialog.loading">
                  确认签退
                </el-button>
              </span>
            </template>
          </el-dialog>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'CheckIn',
  data() {
    return {
      // 摄像头状态
      cameraActive: false,
      
      // 手动签到表单
      manualForm: {
        code: ''
      },
      manualRules: {
        code: [
          { required: true, message: '请输入预约码', trigger: 'blur' },
          { min: 6, max: 20, message: '预约码长度为6-20个字符', trigger: 'blur' }
        ]
      },
      
      // 签到结果对话框
      checkInResult: {
        visible: false,
        success: false,
        message: ''
      },
      
      // 使用中的预约
      activeReservations: [],
      loading: false,
      
      // 延长时间对话框
      extendTimeDialog: {
        visible: false,
        reservation: null,
        form: {
          duration: '60'
        },
        loading: false
      },
      
      // 签退确认对话框
      checkOutDialog: {
        visible: false,
        reservation: null,
        loading: false
      }
    };
  },
  created() {
    this.fetchActiveReservations();
  },
  methods: {
    // 获取当前活跃预约
    async fetchActiveReservations() {
      this.loading = true;
      try {
        const response = await axios.get('/api/seats/reservations/current');
        console.log('获取到的当前预约数据:', response.data);
        
        // 检查预约状态
        if (response.data && response.data.length > 0) {
          const activeReservations = response.data.filter(r => r.status === 'active');
          console.log('筛选出的使用中预约数量:', activeReservations.length);
          console.log('使用中预约:', activeReservations);
        } else {
          console.log('没有找到当前预约');
        }
        
        // 将API返回的数据转换为组件所需格式
        this.activeReservations = response.data.map(reservation => {
          const startTime = new Date(reservation.start_time);
          const endTime = new Date(reservation.end_time);
          
          // 格式化日期和时间
          const date = startTime.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '-');
          const timeStr = `${startTime.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}-${endTime.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`;
          const endTimeStr = endTime.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
          
          // 计算剩余时间
          const now = new Date();
          const diffMs = endTime - now;
          const diffHrs = Math.floor(diffMs / 3600000);
          const diffMins = Math.round((diffMs % 3600000) / 60000);
          const remainingTime = diffMs > 0 ? `${diffHrs}小时${diffMins}分钟` : '已结束';
          
          // 获取座位和自习室信息
          let roomName = '未知自习室';
          let seatNumber = '未知座位';
          
          if (reservation.seat && reservation.seat.seat_number) {
            seatNumber = reservation.seat.seat_number;
            
            if (reservation.seat.room) {
              roomName = reservation.seat.room.name || '未知自习室';
            }
          }
          
          return {
            id: reservation.id,
            room: roomName,
            seat: seatNumber,
            date: date,
            time: timeStr,
            endTime: endTimeStr,
            remainingTime: remainingTime,
            canExtend: diffMs > 0, // 如果时间未结束，则可以延长
            loading: false,
            originalData: reservation // 保存原始数据以备后用
          };
        });
      } catch (error) {
        console.error('获取当前预约失败:', error);
        this.$message.error('获取当前预约失败，请刷新页面重试');
      } finally {
        this.loading = false;
      }
    },
    
    // 开启摄像头
    startCamera() {
      // 实际项目中应该使用WebRTC等技术访问摄像头
      // 这里仅做模拟
      this.cameraActive = true;
      
      // 模拟5秒后扫描到二维码
      setTimeout(() => {
        this.handleScanSuccess('mock-qr-code-123456');
      }, 5000);
    },
    
    // 扫描成功处理
    handleScanSuccess(code) {
      // 模拟API请求验证二维码
      setTimeout(() => {
        // 模拟70%概率签到成功
        const success = Math.random() > 0.3;
        
        this.checkInResult = {
          visible: true,
          success,
          message: success 
            ? '已成功签到一号自习室 A12 座位'
            : '签到失败，二维码无效或已过期'
        };
        
        // 如果成功，更新UI状态
        if (success) {
          // 签到成功后刷新数据
          this.fetchActiveReservations();
          console.log('签到成功，预约码：', code);
        }
        
        // 停止摄像头
        this.cameraActive = false;
      }, 1000);
    },
    
    // 手动签到
    handleManualCheckIn() {
      this.$refs.manualFormRef.validate(async valid => {
        if (!valid) return;
        
        try {
          // 发送签到请求
          const response = await axios.post('/api/seats/check-in', {
            check_in_code: this.manualForm.code
          });
          
          this.checkInResult = {
            visible: true,
            success: true,
            message: `已成功签到 ${response.data.room_name || '未知自习室'} ${response.data.seat_number || '未知座位'}`
          };
          
          // 刷新预约列表
          this.fetchActiveReservations();
        } catch (error) {
          console.error('签到失败:', error);
          this.checkInResult = {
            visible: true,
            success: false,
            message: error.response?.data?.error || '签到失败，预约码无效或已过期'
          };
        }
        
        // 清空表单
        this.manualForm.code = '';
      });
    },
    
    // 签退座位
    handleCheckOut(reservation) {
      console.log('签退座位按钮点击，预约信息:', reservation);
      this.checkOutDialog = {
        visible: true,
        reservation,
        loading: false
      };
      console.log('签退对话框状态:', this.checkOutDialog);
    },
    
    // 确认签退
    async confirmCheckOut() {
      console.log('确认签退按钮点击');
      if (!this.checkOutDialog.reservation) {
        console.error('无法签退：没有选择预约');
        return;
      }
      
      this.checkOutDialog.loading = true;
      
      try {
        console.log(`正在发送签退请求，预约ID: ${this.checkOutDialog.reservation.id}`);
        // 发送签退请求
        const response = await axios.post(
          `/api/seats/reservations/${this.checkOutDialog.reservation.id}/check-out`, 
          {},
          { headers: { 'Content-Type': 'application/json' } }
        );
        
        console.log('签退成功，响应:', response.data);
        
        // 从列表中移除
        this.activeReservations = this.activeReservations.filter(
          item => item.id !== this.checkOutDialog.reservation.id
        );
        
        this.$message.success('座位签退成功');
        // 刷新预约列表
        await this.fetchActiveReservations();
      } catch (error) {
        console.error('签退失败:', error);
        console.error('错误详情:', error.response?.data || error.message);
        this.$message.error(error.response?.data?.error || '签退失败，请稍后重试');
      } finally {
        this.checkOutDialog.visible = false;
        this.checkOutDialog.loading = false;
      }
    },
    
    // 延长时间
    handleExtendTime(reservation) {
      this.extendTimeDialog = {
        visible: true,
        reservation,
        form: {
          duration: '60'
        },
        loading: false
      };
    },
    
    // 确认延长时间
    async confirmExtendTime() {
      if (!this.extendTimeDialog.reservation) return;
      
      this.extendTimeDialog.loading = true;
      
      try {
        // 发送延长时间请求
        await axios.post(`/api/seats/reservations/${this.extendTimeDialog.reservation.id}/extend`, {
          duration: parseInt(this.extendTimeDialog.form.duration)
        });
        
        // 刷新预约列表
        await this.fetchActiveReservations();
        
        this.$message.success('座位使用时间已延长');
      } catch (error) {
        console.error('延长时间失败:', error);
        this.$message.error(error.response?.data?.error || '延长时间失败，请稍后重试');
      } finally {
        this.extendTimeDialog.visible = false;
        this.extendTimeDialog.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.checkin-container {
  padding-bottom: 20px;
}

.checkin-card, .checkout-card {
  margin-bottom: 20px;
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.camera-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.camera-box {
  width: 100%;
  max-width: 400px;
  height: 300px;
  background-color: #f5f7fa;
  margin-bottom: 15px;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.camera-placeholder {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.camera-placeholder i {
  font-size: 48px;
  color: #909399;
  margin-bottom: 10px;
}

.camera-active {
  height: 100%;
  position: relative;
}

.camera-active img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 2px solid #409EFF;
  box-sizing: border-box;
}

.scan-line {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 2px;
  background-color: #409EFF;
  box-shadow: 0 0 5px #409EFF;
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% {
    top: 0;
  }
  50% {
    top: 100%;
  }
  100% {
    top: 0;
  }
}

.scan-tips {
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.scan-tips p {
  margin: 5px 0;
}

.manual-checkin {
  margin-top: 20px;
}

.divider {
  display: flex;
  align-items: center;
  margin: 15px 0;
  color: #909399;
}

.divider:before,
.divider:after {
  content: '';
  flex: 1;
  border-top: 1px solid #dcdfe6;
}

.divider span {
  padding: 0 10px;
}

.result-content {
  text-align: center;
  padding: 20px 0;
}

.result-content.success .result-icon {
  color: #67C23A;
}

.result-content.error .result-icon {
  color: #F56C6C;
}

.result-icon {
  font-size: 60px;
  margin-bottom: 15px;
}

.empty-reservations {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: #909399;
}

.empty-reservations i {
  font-size: 48px;
  margin-bottom: 10px;
}

.reservation-item {
  margin-bottom: 15px;
}

.reservation-info {
  padding: 10px 0;
}

.info-row {
  display: flex;
  margin-bottom: 10px;
}

.label {
  width: 80px;
  color: #606266;
}

.value {
  flex: 1;
  font-weight: bold;
}

.remaining-time {
  display: flex;
  margin: 15px 0;
}

.remaining-time .value {
  color: #E6A23C;
}

.checkout-action {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
}

.checkout-warning {
  margin-top: 15px;
  color: #F56C6C;
  display: flex;
  align-items: center;
}

.checkout-warning i {
  margin-right: 5px;
}

.checkout-info {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin: 10px 0;
}

.extend-info {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.extend-form {
  margin-top: 20px;
}
</style> 