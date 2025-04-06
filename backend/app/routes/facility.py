from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, socketio
from app.models.user import User
from app.models.facility import Seat, SeatStatus, SeatType, StudyRoom, RoomType, RoomStatus, MaintenanceLog
from app.models.reservation import Reservation, ReservationStatus
import pandas as pd
import io
from datetime import datetime, time, timedelta

facility_bp = Blueprint('facility', __name__)

def get_user_id_from_jwt():
    """从JWT令牌中获取用户ID，支持不同格式的身份数据"""
    jwt_data = get_jwt_identity()
    
    # 获取用户ID
    if isinstance(jwt_data, dict) and 'id' in jwt_data:
        return jwt_data['id']
    elif isinstance(jwt_data, int):
        return jwt_data
    elif isinstance(jwt_data, str):
        try:
            return int(jwt_data)
        except ValueError:
            return None
    else:
        return None

def is_admin():
    """检查当前用户是否为管理员"""
    current_user_id = get_user_id_from_jwt()
    if current_user_id is None:
        return False
        
    user = User.query.get(current_user_id)
    return user and user.is_admin()

@facility_bp.route('/rooms', methods=['GET'])
@jwt_required()
def get_study_rooms():
    """获取所有自习室（管理员和学生）"""
    rooms = StudyRoom.query.all()
    
    return jsonify({
        'rooms': [room.to_dict() for room in rooms]
    }), 200

@facility_bp.route('/rooms', methods=['POST'])
@jwt_required()
def create_study_room():
    """创建自习室（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['name', 'floor', 'building', 'room_type', 'capacity', 'open_time', 'close_time']
    if not all(field in data for field in required_fields):
        return jsonify({'error': '缺少必填字段'}), 400
    
    # 转换时间格式
    try:
        open_time = datetime.strptime(data['open_time'], '%H:%M').time()
        close_time = datetime.strptime(data['close_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': '时间格式无效，请使用HH:MM格式'}), 400
    
    # 转换房间类型
    try:
        room_type = RoomType(data['room_type'])
    except ValueError:
        return jsonify({'error': '无效的房间类型'}), 400
    
    # 创建自习室
    room = StudyRoom(
        name=data['name'],
        floor=data['floor'],
        building=data['building'],
        room_type=room_type.value,
        capacity=data['capacity'],
        open_time=open_time,
        close_time=close_time,
        status=RoomStatus.OPEN.value,
        description=data.get('description', '')
    )
    
    # 确保 zones 属性被初始化，即使请求中没有提供
    # 使用 data.get('zones', []) 提供默认空列表给 setter
    room.zones = data.get('zones', [])
    
    db.session.add(room)
    db.session.commit()
    
    return jsonify({
        'message': '自习室创建成功',
        'room': room.to_dict()
    }), 201

@facility_bp.route('/rooms/<int:room_id>', methods=['PUT'])
@jwt_required()
def update_study_room(room_id):
    """更新自习室信息（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    room = StudyRoom.query.get(room_id)
    if not room:
        return jsonify({'error': '自习室不存在'}), 404
    
    data = request.get_json()
    
    # 更新基本信息
    if 'name' in data:
        room.name = data['name']
    if 'floor' in data:
        room.floor = data['floor']
    if 'building' in data:
        room.building = data['building']
    if 'capacity' in data:
        room.capacity = data['capacity']
    if 'description' in data:
        room.description = data['description']
    
    # 更新房间类型
    if 'room_type' in data:
        try:
            # 确保使用枚举的值
            room.room_type = RoomType(data['room_type']).value
        except ValueError:
            return jsonify({'error': '无效的房间类型'}), 400
    
    # 更新开放时间
    if 'open_time' in data:
        try:
            room.open_time = datetime.strptime(data['open_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': '开放时间格式无效，请使用HH:MM格式'}), 400
    
    # 更新关闭时间
    if 'close_time' in data:
        try:
            room.close_time = datetime.strptime(data['close_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': '关闭时间格式无效，请使用HH:MM格式'}), 400
    
    # 更新区域信息
    if 'zones' in data and isinstance(data['zones'], list):
        room.zones = data['zones']
    
    db.session.commit()
    
    return jsonify({
        'message': '自习室信息更新成功',
        'room': room.to_dict()
    }), 200

