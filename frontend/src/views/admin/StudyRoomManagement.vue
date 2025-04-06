<template>
  <div class="study-room-container">
    <!-- 顶部工具栏 -->
    <el-card class="toolbar-card">
      <div class="toolbar">
        <div class="search-box">
          <el-input
            placeholder="搜索自习室名称"
            v-model="searchQuery"
            clearable
            @clear="handleSearch"
            @input="handleSearch">
            <template #append>
              <el-button icon="el-icon-search" @click="handleSearch"></el-button>
            </template>
          </el-input>
        </div>
        
        <div class="right-tools">
          <el-button type="primary" icon="el-icon-plus" @click="showAddRoomDialog">添加自习室</el-button>
          <el-button type="info" icon="el-icon-refresh" @click="refreshRooms">刷新</el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 自习室列表 -->
    <el-card class="room-card">
      <template #header>
        <div class="room-header">
          <h3>自习室列表</h3>
          <div class="room-count">
            共 <span class="count-num">{{ filteredRooms.length }}</span> 个自习室
          </div>
        </div>
      </template>
      
      <el-table
        :data="paginatedRooms"
        border
        style="width: 100%"
        v-loading="loading">
        <el-table-column
          prop="id"
          label="ID"
          width="80">
        </el-table-column>
        
        <el-table-column
          prop="name"
          label="自习室名称"
          min-width="180">
        </el-table-column>
        
        <el-table-column
          prop="location"
          label="位置"
          min-width="180">
        </el-table-column>
        
        <el-table-column
          prop="category"
          label="类型"
          width="120">
          <template #default="scope">
            <el-tag :type="getRoomCategoryType(scope.row.category)">
              {{ getRoomCategoryLabel(scope.row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="capacity"
          label="座位容量"
          width="100">
        </el-table-column>
        
        <el-table-column
          prop="currentOccupancy"
          label="当前使用"
          width="100">
          <template #default="scope">
            <div class="occupancy-info">
              <span>{{ scope.row.currentOccupancy }}/{{ scope.row.capacity }}</span>
              <el-progress 
                :percentage="Math.round(scope.row.currentOccupancy / scope.row.capacity * 100)" 
                :status="getOccupancyStatus(scope.row.currentOccupancy, scope.row.capacity)">
              </el-progress>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column
          prop="openingHours"
          label="开放时间"
          width="200">
        </el-table-column>
        
        <el-table-column
          prop="status"
          label="状态"
          width="100">
          <template #default="scope">
            <el-tag :type="getRoomStatusType(scope.row.status)">
              {{ getRoomStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
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
              :type="scope.row.status === 'closed' ? 'success' : 'warning'"
              :icon="scope.row.status === 'closed' ? 'el-icon-check' : 'el-icon-close'"
              @click="toggleRoomStatus(scope.row)">
              {{ scope.row.status === 'closed' ? '开放使用' : '关闭使用' }}
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
          :page-sizes="[5, 10, 20, 50]"
          :page-size="pagination.pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredRooms.length">
        </el-pagination>
      </div>
    </el-card>
    
    <!-- 添加/编辑自习室对话框 -->
    <el-dialog
      :title="editMode ? '编辑自习室' : '添加自习室'"
      :model-value="roomDialogVisible"
      @update:model-value="roomDialogVisible = $event"
      width="600px">
      <el-form :model="roomForm" :rules="roomRules" ref="roomFormRef" label-width="100px">
        <el-form-item label="自习室名称" prop="name">
          <el-input v-model="roomForm.name" placeholder="例如：图书馆三楼自习室"></el-input>
        </el-form-item>
        
        <el-form-item label="位置" prop="location">
          <el-input v-model="roomForm.location" placeholder="例如：图书馆三楼东侧"></el-input>
        </el-form-item>
        
        <el-form-item label="类型" prop="category">
          <el-select v-model="roomForm.category" placeholder="选择自习室类型">
            <el-option label="静音区" value="quiet"></el-option>
            <el-option label="讨论区" value="discussion"></el-option>
            <el-option label="电源区" value="power"></el-option>
            <el-option label="综合区" value="general"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="座位容量" prop="capacity">
          <el-input-number v-model="roomForm.capacity" :min="1" :max="500"></el-input-number>
        </el-form-item>
        
        <el-form-item label="开放时间" prop="openingHours">
          <el-input v-model="roomForm.openingHours" placeholder="例如：08:00-22:00"></el-input>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="roomForm.status">
            <el-radio label="open">开放使用</el-radio>
            <el-radio label="closed">暂时关闭</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            type="textarea" 
            v-model="roomForm.description" 
            :rows="3" 
            placeholder="自习室描述，环境特点等"></el-input>
        </el-form-item>
        
        <el-divider content-position="left">区域管理</el-divider>
        
        <div class="zone-management">
          <div class="zone-list">
            <el-tag
              v-for="(zone, index) in roomForm.zones"
              :key="index"
              closable
              @close="removeZone(index)"
              class="zone-tag">
              {{ zone.name }}
            </el-tag>
            
            <el-button 
              class="add-zone-btn" 
              size="small" 
              type="primary" 
              icon="el-icon-plus"
              @click="showAddZoneDialog">
              添加区域
            </el-button>
          </div>
        </div>
        
        <el-form-item label="设施" prop="facilities">
          <el-checkbox-group v-model="roomForm.facilities">
            <el-checkbox label="wifi">WiFi</el-checkbox>
            <el-checkbox label="airConditioner">空调</el-checkbox>
            <el-checkbox label="sockets">电源插座</el-checkbox>
            <el-checkbox label="desk">大桌</el-checkbox>
            <el-checkbox label="water">饮水机</el-checkbox>
            <el-checkbox label="restroom">卫生间</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="roomDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRoomForm" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 添加区域对话框 -->
    <el-dialog
      title="添加区域"
      :model-value="zoneDialogVisible"
      @update:model-value="zoneDialogVisible = $event"
      width="500px"
      append-to-body>
      <el-form :model="zoneForm" :rules="zoneRules" ref="zoneFormRef" label-width="100px">
        <el-form-item label="区域名称" prop="name">
          <el-input v-model="zoneForm.name" placeholder="例如：A区（靠窗）"></el-input>
        </el-form-item>
        
        <el-form-item label="区域代码" prop="id">
          <el-input v-model="zoneForm.id" placeholder="例如：A"></el-input>
        </el-form-item>
        
        <el-form-item label="区域特点">
          <el-checkbox-group v-model="zoneForm.features">
            <el-checkbox label="window">靠窗</el-checkbox>
            <el-checkbox label="power">电源插座</el-checkbox>
            <el-checkbox label="quiet">安静区域</el-checkbox>
            <el-checkbox label="large">大桌</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            type="textarea" 
            v-model="zoneForm.description" 
            :rows="2" 
            placeholder="可选"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="zoneDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitZoneForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'StudyRoomManagement',
  data() {
    return {
      // 搜索
      searchQuery: '',
      
      // 自习室数据
      rooms: [],
      filteredRooms: [],
      loading: false,
      
      // 分页
      pagination: {
        currentPage: 1,
        pageSize: 10
      },
      
      // 自习室表单
      roomDialogVisible: false,
      editMode: false,
      roomForm: {
        id: null,
        name: '',
        location: '',
        category: 'general',
        capacity: 100,
        openingHours: '08:00-22:00',
        status: 'open',
        description: '',
        zones: [],
        facilities: ['wifi', 'airConditioner']
      },
      roomRules: {
        name: [
          { required: true, message: '请输入自习室名称', trigger: 'blur' },
          { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
        ],
        location: [
          { required: true, message: '请输入自习室位置', trigger: 'blur' }
        ],
        category: [
          { required: true, message: '请选择自习室类型', trigger: 'change' }
        ],
        capacity: [
          { required: true, message: '请输入座位容量', trigger: 'blur' },
          { type: 'number', min: 1, message: '容量必须大于0', trigger: 'blur' }
        ],
        openingHours: [
          { required: true, message: '请输入开放时间', trigger: 'blur' },
          { pattern: /^\d{2}:\d{2}-\d{2}:\d{2}$/, message: '时间格式不正确（例如：08:00-22:00）', trigger: 'blur' }
        ]
      },
      submitting: false,
      
      // 区域表单
      zoneDialogVisible: false,
      zoneForm: {
        id: '',
        name: '',
        features: [],
        description: ''
      },
      zoneRules: {
        name: [
          { required: true, message: '请输入区域名称', trigger: 'blur' }
        ],
        id: [
          { required: true, message: '请输入区域代码', trigger: 'blur' },
          { pattern: /^[A-Z]$/, message: '区域代码应为一个大写字母', trigger: 'blur' }
        ]
      }
    };
  },
  computed: {
    // 分页后的数据
    paginatedRooms() {
      const start = (this.pagination.currentPage - 1) * this.pagination.pageSize;
      const end = start + this.pagination.pageSize;
      return this.filteredRooms.slice(start, end);
    }
  },
  methods: {
    // 辅助调试函数
    debugApiResponse(error) {
      console.error('API错误详情:', error);
      let errorMessage = '操作失败';
      
      if (error.response) {
        // 服务器返回了错误状态码
        console.error('状态码:', error.response.status);
        console.error('响应头:', error.response.headers);
        
        if (error.response.data) {
          if (typeof error.response.data === 'string' && error.response.data.includes('NameError')) {
            // 如果是服务器的NameError（如未定义的枚举），返回具体信息
            errorMessage = '服务器配置错误: 状态值格式不匹配，请联系管理员';
            console.error('服务器错误，可能是枚举值未定义:', error.response.data);
          } else {
            errorMessage = (error.response.data.error || error.response.data.message || '未知服务器错误');
          }
        }
      } else if (error.request) {
        // 请求已发送但没有收到响应
        errorMessage = '服务器无响应，请稍后重试';
      } else {
        // 请求配置出错
        errorMessage = error.message || '请求错误';
      }
      
      return errorMessage;
    },
    
    // 获取自习室类型标签
    getRoomCategoryLabel(category) {
      const categoryMap = {
        'quiet': '静音区',
        'discussion': '讨论区',
        'power': '电源区',
        'general': '综合区'
      };
      return categoryMap[category] || category;
    },
    
    // 获取自习室类型颜色
    getRoomCategoryType(category) {
      const typeMap = {
        'quiet': 'success',
        'discussion': 'warning',
        'power': 'primary',
        'general': 'info'
      };
      return typeMap[category] || '';
    },
    
    // 获取状态标签
    getRoomStatusLabel(status) {
      const statusMap = {
        'open': '开放中',
        'closed': '已关闭',
        'maintenance': '维护中'
      };
      return statusMap[status] || status;
    },
    
    // 获取状态类型（标签颜色）
    getRoomStatusType(status) {
      const typeMap = {
        'open': 'success',
        'closed': 'danger',
        'maintenance': 'info'
      };
      return typeMap[status] || '';
    },
    
    // 获取占用率状态
    getOccupancyStatus(current, total) {
      const percentage = current / total * 100;
      if (percentage >= 90) {
        return 'exception';
      } else if (percentage >= 70) {
        return 'warning';
      } else {
        return 'success';
      }
    },
    
    // 搜索处理
    handleSearch() {
      this.filterRooms();
    },
    
    // 筛选自习室
    filterRooms() {
      if (!this.searchQuery) {
        this.filteredRooms = [...this.rooms];
      } else {
        const query = this.searchQuery.toLowerCase();
        this.filteredRooms = this.rooms.filter(room => {
          return room.name.toLowerCase().includes(query) ||
                 room.location.toLowerCase().includes(query);
        });
      }
      
      // 重置分页
      this.pagination.currentPage = 1;
    },
    
    // 加载自习室数据
    loadRooms() {
      this.loading = true;
      
      // 使用真实API调用
      import('../../utils/api').then(apiModule => {
        const api = apiModule.default;
        
        api.get('/api/facilities/rooms')
          .then(response => {
            if (response.data && Array.isArray(response.data.rooms)) {
              // 转换后端数据为前端需要的格式
              this.rooms = response.data.rooms.map(room => ({
                id: room.id,
                name: room.name,
                location: `${room.building} ${room.floor}楼`,
                category: room.room_type,
                capacity: room.capacity,
                currentOccupancy: 0, // 需要从座位数据中计算，可能需要额外API调用
                openingHours: `${room.open_time}-${room.close_time}`,
                status: 'open', // 假设都是开放状态，除非后端提供
                description: room.description || '',
                zones: room.zones || [],
                facilities: [] // 后端可能没有这个字段，需要根据实际情况调整
              }));
              
              this.filterRooms();
            } else {
              this.$message.warning('没有找到自习室数据');
              this.rooms = [];
              this.filteredRooms = [];
            }
            this.loading = false;
          })
          .catch(error => {
            console.error('获取自习室数据失败:', error);
            this.$message.error('获取自习室数据失败: ' + this.debugApiResponse(error));
            this.loading = false;
          });
      });
    },
    
    // 刷新自习室数据
    refreshRooms() {
      this.loadRooms();
    },
    
    // 分页相关方法
    handleSizeChange(val) {
      this.pagination.pageSize = val;
    },
    
    handleCurrentChange(val) {
      this.pagination.currentPage = val;
    },
    
    // 显示添加自习室对话框
    showAddRoomDialog() {
      this.editMode = false;
      this.roomForm = {
        id: null,
        name: '',
        location: '',
        category: 'general',
        capacity: 100,
        openingHours: '08:00-22:00',
        status: 'open',
        description: '',
        zones: [],
        facilities: ['wifi', 'airConditioner']
      };
      
      this.roomDialogVisible = true;
      this.$nextTick(() => {
        if (this.$refs.roomFormRef) {
          this.$refs.roomFormRef.clearValidate();
        }
      });
    },
    
    // 编辑自习室
    handleEdit(row) {
      this.editMode = true;
      this.roomForm = JSON.parse(JSON.stringify(row)); // 深复制
      
      this.roomDialogVisible = true;
      this.$nextTick(() => {
        if (this.$refs.roomFormRef) {
          this.$refs.roomFormRef.clearValidate();
        }
      });
    },
    
    // 切换自习室状态
    toggleRoomStatus(row) {
      const action = row.status === 'closed' ? '开放' : '关闭';
      const newStatus = row.status === 'closed' ? 'open' : 'closed';
      
      this.$confirm(`确定要${action}自习室"${row.name}"吗？`, '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 使用API调用切换状态
        import('../../utils/api').then(apiModule => {
          const api = apiModule.default;
          
          api.patch(`/api/facilities/rooms/${row.id}/status`, {
            status: newStatus
          })
            .then(response => {
              this.$message.success(`自习室"${row.name}"已${action}`);
              this.loadRooms(); // 重新加载自习室数据
            })
            .catch(error => {
              this.$message.error(action + '失败: ' + this.debugApiResponse(error));
            });
        });
      }).catch(() => {});
    },
    
    // 删除自习室
    handleDelete(row) {
      this.$confirm(`确定要删除自习室"${row.name}"吗？此操作不可恢复！`, '警告', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'error'
      }).then(() => {
        // 使用API调用删除自习室
        import('../../utils/api').then(apiModule => {
          const api = apiModule.default;
          
          api.delete(`/api/facilities/rooms/${row.id}`)
            .then(response => {
              this.$message.success(`自习室"${row.name}"已删除`);
              this.loadRooms(); // 重新加载自习室数据
            })
            .catch(error => {
              this.$message.error('删除自习室失败: ' + this.debugApiResponse(error));
            });
        });
      }).catch(() => {});
    },
    
    // 提交自习室表单
    submitRoomForm() {
      this.$refs.roomFormRef.validate(valid => {
        if (!valid) return;
        
        this.submitting = true;
        
        // 解析时间字符串（添加安全检查）
        let openTime = '08:00', closeTime = '22:00';
        if (this.roomForm.openingHours && this.roomForm.openingHours.includes('-')) {
          const timeParts = this.roomForm.openingHours.split('-');
          // 去除空格并验证格式
          const openTimeTmp = timeParts[0] ? timeParts[0].trim() : '';
          const closeTimeTmp = timeParts[1] ? timeParts[1].trim() : '';
          
          // 验证时间格式是否为HH:MM
          const timeRegex = /^([01]?[0-9]|2[0-3]):([0-5][0-9])$/;
          if (timeRegex.test(openTimeTmp)) {
            openTime = openTimeTmp;
          } else {
            this.$message.warning('开放时间格式不正确，已使用默认值08:00');
          }
          if (timeRegex.test(closeTimeTmp)) {
            closeTime = closeTimeTmp;
          } else {
            this.$message.warning('关闭时间格式不正确，已使用默认值22:00');
          }
        } else {
          this.$message.warning('时间格式不正确，已使用默认值08:00-22:00');
        }
        
        // 解析位置信息（添加安全检查）
        let building = '', floor = 1;
        if (this.roomForm.location && typeof this.roomForm.location === 'string') {
          const locationParts = this.roomForm.location.split(' ');
          if (locationParts.length >= 1) {
            building = locationParts[0] || '';
          }
          if (locationParts.length >= 2) {
            const floorStr = locationParts[1] || '';
            const floorNum = parseInt(floorStr.replace(/[^0-9]/g, ''));
            floor = isNaN(floorNum) ? 1 : floorNum;
          }
        }
        
        // 准备API请求数据 (恢复status字段)
        const apiData = {
          name: this.roomForm.name,
          floor: floor,
          building: building,
          room_type: this.roomForm.category,
          capacity: Number(this.roomForm.capacity),
          open_time: openTime,
          close_time: closeTime,
          // 恢复status字段，使用字符串
          status: this.roomForm.status ? String(this.roomForm.status) : 'open',
          zones: this.roomForm.zones.map(zone => ({
            name: zone.name,
            id: zone.id || '' 
          })),
          description: this.roomForm.description || ''
        };
        
        console.log('发送到服务器的数据:', JSON.stringify(apiData, null, 2));
        
        // 导入API模块
        import('../../utils/api').then(apiModule => {
          const api = apiModule.default;
          
          let request;
          if (this.editMode) {
            // 更新自习室
            request = api.put(`/api/facilities/rooms/${this.roomForm.id}`, apiData);
          } else {
            // 添加自习室
            request = api.post('/api/facilities/rooms', apiData);
          }
          
          request
            .then(response => {
              const action = this.editMode ? '更新' : '添加';
              this.$message.success(`自习室"${this.roomForm.name}" ${action}成功`);
              this.roomDialogVisible = false;
              this.loadRooms(); // 重新加载自习室数据
            })
            .catch(error => {
              // 简化错误处理，移除重试逻辑
              console.error(`${this.editMode ? '更新' : '添加'}自习室失败，完整错误:`, error);
              console.error('错误响应数据:', error.response?.data);
              this.$message.error(`${this.editMode ? '更新' : '添加'}自习室失败: ${this.debugApiResponse(error)}`);
            })
            .finally(() => {
              this.submitting = false;
            });
        });
      });
    },
    
    // 显示添加区域对话框
    showAddZoneDialog() {
      this.zoneForm = {
        id: '',
        name: '',
        features: [],
        description: ''
      };
      
      this.zoneDialogVisible = true;
      this.$nextTick(() => {
        if (this.$refs.zoneFormRef) {
          this.$refs.zoneFormRef.clearValidate();
        }
      });
    },
    
    // 提交区域表单
    submitZoneForm() {
      this.$refs.zoneFormRef.validate(valid => {
        if (!valid) return;
        
        // 检查区域代码是否重复
        const isDuplicate = this.roomForm.zones.some(zone => zone.id === this.zoneForm.id);
        if (isDuplicate) {
          this.$message.error('区域代码已存在，请使用不同的代码');
          return;
        }
        
        // 添加到区域列表
        this.roomForm.zones.push({ ...this.zoneForm });
        this.$message.success('区域添加成功');
        this.zoneDialogVisible = false;
      });
    },
    
    // 移除区域
    removeZone(index) {
      this.$confirm('确定要移除此区域吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.roomForm.zones.splice(index, 1);
        this.$message.success('区域已移除');
      }).catch(() => {});
    }
  },
  mounted() {
    // 加载自习室数据
    this.loadRooms();
  }
};
</script>

<style scoped>
.study-room-container {
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

.search-box {
  width: 300px;
}

.right-tools {
  display: flex;
  gap: 10px;
}

.room-card {
  margin-bottom: 20px;
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.count-num {
  font-weight: bold;
  color: #409EFF;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.occupancy-info {
  display: flex;
  flex-direction: column;
}

.zone-management {
  margin-bottom: 20px;
}

.zone-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.zone-tag {
  margin-right: 5px;
}

.add-zone-btn {
  margin-left: 10px;
}
</style> 