from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db, socketio
from app.models.user import User
from app.models.facility import Seat, SeatStatus, StudyRoom
from app.models.reservation import Reservation, ReservationStatus, CheckIn
from app.utils.qrcode import generate_qrcode
from datetime import datetime, timedelta
import math
import uuid

seat_bp = Blueprint('seat', __name__)

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

@seat_bp.route('/rooms', methods=['GET'])
@jwt_required()
def get_rooms():
    """获取所有自习室"""
    rooms = StudyRoom.query.all()
    include_seats = request.args.get('include_seats', 'false').lower() == 'true'
    
    return jsonify({
        'rooms': [room.to_dict(include_seats=include_seats) for room in rooms]
    }), 200

@seat_bp.route('/rooms/<int:room_id>', methods=['GET'])
@jwt_required()
def get_room(room_id):
    """获取自习室详情"""
    room = StudyRoom.query.get(room_id)
    if not room:
        return jsonify({'error': '自习室不存在'}), 404
    
    return jsonify({'room': room.to_dict(include_seats=True)}), 200

@seat_bp.route('/rooms/<int:room_id>/seats', methods=['GET'])
@jwt_required()
def get_room_seats(room_id):
    """获取自习室座位列表"""
    room = StudyRoom.query.get(room_id)
    if not room:
        return jsonify({'error': '自习室不存在'}), 404
    
    # 过滤参数
    seat_type = request.args.get('seat_type')
    status = request.args.get('status')
    
    seats_query = Seat.query.filter_by(room_id=room_id)
    
    if seat_type:
        seats_query = seats_query.filter_by(seat_type=seat_type)
    if status:
        seats_query = seats_query.filter_by(status=status)
    
    seats = seats_query.all()
    
    return jsonify({
        'seats': [seat.to_dict(include_reservations=True) for seat in seats]
    }), 200

@seat_bp.route('/availability', methods=['GET'])
@jwt_required()
def check_seat_availability():
    """检查座位在指定时间段的可用性"""
    seat_id = request.args.get('seat_id', type=int)
    start_time_str = request.args.get('start_time')
    end_time_str = request.args.get('end_time')
    
    if not all([seat_id, start_time_str, end_time_str]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
    except ValueError:
        return jsonify({'error': '时间格式无效'}), 400
    
    # 检查时间范围是否有效
    if end_time <= start_time:
        return jsonify({'error': '结束时间必须晚于开始时间'}), 400
    
    # 检查时长是否超过最大限制
    max_hours = current_app.config.get('RESERVATION_MAX_HOURS', 4)
    if (end_time - start_time).total_seconds() > max_hours * 3600:
        return jsonify({'error': f'预约时长不能超过{max_hours}小时'}), 400
    
    # 检查座位是否存在
    seat = Seat.query.get(seat_id)
    if not seat:
        return jsonify({'error': '座位不存在'}), 404
    
    # 检查座位状态
    if seat.status != SeatStatus.AVAILABLE:
        return jsonify({'error': '座位不可用', 'status': seat.status.value}), 400
    
    # 检查是否与现有预约冲突
    conflicting_reservations = Reservation.query.filter(
        Reservation.seat_id == seat_id,
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.ACTIVE]),
        Reservation.start_time < end_time,
        Reservation.end_time > start_time
    ).all()
    
    if conflicting_reservations:
        return jsonify({
            'available': False,
            'conflicting_times': [
                {
                    'start_time': r.start_time.isoformat(),
                    'end_time': r.end_time.isoformat()
                } for r in conflicting_reservations
            ]
        }), 200
    
    return jsonify({'available': True}), 200