@facility_bp.route('/rooms/<int:room_id>/seats', methods=['GET'])
@jwt_required()
def get_room_seats(room_id):
    """获取自习室的所有座位，并根据指定时间段确定状态"""
    room = StudyRoom.query.get(room_id)
    if not room:
        return jsonify({'error': '自习室不存在'}), 404

    # 获取查询参数
    date_str = request.args.get('date')
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')

    # 验证并解析日期和时间参数
    query_start_dt = None
    query_end_dt = None
    if date_str and start_time_str and end_time_str:
        try:
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query_start_time = datetime.strptime(start_time_str, '%H:%M').time()
            query_end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            query_start_dt = datetime.combine(query_date, query_start_time)
            # 结束时间需要稍微增加一点，以包含边界情况
            query_end_dt = datetime.combine(query_date, query_end_time) - timedelta(seconds=1)

        except ValueError:
            return jsonify({'error': '日期或时间格式无效'}), 400

    # 获取该房间的所有座位
    seats = Seat.query.filter_by(room_id=room_id).all()
    seat_dicts = []

    for seat in seats:
        seat_data = seat.to_dict() # 获取基础信息
        current_status = seat.status # 获取座位的固有状态

        # 如果座位本身不是 AVAILABLE 或 OCCUPIED (例如是 MAINTENANCE)，直接使用该状态
        if current_status not in [SeatStatus.AVAILABLE, SeatStatus.OCCUPIED]:
            seat_data['status'] = current_status.value
        elif query_start_dt and query_end_dt:
            # 检查指定时间段内是否有冲突的预约
            # 状态为 ACTIVE 的算有效预约
            conflicting_reservation = Reservation.query.filter(
                Reservation.seat_id == seat.id,
                Reservation.status == ReservationStatus.ACTIVE,
                Reservation.start_time < query_end_dt, # 预约开始时间 < 查询结束时间
                Reservation.end_time > query_start_dt  # 预约结束时间 > 查询开始时间
            ).first()
            
            if conflicting_reservation:
                seat_data['status'] = SeatStatus.OCCUPIED.value # 时间段内被占用
            else:
                seat_data['status'] = SeatStatus.AVAILABLE.value # 时间段内可用
        else:
            # 如果没有提供时间参数，则返回座位的当前固有状态
            seat_data['status'] = current_status.value

        seat_dicts.append(seat_data)

    return jsonify({'seats': seat_dicts}), 200

@facility_bp.route('/rooms/<int:room_id>/seats', methods=['POST'])
@jwt_required()
def create_seat(room_id):
    """创建座位（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    room = StudyRoom.query.get(room_id)
    if not room:
        return jsonify({'error': '自习室不存在'}), 404
    
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['seat_number', 'seat_type', 'x_position', 'y_position']
    if not all(field in data for field in required_fields):
        return jsonify({'error': '缺少必填字段'}), 400
    
    # 检查座位号是否已存在
    existing_seat = Seat.query.filter_by(room_id=room_id, seat_number=data['seat_number']).first()
    if existing_seat:
        return jsonify({'error': '座位号已存在'}), 400
    
    # 转换座位类型
    try:
        seat_type = SeatType(data['seat_type'])
    except ValueError:
        return jsonify({'error': '无效的座位类型'}), 400
    
    # 创建座位
    seat = Seat(
        room_id=room_id,
        seat_number=data['seat_number'],
        seat_type=seat_type,
        status=SeatStatus.AVAILABLE,
        x_position=data['x_position'],
        y_position=data['y_position'],
        maintenance_note=data.get('maintenance_note', '')
    )
    
    db.session.add(seat)
    db.session.commit()
    
    # 通过WebSocket广播座位创建
    socketio.emit('seat_created', {
        'seat': seat.to_dict()
    })
    
    return jsonify({
        'message': '座位创建成功',
        'seat': seat.to_dict()
    }), 201

@facility_bp.route('/seats/<int:seat_id>', methods=['PUT'])
@jwt_required()
def update_seat(seat_id):
    """更新座位信息（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    seat = Seat.query.get(seat_id)
    if not seat:
        return jsonify({'error': '座位不存在'}), 404
    
    data = request.get_json()
    
    # 更新座位信息
    if 'seat_number' in data:
        # 检查座位号是否已存在
        existing_seat = Seat.query.filter_by(
            room_id=seat.room_id, 
            seat_number=data['seat_number']
        ).first()
        if existing_seat and existing_seat.id != seat_id:
            return jsonify({'error': '座位号已存在'}), 400
        seat.seat_number = data['seat_number']
    
    if 'seat_type' in data:
        try:
            seat.seat_type = SeatType(data['seat_type'])
        except ValueError:
            return jsonify({'error': '无效的座位类型'}), 400
    
    if 'status' in data:
        try:
            seat.status = SeatStatus(data['status'])
        except ValueError:
            return jsonify({'error': '无效的座位状态'}), 400
    
    if 'x_position' in data:
        seat.x_position = data['x_position']
    
    if 'y_position' in data:
        seat.y_position = data['y_position']
    
    if 'maintenance_note' in data:
        seat.maintenance_note = data['maintenance_note']
    
    db.session.commit()
    
    # 通过WebSocket广播座位更新
    socketio.emit('seat_updated', {
        'seat': seat.to_dict()
    })
    
    return jsonify({
        'message': '座位信息更新成功',
        'seat': seat.to_dict()
    }), 200

