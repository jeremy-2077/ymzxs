<template>
  <div class="facility-container">
    <!-- 顶部工具栏 -->
    <el-card class="toolbar-card">
      <div class="toolbar">
        <div class="left-tools">
          <el-select v-model="selectedRoom" placeholder="选择自习室" @change="handleRoomChange">
            <el-option
              v-for="room in studyRooms"
              :key="room.id"
              :label="room.name"
              :value="room.id">
            </el-option>
          </el-select>
          
          <el-select v-model="selectedZone" placeholder="选择区域" @change="handleZoneChange">
            <el-option label="全部区域" value="all"></el-option>
            <el-option
              v-for="zone in currentRoomZones"
              :key="zone.id"
              :label="zone.name"
              :value="zone.id">
            </el-option>
          </el-select>
          
          <el-select v-model="filterStatus" placeholder="座位状态" @change="filterSeats">
            <el-option label="全部状态" value="all"></el-option>
            <el-option label="可用" value="available"></el-option>
            <el-option label="已占用" value="occupied"></el-option>
            <el-option label="维修中" value="maintenance"></el-option>
          </el-select>
        </div>
        
        <div class="right-tools">
          <el-button type="success" icon="el-icon-plus" @click="showAddRoomDialog">添加自习室</el-button>
          <el-button type="primary" icon="el-icon-plus" @click="showAddSeatDialog">添加座位</el-button>
          <el-button type="success" icon="el-icon-upload2" @click="showImportDialog">批量导入</el-button>
          <el-button type="warning" icon="el-icon-download" @click="exportSeats">导出数据</el-button>
          <el-button type="info" icon="el-icon-refresh" @click="refreshSeats">刷新</el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 座位列表 -->
    <el-card class="seat-card">
      <template #header>
        <div class="seat-header">
          <h3>座位列表</h3>
          <div class="seat-count">
            共 <span class="count-num">{{ filteredSeats.length }}</span> 个座位
          </div>
        </div>
      </template>
      
      <el-table 
        :data="filteredSeats" 
        border 
        style="width: 100%"
        v-loading="loading">
        <el-table-column
          prop="number"
          label="座位号"
          width="100">
        </el-table-column>
        
        <el-table-column
          prop="zone"
          label="所属区域"
          width="120">
          <template #default="scope">
            {{ getZoneName(scope.row.zone) }}
          </template>
        </el-table-column>
        
        <el-table-column
          prop="type"
          label="座位类型"
          width="220">
          <template #default="scope">
            <el-tag v-if="scope.row.isWindow" type="success" effect="plain" class="seat-tag">靠窗</el-tag>
            <el-tag v-if="scope.row.hasSocket" type="primary" effect="plain" class="seat-tag">电源插座</el-tag>
            <el-tag v-if="scope.row.isTable" type="warning" effect="plain" class="seat-tag">四人桌</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="status"
          label="状态"
          width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="currentUser"
          label="当前使用者"
          width="120">
        </el-table-column>
        
        <el-table-column
          prop="note"
          label="备注">
        </el-table-column>
        
        <el-table-column
          label="操作"
          width="250">
          <template #default="scope">
            <el-button
              size="mini"
              type="primary"
              icon="el-icon-edit"
              @click="handleEdit(scope.row)">
              编辑
            </el-button>
            
            <el-button
              size="mini"
              :type="scope.row.status === 'maintenance' ? 'success' : 'warning'"
              :icon="scope.row.status === 'maintenance' ? 'el-icon-check' : 'el-icon-s-tools'"
              @click="toggleMaintenance(scope.row)">
              {{ scope.row.status === 'maintenance' ? '恢复可用' : '设为维修' }}
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
          :total="filteredSeats.length">
        </el-pagination>
      </div>
    </el-card>
    
    <!-- 添加/编辑座位对话框 -->
    <el-dialog
      :title="editMode ? '编辑座位' : '添加座位'"
      :model-value="seatDialogVisible"
      @update:model-value="seatDialogVisible = $event"
      width="500px">
      <el-form :model="seatForm" :rules="seatRules" ref="seatFormRef" label-width="100px">
        <el-form-item label="自习室" prop="roomId">
          <el-select v-model="seatForm.roomId" placeholder="选择自习室" :disabled="editMode">
            <el-option
              v-for="room in studyRooms"
              :key="room.id"
              :label="room.name"
              :value="room.id">
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="区域" prop="zone">
          <el-select v-model="seatForm.zone" placeholder="选择区域">
            <el-option
              v-for="zone in getZonesByRoomId(seatForm.roomId)"
              :key="zone.id"
              :label="zone.name"
              :value="zone.id">
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="座位号" prop="number">
          <el-input v-model="seatForm.number" placeholder="例如：A01" :disabled="editMode"></el-input>
        </el-form-item>
        
        <el-form-item label="座位类型">
          <el-checkbox v-model="seatForm.isWindow">靠窗</el-checkbox>
          <el-checkbox v-model="seatForm.hasSocket">电源插座</el-checkbox>
          <el-checkbox v-model="seatForm.isTable">四人桌</el-checkbox>
        </el-form-item>
        
        <el-form-item label="座位状态" prop="status">
          <el-radio-group v-model="seatForm.status">
            <el-radio label="available">可用</el-radio>
            <el-radio label="maintenance">维修中</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="备注" prop="note">
          <el-input v-model="seatForm.note" type="textarea" :rows="3" placeholder="选填"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="seatDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitSeatForm" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 批量导入对话框 -->
    <el-dialog
      title="批量导入座位"
      :model-value="importDialogVisible"
      @update:model-value="importDialogVisible = $event"
      width="500px">
      <div class="import-tips">
        <p>请按照模板格式上传Excel文件，包含以下字段：</p>
        <ul>
          <li>座位号（必填，例如：A01）</li>
          <li>区域（必填，例如：A、B、C）</li>
          <li>类型（可选，多个类型用逗号分隔，例如：窗边,电源）</li>
          <li>状态（可选，默认为"可用"）</li>
          <li>备注（可选）</li>
        </ul>
      </div>
      
      <el-form :model="importForm" ref="importFormRef" label-width="100px">
        <el-form-item label="自习室" prop="roomId">
          <el-select v-model="importForm.roomId" placeholder="选择自习室">
            <el-option
              v-for="room in studyRooms"
              :key="room.id"
              :label="room.name"
              :value="room.id">
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="Excel文件" prop="file">
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
        </el-form-item>
      </el-form>
      
      <div class="download-template">
        <a href="#" @click.prevent="downloadTemplate">下载导入模板</a>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitImport" :loading="importing">开始导入</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 添加自习室对话框 -->
    <el-dialog
      title="添加自习室"
      :model-value="roomDialogVisible" 
      @update:model-value="roomDialogVisible = $event"
      :modal="true"
      :close-on-click-modal="false"
      width="500px">
      <el-form :model="roomForm" :rules="roomRules" ref="roomFormRef" label-width="100px">
        <el-form-item label="自习室名称" prop="name">
          <el-input v-model="roomForm.name" placeholder="请输入自习室名称"></el-input>
        </el-form-item>
        
        <el-form-item label="建筑名称" prop="building">
          <el-input v-model="roomForm.building" placeholder="请输入建筑名称"></el-input>
        </el-form-item>
        
        <el-form-item label="楼层" prop="floor">
          <el-input v-model="roomForm.floor" placeholder="请输入楼层"></el-input>
        </el-form-item>
        
        <el-form-item label="自习室类型" prop="room_type">
          <el-select v-model="roomForm.room_type" placeholder="请选择自习室类型">
            <el-option label="普通自习室" value="general"></el-option>
            <el-option label="讨论室" value="discussion"></el-option>
            <el-option label="小组学习室" value="group"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="座位容量" prop="capacity">
          <el-input v-model="roomForm.capacity" placeholder="请输入座位容量"></el-input>
        </el-form-item>
        
        <el-form-item label="开放时间" prop="openTime">
          <el-time-picker
            v-model="roomForm.openTime"
            :picker-options="{
              format: 'HH:mm',
              step: '30'
            }"
            placeholder="选择开放时间">
          </el-time-picker>
        </el-form-item>
        
        <el-form-item label="关闭时间" prop="closeTime">
          <el-time-picker
            v-model="roomForm.closeTime"
            :picker-options="{
              format: 'HH:mm',
              step: '30'
            }"
            placeholder="选择关闭时间">
          </el-time-picker>
        </el-form-item>
        
        <el-form-item label="区域" prop="zones">
          <el-select v-model="roomForm.zones" placeholder="选择区域" multiple>
            <el-option
              v-for="zone in getZonesByRoomId(roomForm.roomId)"
              :key="zone.id"
              :label="zone.name"
              :value="zone.id">
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input v-model="roomForm.description" type="textarea" :rows="3" placeholder="选填"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="roomDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRoomForm" :loading="submittingRoom">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'FacilityManagement',
  data() {
    return {
      // 自习室数据
      studyRooms: [],
      
      // 筛选条件
      selectedRoom: 1,
      selectedZone: 'all',
      filterStatus: 'all',
      
      // 座位数据
      seats: [],
      filteredSeats: [],
      loading: false,
      
      // 分页
      pagination: {
        currentPage: 1,
        pageSize: 10
      },
      
      // 座位表单
      seatDialogVisible: false,
      editMode: false,
      seatForm: {
        id: null,
        roomId: 1,
        zone: '',
        number: '',
        status: 'available',
        isWindow: false,
        hasSocket: false,
        isTable: false,
        note: ''
      },
      seatRules: {
        roomId: [
          { required: true, message: '请选择自习室', trigger: 'change' }
        ],
        zone: [
          { required: true, message: '请选择区域', trigger: 'change' }
        ],
        number: [
          { required: true, message: '请输入座位号', trigger: 'blur' },
          { pattern: /^[A-Z][0-9]{2,3}$/, message: '座位号格式不正确（例如：A01）', trigger: 'blur' }
        ]
      },
      submitting: false,
      
      // 导入对话框
      importDialogVisible: false,
      importForm: {
        roomId: 1,
        file: null
      },
      importFile: [],
      importing: false,
      
      // 自习室表单
      roomDialogVisible: false,
      roomForm: {
        name: '',
        building: '',
        floor: 1,
        room_type: 'general',
        capacity: 100,
        openTime: new Date(new Date().setHours(8, 0, 0)),
        closeTime: new Date(new Date().setHours(22, 0, 0)),
        openTimeStr: '08:00',
        closeTimeStr: '22:00',
        zones: [
          { name: 'A区' }
        ],
        description: ''
      },
      roomRules: {
        name: [
          { required: true, message: '请输入自习室名称', trigger: 'blur' },
          { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
        ],
        building: [
          { required: true, message: '请输入建筑名称', trigger: 'blur' }
        ],
        floor: [
          { required: true, message: '请输入楼层', trigger: 'blur' }
        ],
        room_type: [
          { required: true, message: '请选择自习室类型', trigger: 'change' }
        ],
        capacity: [
          { required: true, message: '请输入座位容量', trigger: 'blur' },
          { type: 'number', min: 1, message: '容量必须大于0', trigger: 'blur' }
        ]
      },
      submittingRoom: false
    };
  },
  computed: {
    // 当前自习室区域
    currentRoomZones() {
      const room = this.studyRooms.find(r => r.id === this.selectedRoom);
      return room ? room.zones : [];
    }
  },
  methods: {
    // 加载自习室列表
    loadStudyRooms() {
      import('../../utils/api').then(apiModule => {
        const api = apiModule.default;
        this.loading = true;
        
        api.get('/api/facilities/rooms')
          .then(response => {
            if (response.data && Array.isArray(response.data.rooms) && response.data.rooms.length > 0) {
              // 从API获取自习室列表
              this.studyRooms = response.data.rooms.map(room => ({
                id: room.id,
                name: room.name,
                zones: room.zones || [] // 如果后端返回区域信息
              }));
              
              // 设置默认选中的自习室为列表中的第一个
              if (this.studyRooms.length > 0) {
                this.selectedRoom = this.studyRooms[0].id;
              }
              
              // 加载座位数据
              this.loadSeats();
            } else {
              this.$message.warning('请先添加自习室，再进行座位管理');
              this.loading = false;
            }
          })
          .catch(error => {
            console.error('获取自习室数据失败:', error);
            this.$message.error('获取自习室数据失败: ' + (error.response?.data?.error || error.message));
            this.loading = false;
          });
      });
    },
    // 获取区域名称
    getZoneName(zoneId) {
      if (!zoneId) return '未知区域';
      
      // 尝试从区域对象数组中获取
      for (const room of this.studyRooms) {
        if (room.zones && Array.isArray(room.zones)) {
          const zone = room.zones.find(z => z.id === zoneId || z.name === zoneId);
          if (zone) return zone.name || zone.id;
        }
      }
      
      // 如果找不到，使用ID作为名称
      return zoneId;
    },
    
    // 获取指定自习室的区域
    getZonesByRoomId(roomId) {
      if (!roomId) return [];
      
      const room = this.studyRooms.find(r => r.id === roomId);
      if (!room) return [];
      
      return room.zones && Array.isArray(room.zones) ? room.zones : [];
    },
    
    // 获取状态标签
    getStatusLabel(status) {
      const statusMap = {
        'available': '可用',
        'occupied': '已占用',
        'maintenance': '维修中'
      };
      return statusMap[status] || status;
    },
    
    // 获取状态类型（标签颜色）
    getStatusType(status) {
      const typeMap = {
        'available': 'success',
        'occupied': 'danger',
        'maintenance': 'info'
      };
      return typeMap[status] || '';
    },
    
    // 处理自习室切换
    handleRoomChange() {
      this.selectedZone = 'all';
      this.loadSeats();
    },
    
    // 处理区域切换
    handleZoneChange() {
      this.filterSeats();
    },
    
    // 加载座位数据
    loadSeats() {
      this.loading = true;
      
      // 使用真实API调用
      import('../../utils/api').then(apiModule => {
        const api = apiModule.default;
        api.get(`/api/facilities/rooms/${this.selectedRoom}/seats`)
          .then(response => {
            if (response.data && Array.isArray(response.data.seats)) {
              // 转换后端数据格式为前端格式
              this.seats = response.data.seats.map(seat => ({
                id: seat.id,
                roomId: seat.room_id,
                zone: String.fromCharCode(65 + Math.floor(parseInt(seat.seat_number) / 100)),  // 从座位号提取区域
                number: seat.seat_number,
                status: seat.status,
                hasSocket: seat.seat_type === 'socket',
                isWindow: seat.seat_type === 'window',
                isTable: seat.seat_type === 'table',
                currentUser: '',  // 需要额外调用获取当前使用者
                note: seat.maintenance_note || ''
              }));
              
              this.filterSeats();
            } else {
              this.$message.warning('未获取到座位数据');
              this.seats = [];
              this.filteredSeats = [];
            }
            this.loading = false;
          })
          .catch(error => {
            console.error('获取座位数据失败:', error);
            this.$message.error('获取座位数据失败: ' + (error.response?.data?.error || error.message));
            this.seats = [];
            this.filteredSeats = [];
            this.loading = false;
          });
      });
    },
    
    // 筛选座位
    filterSeats() {
      this.filteredSeats = this.seats.filter(seat => {
        // 筛选区域
        if (this.selectedZone !== 'all' && seat.zone !== this.selectedZone) {
          return false;
        }
        
        // 筛选状态
        if (this.filterStatus !== 'all' && seat.status !== this.filterStatus) {
          return false;
        }
        
        return true;
      });
      
      // 重置分页
      this.pagination.currentPage = 1;
    },
    
    // 刷新座位数据
    refreshSeats() {
      this.loadSeats();
    },
    
    // 分页相关方法
    handleSizeChange(val) {
      this.pagination.pageSize = val;
    },
    
    handleCurrentChange(val) {
      this.pagination.currentPage = val;
    },
    
    // 显示添加座位对话框
    showAddSeatDialog() {
      this.editMode = false;
      this.seatForm = {
        id: null,
        roomId: this.selectedRoom,
        zone: this.selectedZone !== 'all' ? this.selectedZone : '',
        number: '',
        status: 'available',
        isWindow: false,
        hasSocket: false,
        isTable: false,
        note: ''
      };
      
      this.seatDialogVisible = true;
      this.$nextTick(() => {
        if (this.$refs.seatFormRef) {
          this.$refs.seatFormRef.clearValidate();
        }
      });
    },
    
    // 编辑座位
    handleEdit(row) {
      this.editMode = true;
      this.seatForm = {
        id: row.id,
        roomId: row.roomId,
        zone: row.zone,
        number: row.number,
        status: row.status,
        isWindow: row.isWindow,
        hasSocket: row.hasSocket,
        isTable: row.isTable,
        note: row.note
      };
      
      this.seatDialogVisible = true;
      this.$nextTick(() => {
        if (this.$refs.seatFormRef) {
          this.$refs.seatFormRef.clearValidate();
        }
      });
    },
    
    // 切换维修状态
    toggleMaintenance(row) {
      const action = row.status === 'maintenance' ? '设为可用' : '设为维修';
      const newStatus = row.status === 'maintenance' ? 'available' : 'maintenance';
      
      this.$confirm(`确定要将座位 ${row.number} ${action}吗？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 使用API更新座位状态
        import('../../utils/api').then(apiModule => {
          const api = apiModule.default;
          
          // 如果设置为维修状态，需要添加维修原因
          let maintenanceReason = '';
          if (newStatus === 'maintenance') {
            maintenanceReason = window.prompt('请输入维修原因：', '');
            if (maintenanceReason === null) return; // 用户取消
          }
          
          api.patch(`/api/facilities/seats/${row.id}/status`, {
            status: newStatus,
            reason: maintenanceReason || '管理员设置'
          })
            .then(response => {
              this.$message.success(`座位 ${row.number} 已${action}`);
              this.loadSeats(); // 重新加载座位数据
            })
            .catch(error => {
              this.$message.error(action + '失败: ' + (error.response?.data?.error || error.message));
            });
        });
      }).catch(() => {});
    },
    
    // 删除座位
    handleDelete(row) {
      this.$confirm(`确定要删除座位 ${row.number} 吗？此操作不可恢复！`, '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }).then(() => {
        // 使用API删除座位
        import('../../utils/api').then(apiModule => {
          const api = apiModule.default;
          
          api.delete(`/api/facilities/seats/${row.id}`)
            .then(response => {
              this.$message.success(`座位 ${row.number} 已删除`);
              this.loadSeats(); // 重新加载座位数据
            })
            .catch(error => {
              this.$message.error('删除座位失败: ' + (error.response?.data?.error || error.message));
            });
        });
      }).catch(() => {});
    },
    
    // 提交座位表单
    submitSeatForm() {
      if (!this.$refs.seatFormRef) {
        this.$message.error('表单引用不存在，请重新打开对话框');
        return;
      }
      
      this.$refs.seatFormRef.validate(valid => {
        if (!valid) return;
        
        this.submitting = true;
        
        // 准备API请求数据
        const apiData = {
          seat_number: this.seatForm.number,
          seat_type: this.getSeatType(),
          x_position: 0, // 这些坐标需要根据实际布局计算
          y_position: 0,
          maintenance_note: this.seatForm.note || ''
        };
        
        // 导入API模块
        import('../../utils/api').then(apiModule => {
          const api = apiModule.default;
          
          if (this.editMode) {
            // 更新座位
            api.put(`/api/facilities/seats/${this.seatForm.id}`, apiData)
              .then(response => {
                this.$message.success(`座位 ${this.seatForm.number} 更新成功`);
                this.seatDialogVisible = false;
                this.loadSeats(); // 重新加载座位数据
              })
              .catch(error => {
                this.$message.error('更新座位失败: ' + (error.response?.data?.error || error.message));
              })
              .finally(() => {
                this.submitting = false;
              });
          } else {
            // 添加座位
            api.post(`/api/facilities/rooms/${this.seatForm.roomId}/seats`, apiData)
              .then(response => {
                this.$message.success(`座位 ${this.seatForm.number} 添加成功`);
                this.seatDialogVisible = false;
                this.loadSeats(); // 重新加载座位数据
              })
              .catch(error => {
                this.$message.error('添加座位失败: ' + (error.response?.data?.error || error.message));
              })
              .finally(() => {
                this.submitting = false;
              });
          }
        });
      });
    },
    
    // 根据表单选项确定座位类型
    getSeatType() {
      if (this.seatForm.isWindow) return 'window';
      if (this.seatForm.hasSocket) return 'socket';
      if (this.seatForm.isTable) return 'table';
      return 'normal';
    },
    
    // 显示导入对话框
    showImportDialog() {
      this.importDialogVisible = true;
      this.importForm = {
        roomId: this.selectedRoom,
        file: null
      };
      this.importFile = [];
    },
    
    // 文件变更处理
    handleFileChange(file) {
      this.importFile = [file];
      this.importForm.file = file.raw;
    },
    
    // 下载模板
    downloadTemplate() {
      this.$message.info('模板下载功能正在开发中');
    },
    
    // 提交导入
    submitImport() {
      if (!this.importForm.roomId) {
        this.$message.warning('请选择自习室');
        return;
      }
      
      if (!this.importForm.file) {
        this.$message.warning('请选择Excel文件');
        return;
      }
      
      this.importing = true;
      
      // 创建FormData对象
      const formData = new FormData();
      formData.append('file', this.importForm.file);
      
      // 使用API导入座位数据
      import('../../utils/api').then(apiModule => {
        const api = apiModule.default;
        
        api.post(`/api/facilities/import-seats`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
          .then(response => {
            this.$message.success('座位数据导入成功');
            this.importDialogVisible = false;
            this.loadSeats(); // 重新加载座位数据
          })
          .catch(error => {
            console.error('导入座位数据失败:', error);
            this.$message.error('导入座位数据失败: ' + (error.response?.data?.error || error.message));
          })
          .finally(() => {
            this.importing = false;
          });
      });
    },
    
    // 导出座位数据
    exportSeats() {
      // 使用API导出座位数据
      import('../../utils/api').then(apiModule => {
        const api = apiModule.default;
        
        // 显示加载中提示
        const loading = this.$loading({
          lock: true,
          text: '正在导出数据...',
          spinner: 'el-icon-loading',
          background: 'rgba(0, 0, 0, 0.7)'
        });
        
        // 设置响应类型为blob以处理文件下载
        api.get(`/api/facilities/export-seats`, {
          params: { room_id: this.selectedRoom },
          responseType: 'blob'
        })
          .then(response => {
            // 创建Blob对象
            const blob = new Blob([response.data], { 
              type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
            });
            
            // 创建下载链接
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            const filename = `seats_export_${new Date().toISOString().slice(0, 10)}.xlsx`;
            link.download = filename;
            link.click();
            
            this.$message.success('座位数据导出成功');
          })
          .catch(error => {
            console.error('导出座位数据失败:', error);
            this.$message.error('导出座位数据失败，请稍后重试');
          })
          .finally(() => {
            loading.close();
          });
      });
    },
    
    // 显示添加自习室对话框
    showAddRoomDialog() {
      // 重置表单
      this.roomForm = {
        name: '',
        building: '',
        floor: 1,
        room_type: 'general',
        capacity: 100,
        openTime: new Date(new Date().setHours(8, 0, 0)),
        closeTime: new Date(new Date().setHours(22, 0, 0)),
        openTimeStr: '08:00',
        closeTimeStr: '22:00',
        zones: [
          { name: 'A区' }
        ],
        description: ''
      };
      
      // 显示对话框
      this.roomDialogVisible = true;
    },
    
    // 提交自习室表单
    submitRoomForm() {
      if (!this.$refs.roomFormRef) {
        this.$message.error('表单引用不存在，请重新打开对话框');
        return;
      }
      
      this.$refs.roomFormRef.validate(valid => {
        if (!valid) return;
        
        this.submittingRoom = true;
        
        // 准备API请求数据
        const apiData = {
          name: this.roomForm.name,
          building: this.roomForm.building,
          floor: this.roomForm.floor,
          room_type: this.roomForm.room_type,
          capacity: this.roomForm.capacity,
          open_time: this.roomForm.openTime.toISOString().slice(0, 10),
          close_time: this.roomForm.closeTime.toISOString().slice(0, 10),
          zones: this.roomForm.zones.map(zone => ({ name: zone.name })),
          description: this.roomForm.description
        };
        
        // 使用API创建自习室
        import('../../utils/api').then(apiModule => {
          const api = apiModule.default;
          
          api.post('/api/facilities/rooms', apiData)
            .then(response => {
              this.$message.success(`自习室 ${this.roomForm.name} 创建成功`);
              this.roomDialogVisible = false;
              this.loadStudyRooms(); // 重新加载自习室列表
            })
            .catch(error => {
              this.$message.error('创建自习室失败: ' + (error.response?.data?.error || error.message));
              console.error('创建自习室失败：', error);
            })
            .finally(() => {
              this.submittingRoom = false;
            });
        });
      });
    }
  },
  mounted() {
    console.log('FacilityManagement组件已挂载');
    // 确保对话框初始状态为关闭
    this.roomDialogVisible = false;
    
    // 先加载自习室列表，再加载座位数据
    this.loadStudyRooms();
  }
};
</script>

<style scoped>
.facility-container {
  padding-bottom: 20px;
}

.toolbar-card {
  margin-bottom: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-tools {
  display: flex;
  gap: 15px;
}

.right-tools {
  display: flex;
  gap: 10px;
}

.seat-card {
  margin-bottom: 20px;
}

.seat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.count-num {
  font-weight: bold;
  color: #409EFF;
}

.seat-tag {
  margin-right: 5px;
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

.zone-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.zone-input {
  margin-right: 10px;
}
</style> 