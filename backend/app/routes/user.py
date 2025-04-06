from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, UserStatus
import csv
import io
import datetime

user_bp = Blueprint('user', __name__)

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

@user_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 过滤参数
    status = request.args.get('status')
    role = request.args.get('role')
    query = request.args.get('query')  # 搜索姓名、邮箱或学号
    
    users_query = User.query
    
    # 应用过滤
    if status:
        users_query = users_query.filter(User.status == status)
    if role:
        users_query = users_query.filter(User.role == role)
    if query:
        users_query = users_query.filter(
            (User.name.ilike(f'%{query}%')) |
            (User.email.ilike(f'%{query}%')) |
            (User.student_id.ilike(f'%{query}%'))
        )
    
    # 分页
    pagination = users_query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'users': [user.to_dict() for user in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """获取用户详情（管理员或用户本人）"""
    current_user_id = get_user_id_from_jwt()
    if current_user_id is None:
        return jsonify({'error': '无效的JWT令牌格式'}), 401
    
    # 验证权限
    if current_user_id != user_id and not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    include_reservations = request.args.get('include_reservations', 'false').lower() == 'true'
    
    return jsonify({'user': user.to_dict(include_reservations=include_reservations)}), 200

@user_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息（管理员或用户本人）"""
    current_user_id = get_user_id_from_jwt()
    if current_user_id is None:
        return jsonify({'error': '无效的JWT令牌格式'}), 401
        
    current_user = User.query.get(current_user_id)
    
    # 验证权限
    if current_user_id != user_id and not current_user.is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 更新基本信息
    if 'name' in data:
        user.name = data['name']
    if 'phone' in data:
        user.phone = data['phone']
        
    # 管理员可以更新额外字段
    if current_user.is_admin():
        if 'status' in data:
            user.status = UserStatus(data['status'])
        if 'student_id' in data:
            # 检查学号是否已存在
            existing = User.query.filter_by(student_id=data['student_id']).first()
            if existing and existing.id != user_id:
                return jsonify({'error': '学号已被其他用户使用'}), 400
            user.student_id = data['student_id']
    
    db.session.commit()
    
    return jsonify({'message': '用户信息更新成功', 'user': user.to_dict()}), 200

@user_bp.route('/<int:user_id>/status', methods=['PATCH'])
@jwt_required()
def update_user_status(user_id):
    """更新用户状态（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'error': '缺少状态参数'}), 400
    
    try:
        user.status = UserStatus(data['status'])
        db.session.commit()
        return jsonify({'message': '用户状态已更新', 'user': user.to_dict()}), 200
    except ValueError:
        return jsonify({'error': '无效的状态值'}), 400

@user_bp.route('/export', methods=['GET'])
@jwt_required()
def export_users():
    """导出用户列表为CSV（仅管理员）"""
    if not is_admin():
        return jsonify({'error': '权限不足'}), 403
    
    # 创建CSV输出
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入标题行
    writer.writerow(['ID', '姓名', '邮箱', '学号', '电话', '角色', '状态', '注册时间'])
    
    # 查询用户
    users = User.query.all()
    
    # 写入数据行
    for user in users:
        writer.writerow([
            user.id,
            user.name,
            user.email,
            user.student_id or '',
            user.phone or '',
            user.role.value,
            user.status.value,
            user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # 设置响应头
    output.seek(0)
    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f'users_export_{now}.csv'
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename="{filename}"'
    }

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户的个人资料"""
    current_user_id = get_user_id_from_jwt()
    if current_user_id is None:
        return jsonify({'error': '无效的JWT令牌格式'}), 401
        
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify(user.to_dict()), 200

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新当前用户的个人资料"""
    current_user_id = get_user_id_from_jwt()
    if current_user_id is None:
        return jsonify({'error': '无效的JWT令牌格式'}), 401
        
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 更新基本信息
    if 'name' in data:
        user.name = data['name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'email' in data:
        user.email = data['email']
    
    db.session.commit()
    
    return jsonify({'message': '个人资料更新成功', 'user': user.to_dict()}), 200

@user_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password_profile():
    """修改当前用户密码"""
    current_user_id = get_user_id_from_jwt()
    if current_user_id is None:
        return jsonify({'error': '无效的JWT令牌格式'}), 401
        
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 验证旧密码
    if not user.check_password(data.get('current_password', '')):
        return jsonify({'error': '当前密码不正确'}), 401
    
    # 设置新密码
    user.set_password(data.get('new_password'))
    db.session.commit()
    
    return jsonify({'message': '密码修改成功'}), 200 