@seat_bp.route('/reserve', methods=['POST'])
@jwt_required()
def reserve_seat():
    """预约座位"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 检查用户是否可以预约
    if not user.can_make_reservation():
        return jsonify({'error': '您当前无法预约座位，可能由于账户状态或失信记录'}), 403
    
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['seat_id', 'start_time', 'end_time']
    if not all(field in data for field in required_fields):
        return jsonify({'error': '缺少必填字段'}), 400
    
    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except ValueError:
        return jsonify({'error': '时间格式无效'}), 400
    
    # 检查时间范围是否有效
    if end_time <= start_time:
        return jsonify({'error': '结束时间必须晚于开始时间'}), 400
    
    # 检查时长是否超过最大限制
    max_hours = current_app.config.get('RESERVATION_MAX_HOURS', 4)
    if (end_time - start_time).total_seconds() > max_hours * 3600:
        return jsonify({'error': f'预约时长不能超过{max_hours}小时'}), 400
    
    # 检查座位是否存在
    seat = Seat.query.get(data['seat_id'])
    if not seat:
        return jsonify({'error': '座位不存在'}), 404
    
    # 检查座位状态
    if seat.status != SeatStatus.AVAILABLE:
        return jsonify({'error': '座位不可用', 'status': seat.status.value}), 400
    
    # 检查是否与现有预约冲突
    conflicting_reservations = Reservation.query.filter(
        Reservation.seat_id == data['seat_id'],
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.ACTIVE]),
        Reservation.start_time < end_time,
        Reservation.end_time > start_time
    ).all()
    
    if conflicting_reservations:
        return jsonify({
            'error': '所选时段已被预约',
            'conflicting_times': [
                {
                    'start_time': r.start_time.isoformat(),
                    'end_time': r.end_time.isoformat()
                } for r in conflicting_reservations
            ]
        }), 400
    
    # 创建预约
    reservation = Reservation(
        user_id=current_user_id,
        seat_id=data['seat_id'],
        start_time=start_time,
        end_time=end_time,
        status=ReservationStatus.PENDING
    )
    
    # 生成预约二维码
    # qrcode_data = str(uuid.uuid4()) # UUID 作为二维码内容
    # qrcode_url = generate_qrcode(qrcode_data, f"reservation_{reservation.id}") # 不直接生成和存储 Base64 URL
    # reservation.qrcode_url = qrcode_url # 不存储完整的 Base64 URL
    
    # 仅存储用于生成二维码的唯一标识符（例如，预约ID本身或UUID）
    # 这里我们选择不直接存储 URL，可以在需要时生成
    # reservation.qrcode_url = qrcode_data # 如果选择存储 UUID
    reservation.qrcode_url = f"/api/reservations/{reservation.id}/qrcode" # 存储一个指向动态生成二维码的URL
    
    db.session.add(reservation)
    db.session.commit()
    
    # 通过WebSocket广播座位状态更新 (移除或修改)
    # 简单的移除：
    # socketio.emit('seat_status_changed', {
    #     'seat_id': seat.id,
    #     'status': seat.status.value
    # })
    # 或者广播一个不同的事件，例如预约成功事件
    socketio.emit('reservation_created', {'reservation': reservation.to_dict(include_seat=True)})
    
    return jsonify({
        'message': '预约成功',
        'reservation': reservation.to_dict(include_seat=True)
    }), 201

@seat_bp.route('/reservations', methods=['GET'])
@jwt_required()
def get_reservations():
    """获取用户的预约列表"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    print(f"获取预约请求 - 用户ID: {current_user_id}")
    
    if not user:
        print(f"用户不存在: {current_user_id}")
        return jsonify({'error': '用户不存在'}), 404
    
    # 过滤参数
    status = request.args.get('status')
    print(f"查询参数 - status: {status}")
    
    # 默认只显示当前和未来的预约
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"当前时间: {datetime.now().isoformat()}")
    
    reservations_query = Reservation.query.filter_by(user_id=current_user_id)
    
    if status:
        # 处理逗号分隔的多状态查询
        if ',' in status:
            status_list = [s.strip() for s in status.split(',')]
            print(f"查询多个状态: {status_list}")
            try:
                # 将字符串状态转换为枚举值
                status_values = []
                for s in status_list:
                    for enum_val in ReservationStatus:
                        if enum_val.value == s:
                            status_values.append(enum_val)
                            break
                print(f"处理后的状态枚举: {[s.value for s in status_values]}")
                reservations_query = reservations_query.filter(Reservation.status.in_(status_values))
            except Exception as e:
                print(f"状态值处理错误: {e}")
                # 错误时，使用默认查询继续
                reservations_query = reservations_query.filter(
                    Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.ACTIVE])
                )
        else:
            print(f"查询单个状态: {status}")
            try:
                # 查找匹配的枚举值
                status_enum = None
                for enum_val in ReservationStatus:
                    if enum_val.value == status:
                        status_enum = enum_val
                        break
                
                if status_enum:
                    print(f"找到匹配的状态枚举: {status_enum.value}")
                    reservations_query = reservations_query.filter_by(status=status_enum)
                else:
                    print(f"未找到匹配的状态枚举: {status}")
                    # 如果找不到匹配的枚举，使用默认查询
                    reservations_query = reservations_query.filter(
                        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.ACTIVE])
                    )
            except Exception as e:
                print(f"单个状态处理错误: {e}")
                # 错误时，使用默认查询继续
                reservations_query = reservations_query.filter(
                    Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.ACTIVE])
                )
    else:
        # 默认只显示未完成的预约
        reservations_query = reservations_query.filter(
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.ACTIVE])
        )
        print("未指定状态，默认查询PENDING和ACTIVE")
    
    # 按开始时间排序
    reservations = reservations_query.order_by(Reservation.start_time).all()
    print(f"找到 {len(reservations)} 条预约记录")
    
    for i, r in enumerate(reservations):
        print(f"预约 {i+1}/{len(reservations)} - ID: {r.id}, 状态: {r.status.value}, 时间: {r.start_time} - {r.end_time}")
        # 额外检查座位和自习室信息
        if r.seat:
            print(f"  座位: ID={r.seat.id}, 编号={r.seat.seat_number}")
            if r.seat.room:
                print(f"  自习室: ID={r.seat.room.id}, 名称={r.seat.room.name}")
            else:
                print("  自习室信息不可用")
        else:
            print("  座位信息不可用")
    
    # 确保在返回预约信息时包含座位和自习室信息
    result = {'reservations': [r.to_dict(include_seat=True) for r in reservations]}
    print(f"返回 {len(result['reservations'])} 条预约记录")
    
    return jsonify(result), 200