@facility_bp.route('/seats/<int:seat_id>/status', methods=['PATCH'])
@jwt_required()
def update_seat_status(seat_id):
    """更新座位状态（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    seat = Seat.query.get(seat_id)
    if not seat:
        return jsonify({'error': '座位不存在'}), 404
    
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'error': '缺少状态参数'}), 400
    
    try:
        new_status = SeatStatus(data['status'])
    except ValueError:
        return jsonify({'error': '无效的座位状态'}), 400
    
    # 如果更新为维修状态，创建维修记录
    if new_status == SeatStatus.MAINTENANCE and seat.status != SeatStatus.MAINTENANCE:
        if 'reason' not in data:
            return jsonify({'error': '设置维修状态需要提供原因'}), 400
        
        current_user_id = get_user_id_from_jwt()
        
        maintenance_log = MaintenanceLog(
            seat_id=seat_id,
            admin_id=current_user_id,
            reason=data['reason'],
            status='in_progress'
        )
        
        db.session.add(maintenance_log)
    
    # 如果从维修状态恢复，更新维修记录
    elif seat.status == SeatStatus.MAINTENANCE and new_status != SeatStatus.MAINTENANCE:
        maintenance_log = MaintenanceLog.query.filter_by(
            seat_id=seat_id,
            status='in_progress'
        ).first()
        
        if maintenance_log:
            maintenance_log.end_time = datetime.utcnow()
            maintenance_log.status = 'completed'
    
    # 更新座位状态
    seat.status = new_status
    db.session.commit()
    
    # 通过WebSocket广播座位状态更新
    socketio.emit('seat_status_changed', {
        'seat_id': seat.id,
        'status': seat.status.value
    })
    
    return jsonify({
        'message': '座位状态更新成功',
        'seat': seat.to_dict()
    }), 200

@facility_bp.route('/maintenance-logs', methods=['GET'])
@jwt_required()
def get_maintenance_logs():
    """获取维修记录（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    # 过滤参数
    seat_id = request.args.get('seat_id', type=int)
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = MaintenanceLog.query
    
    if seat_id:
        query = query.filter_by(seat_id=seat_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if start_date:
        try:
            start_datetime = datetime.fromisoformat(start_date)
            query = query.filter(MaintenanceLog.start_time >= start_datetime)
        except ValueError:
            return jsonify({'error': '开始日期格式无效'}), 400
    
    if end_date:
        try:
            end_datetime = datetime.fromisoformat(end_date)
            query = query.filter(MaintenanceLog.start_time <= end_datetime)
        except ValueError:
            return jsonify({'error': '结束日期格式无效'}), 400
    
    logs = query.order_by(MaintenanceLog.start_time.desc()).all()
    
    return jsonify({
        'maintenance_logs': [log.to_dict() for log in logs]
    }), 200

@facility_bp.route('/import-seats', methods=['POST'])
@jwt_required()
def import_seats():
    """批量导入座位信息（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': '缺少文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 验证文件是否为Excel
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'error': '只支持Excel文件(.xlsx, .xls)'}), 400
    
    try:
        # 读取Excel文件
        df = pd.read_excel(file)
        
        # 验证必要字段
        required_columns = ['room_id', 'seat_number', 'seat_type', 'x_position', 'y_position']
        
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': f'Excel文件缺少必要字段: {", ".join(required_columns)}'}), 400
        
        # 记录成功和失败的导入
        success_count = 0
        error_records = []
        
        # 处理每一行数据
        for index, row in df.iterrows():
            try:
                # 检查自习室是否存在
                room_id = int(row['room_id'])
                room = StudyRoom.query.get(room_id)
                
                if not room:
                    error_records.append({
                        'row': index + 2,  # Excel行号从1开始，且有标题行
                        'error': f'自习室不存在: {room_id}'
                    })
                    continue
                
                # 检查座位号是否已存在
                seat_number = str(row['seat_number'])
                existing_seat = Seat.query.filter_by(room_id=room_id, seat_number=seat_number).first()
                
                if existing_seat:
                    error_records.append({
                        'row': index + 2,
                        'error': f'座位号已存在: {seat_number}'
                    })
                    continue
                
                # 转换座位类型
                try:
                    seat_type = SeatType(row['seat_type'])
                except ValueError:
                    error_records.append({
                        'row': index + 2,
                        'error': f'无效的座位类型: {row["seat_type"]}'
                    })
                    continue
                
                # 创建新座位
                seat = Seat(
                    room_id=room_id,
                    seat_number=seat_number,
                    seat_type=seat_type,
                    status=SeatStatus.AVAILABLE,
                    x_position=int(row['x_position']),
                    y_position=int(row['y_position']),
                    maintenance_note=str(row.get('maintenance_note', ''))
                )
                
                db.session.add(seat)
                success_count += 1
                
            except Exception as e:
                error_records.append({
                    'row': index + 2,
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'message': f'成功导入{success_count}个座位',
            'success_count': success_count,
            'error_count': len(error_records),
            'errors': error_records
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'导入失败: {str(e)}'}), 500

@facility_bp.route('/export-seats', methods=['GET'])
@jwt_required()
def export_seats():
    """导出座位信息（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    room_id = request.args.get('room_id', type=int)
    
    # 构建查询
    query = Seat.query
    
    if room_id:
        room = StudyRoom.query.get(room_id)
        if not room:
            return jsonify({'error': '自习室不存在'}), 404
        
        query = query.filter_by(room_id=room_id)
    
    seats = query.all()
    
    # 创建DataFrame
    data = []
    for seat in seats:
        room = StudyRoom.query.get(seat.room_id)
        
        data.append({
            'room_id': seat.room_id,
            'room_name': room.name,
            'seat_id': seat.id,
            'seat_number': seat.seat_number,
            'seat_type': seat.seat_type.value,
            'status': seat.status.value,
            'x_position': seat.x_position,
            'y_position': seat.y_position,
            'maintenance_note': seat.maintenance_note or ''
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel输出
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Seats', index=False)
    
    output.seek(0)
    
    # 设置文件名
    filename = f'seats_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
    
    return output.getvalue(), 200, {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': f'attachment; filename="{filename}"'
    }

@facility_bp.route('/rooms/<int:room_id>/status', methods=['PATCH'])
@jwt_required()
def update_study_room_status(room_id):
    """更新自习室状态（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    room = StudyRoom.query.get(room_id)
    if not room:
        return jsonify({'error': '自习室不存在'}), 404
    
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'error': '缺少状态参数'}), 400
    
    status = data['status']
    if status not in ['open', 'closed', 'maintenance']:
        return jsonify({'error': '无效的状态值'}), 400
    
    # 如果关闭自习室，取消所有待处理的预约
    if status == 'closed':
        current_reservations = Reservation.query.join(Seat, Seat.id == Reservation.seat_id)\
            .filter(Seat.room_id == room_id, Reservation.status == ReservationStatus.ACTIVE)\
            .all()
        
        for reservation in current_reservations:
            reservation.status = ReservationStatus.CANCELLED
            
        # 更新所有座位为维护状态
        seats = Seat.query.filter_by(room_id=room_id).all()
        for seat in seats:
            seat.status = SeatStatus.MAINTENANCE
    
    # 保存自习室状态变更
    room.status = status
    db.session.commit()
    
    # 通过WebSocket广播自习室状态更新
    socketio.emit('room_status_changed', {
        'room_id': room.id,
        'status': status
    })
    
    return jsonify({
        'message': '自习室状态更新成功',
        'room': room.to_dict()
    }), 200

@facility_bp.route('/rooms/<int:room_id>', methods=['DELETE'])
@jwt_required()
def delete_study_room(room_id):
    """删除自习室（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    room = StudyRoom.query.get(room_id)
    if not room:
        return jsonify({'error': '自习室不存在'}), 404
    
    # 检查是否有进行中的预约
    active_reservations = Reservation.query.join(Seat, Seat.id == Reservation.seat_id)\
        .filter(Seat.room_id == room_id, Reservation.status == ReservationStatus.ACTIVE)\
        .count()
    
    if active_reservations > 0:
        return jsonify({'error': '该自习室有进行中的预约，无法删除'}), 400
    
    # 删除自习室相关的所有座位
    Seat.query.filter_by(room_id=room_id).delete()
    
    # 删除自习室
    db.session.delete(room)
    db.session.commit()
    
    return jsonify({'message': '自习室删除成功'}), 200 