@seat_bp.route('/reservations/current', methods=['GET'])
@jwt_required()
def get_current_reservations():
    """获取用户当前的预约"""
    try:
        # 获取当前用户ID
        current_user_id = get_user_id_from_jwt()
        print(f"当前用户ID: {current_user_id}")
        
        if current_user_id is None:
            return jsonify({'error': '无效的JWT令牌格式'}), 401
        
        # 获取用户
        user = User.query.get(current_user_id)
        print(f"用户查询结果: {user}")
        
        if not user:
            return jsonify({'error': '用户不存在，ID: ' + str(current_user_id)}), 404
        
        # 获取当前和未来的预约
        now = datetime.now()
        print(f"当前时间: {now}")
        
        reservations_query = Reservation.query.filter_by(user_id=current_user_id).filter(
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.ACTIVE])
        )
        
        # 按开始时间排序
        reservations = reservations_query.order_by(Reservation.start_time).all()
        print(f"查询到的预约数量: {len(reservations)}")
        
        result = [r.to_dict(include_seat=True) for r in reservations]
        print(f"返回结果: {result}")
        
        return jsonify(result), 200
    except Exception as e:
        print(f"获取当前预约时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'获取预约失败: {str(e)}'}), 500

@seat_bp.route('/reservations/history', methods=['GET'])
@jwt_required()
def get_history_reservations():
    """获取用户历史预约记录"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取已完成、已取消或过期的预约
    reservations_query = Reservation.query.filter_by(user_id=current_user_id).filter(
        Reservation.status.in_([
            ReservationStatus.COMPLETED, 
            ReservationStatus.CANCELLED, 
            ReservationStatus.EXPIRED
        ])
    )
    
    # 按开始时间倒序排序（最新的排在前面）
    paginated_reservations = reservations_query.order_by(Reservation.start_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [r.to_dict(include_seat=True) for r in paginated_reservations.items],
        'total': paginated_reservations.total,
        'pages': paginated_reservations.pages,
        'page': page,
        'per_page': per_page
    }), 200

@seat_bp.route('/reservations/<int:reservation_id>/check-in', methods=['POST'])
@jwt_required()
def check_in_reservation(reservation_id):
    """使用签到码进行签到"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    check_in_code = data.get('check_in_code')
    
    if not check_in_code:
        return jsonify({'error': '缺少签到码'}), 400
    
    reservation = Reservation.query.get(reservation_id)
    
    if not reservation:
        return jsonify({'error': '预约不存在'}), 404
    
    # 验证是否是自己的预约
    if reservation.user_id != current_user_id:
        return jsonify({'error': '不是您的预约'}), 403
    
    # 检查预约状态
    if reservation.status != ReservationStatus.PENDING:
        return jsonify({'error': '预约状态不是待签到'}), 400
    
    # 检查是否可以签到
    if not reservation.can_checkin():
        return jsonify({'error': '不在签到时间范围内'}), 400
    
    # TODO: 验证签到码
    # 简化处理，这里应该添加实际的签到码验证逻辑
    
    # 创建签到记录
    checkin = CheckIn(
        reservation_id=reservation.id,
        checkin_time=datetime.utcnow(),
        checkin_location="manual"
    )
    
    # 更新预约状态
    reservation.status = ReservationStatus.ACTIVE
    reservation.checkin_time = datetime.utcnow()
    
    db.session.add(checkin)
    db.session.commit()
    
    return jsonify({
        'message': '签到成功',
        'checkin': checkin.to_dict()
    }), 200

@seat_bp.route('/reservations/<int:reservation_id>/check-out', methods=['POST'])
@jwt_required()
def check_out_reservation(reservation_id):
    """签退预约"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    reservation = Reservation.query.get(reservation_id)
    
    if not reservation:
        return jsonify({'error': '预约不存在'}), 404
    
    # 验证是否是自己的预约
    if reservation.user_id != current_user_id and not user.is_admin():
        return jsonify({'error': '不是您的预约或权限不足'}), 403
    
    # 检查预约状态
    if reservation.status != ReservationStatus.ACTIVE:
        return jsonify({'error': '预约状态不是使用中'}), 400
    
    # 获取签到记录
    checkin = CheckIn.query.filter_by(reservation_id=reservation.id).first()
    
    if not checkin:
        return jsonify({'error': '找不到签到记录'}), 404
    
    # 更新签退信息
    now = datetime.utcnow()
    checkin.checkout_time = now
    checkin.checkout_location = "manual"
    
    # 计算使用时长（分钟）
    duration = (now - checkin.checkin_time).total_seconds() // 60
    checkin.duration = duration
    
    # 更新预约状态
    reservation.status = ReservationStatus.COMPLETED
    reservation.checkout_time = now
    
    # 更新座位状态
    seat = Seat.query.get(reservation.seat_id)
    seat.status = SeatStatus.AVAILABLE
    
    db.session.commit()
    
    # 通过WebSocket广播座位状态更新
    socketio.emit('seat_status_changed', {
        'seat_id': seat.id,
        'status': seat.status.value
    })
    
    return jsonify({
        'message': '签退成功',
        'duration': duration
    }), 200

@seat_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_reservation_api(reservation_id):
    """通过API取消预约"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    reservation = Reservation.query.get(reservation_id)
    
    if not reservation:
        return jsonify({'error': '预约不存在'}), 404
    
    # 验证权限（管理员或预约本人）
    if reservation.user_id != current_user_id and not user.is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    # 检查是否可以取消
    if not reservation.can_cancel() and not user.is_admin():
        return jsonify({'error': '已经超过可取消时间（开始前30分钟）'}), 400
    
    # 更新预约状态
    reservation.status = ReservationStatus.CANCELLED
    
    # 更新座位状态
    seat = Seat.query.get(reservation.seat_id)
    seat.status = SeatStatus.AVAILABLE
    
    db.session.commit()
    
    # 通过WebSocket广播座位状态更新
    socketio.emit('seat_status_changed', {
        'seat_id': seat.id,
        'status': seat.status.value
    })
    
    return jsonify({'message': '预约已取消'}), 200

@seat_bp.route('/reservations/<int:reservation_id>', methods=['GET'])
@jwt_required()
def get_reservation(reservation_id):
    """获取预约详情"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    reservation = Reservation.query.get(reservation_id)
    
    if not reservation:
        return jsonify({'error': '预约不存在'}), 404
    
    # 验证权限（管理员或预约本人）
    if reservation.user_id != current_user_id and not user.is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    return jsonify({
        'reservation': reservation.to_dict(include_user=True, include_seat=True)
    }), 200

@seat_bp.route('/check-in', methods=['POST'])
@jwt_required()
def manual_check_in():
    """使用预约码进行手动签到"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    check_in_code = data.get('check_in_code')
    
    if not check_in_code:
        return jsonify({'error': '缺少签到码'}), 400
    
    # 根据签到码查找预约
    # 签到码可能是预约ID的编码，这里简化处理为直接查找预约ID
    try:
        # 假设签到码是预约ID的某种编码形式，这里简化处理
        reservation_id = int(check_in_code)
        reservation = Reservation.query.get(reservation_id)
    except ValueError:
        # 如果不是整数，可能是其他格式的签到码
        # 在实际项目中，应该有更复杂的签到码匹配逻辑
        return jsonify({'error': '无效的签到码'}), 400
    
    if not reservation:
        return jsonify({'error': '预约不存在'}), 404
    
    # 验证是否是自己的预约
    if reservation.user_id != current_user_id:
        return jsonify({'error': '不是您的预约'}), 403
    
    # 检查预约状态
    if reservation.status != ReservationStatus.PENDING:
        return jsonify({'error': '预约状态不是待签到'}), 400
    
    # 检查是否可以签到
    if not reservation.can_checkin():
        return jsonify({'error': '不在签到时间范围内'}), 400
    
    # 创建签到记录
    checkin = CheckIn(
        reservation_id=reservation.id,
        checkin_time=datetime.utcnow(),
        checkin_location="manual"
    )
    
    # 更新预约状态
    reservation.status = ReservationStatus.ACTIVE
    reservation.checkin_time = datetime.utcnow()
    
    db.session.add(checkin)
    db.session.commit()
    
    # 获取座位和自习室信息用于返回
    seat_data = {}
    room_name = "未知自习室"
    seat_number = "未知座位"
    
    if reservation.seat:
        seat_number = reservation.seat.seat_number or "未知座位"
        if reservation.seat.room:
            room_name = reservation.seat.room.name or "未知自习室"
    
    return jsonify({
        'message': '签到成功',
        'room_name': room_name,
        'seat_number': seat_number,
        'checkin': checkin.to_dict()
    }), 200

@seat_bp.route('/reservations/<int:reservation_id>/extend', methods=['POST'])
@jwt_required()
def extend_reservation(reservation_id):
    """延长预约时间"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    duration = data.get('duration', 60)  # 默认延长60分钟
    
    # 验证duration是否为整数
    try:
        duration = int(duration)
        if duration <= 0:
            return jsonify({'error': '延长时间必须大于0分钟'}), 400
    except ValueError:
        return jsonify({'error': '延长时间必须为整数'}), 400
    
    # 获取预约
    reservation = Reservation.query.get(reservation_id)
    
    if not reservation:
        return jsonify({'error': '预约不存在'}), 404
    
    # 验证是否是自己的预约
    if reservation.user_id != current_user_id:
        return jsonify({'error': '不是您的预约'}), 403
    
    # 验证预约状态
    if reservation.status not in [ReservationStatus.PENDING, ReservationStatus.ACTIVE]:
        return jsonify({'error': f'预约状态不允许延长时间: {reservation.status.value}'}), 400
    
    # 验证预约是否已结束
    now = datetime.utcnow()
    if reservation.end_time <= now:
        return jsonify({'error': '预约已结束，无法延长时间'}), 400
    
    # 计算新的结束时间
    old_end_time = reservation.end_time
    new_end_time = old_end_time + timedelta(minutes=duration)
    
    # 验证是否超出自习室开放时间
    # 在实际项目中，需要检查自习室的开放时间
    # 简化处理，这里假设自习室24小时开放
    
    # 验证是否与其他预约冲突
    # 检查该座位在新结束时间之前是否有其他预约开始
    conflicting_reservations = Reservation.query.filter(
        Reservation.seat_id == reservation.seat_id,
        Reservation.id != reservation.id,
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.ACTIVE]),
        Reservation.start_time < new_end_time,
        Reservation.start_time > old_end_time
    ).all()
    
    if conflicting_reservations:
        # 找到最早的冲突预约
        earliest_conflict = min(conflicting_reservations, key=lambda r: r.start_time)
        max_extend_minutes = int((earliest_conflict.start_time - old_end_time).total_seconds() / 60)
        
        if max_extend_minutes <= 0:
            return jsonify({'error': '无法延长时间，与其他预约冲突'}), 400
        
        return jsonify({
            'error': f'延长时间过长，与其他预约冲突',
            'max_duration': max_extend_minutes
        }), 400
    
    # 更新预约结束时间
    reservation.end_time = new_end_time
    db.session.commit()
    
    # 通过WebSocket广播预约更新
    socketio.emit('reservation_updated', {
        'reservation_id': reservation.id,
        'seat_id': reservation.seat_id,
        'end_time': new_end_time.isoformat()
    })
    
    return jsonify({
        'message': '预约时间已延长',
        'old_end_time': old_end_time.isoformat(),
        'new_end_time': new_end_time.isoformat(),
        'extended_minutes': duration,
        'reservation': reservation.to_dict(include_seat=True)
    }), 200

@seat_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取当前用户的仪表板统计数据"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 获取今日日期（0点0分）
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # 一个月前
    one_month_ago = today - timedelta(days=30)
    
    # 今日预约数
    today_reservations = Reservation.query.filter(
        Reservation.user_id == current_user_id,
        Reservation.start_time >= today,
        Reservation.start_time < today + timedelta(days=1)
    ).count()
    
    # 待签到预约数
    pending_reservations = Reservation.query.filter(
        Reservation.user_id == current_user_id,
        Reservation.status == ReservationStatus.PENDING
    ).count()
    
    # 本月学习总时长(分钟)
    completed_reservations = Reservation.query.filter(
        Reservation.user_id == current_user_id,
        Reservation.status == ReservationStatus.COMPLETED,
        Reservation.checkout_time >= one_month_ago
    ).all()
    
    study_minutes = 0
    for reservation in completed_reservations:
        if reservation.checkin and reservation.checkin.duration:
            study_minutes += reservation.checkin.duration
    
    # 将分钟转换为小时
    study_hours = math.ceil(study_minutes / 60)
    
    # 失信记录
    failed_checkins = user.failed_checkins
    
    return jsonify({
        'today_reservations': today_reservations,
        'pending_reservations': pending_reservations,
        'study_hours': study_hours,
        'failed_checkins': failed_checkins
    }), 200

@seat_bp.route('/dashboard/recent_reservations', methods=['GET'])
@jwt_required()
def get_recent_reservations():
    """获取用户最近的预约记录"""
    current_user_id = get_user_id_from_jwt()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 获取最近的预约（按开始时间倒序排列，限制5条）
    recent_reservations = Reservation.query.filter(
        Reservation.user_id == current_user_id
    ).order_by(Reservation.start_time.desc()).limit(5).all()
    
    # 准备返回数据
    result = []
    for reservation in recent_reservations:
        room_name = "未知自习室"
        seat_number = "未知座位"
        
        if reservation.seat:
            seat_number = reservation.seat.seat_number or "未知座位"
            if reservation.seat.room:
                room_name = reservation.seat.room.name or "未知自习室"
        
        # 格式化日期和时间
        start_time = reservation.start_time
        end_time = reservation.end_time
        date_str = start_time.strftime("%Y-%m-%d")
        time_str = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
        
        result.append({
            'id': reservation.id,
            'room': room_name,
            'seat': seat_number,
            'date': date_str,
            'time': time_str,
            'status': reservation.status.value
        })
    
    return jsonify(result), 200

@seat_bp.route('/dashboard/rooms_status', methods=['GET'])
@jwt_required()
def get_rooms_status():
    """获取自习室状态统计"""
    # 查询所有自习室
    study_rooms = StudyRoom.query.all()
    
    result = []
    for room in study_rooms:
        # 获取该自习室的所有座位
        seats = Seat.query.filter_by(room_id=room.id).all()
        
        total_seats = len(seats)
        available_seats = sum(1 for seat in seats if seat.status == SeatStatus.AVAILABLE)
        occupied_seats = total_seats - available_seats
        
        result.append({
            'id': room.id,
            'name': room.name,
            'totalSeats': total_seats,
            'availableSeats': available_seats,
            'occupiedSeats': occupied_seats
        })
    
    return jsonify(result), 200 