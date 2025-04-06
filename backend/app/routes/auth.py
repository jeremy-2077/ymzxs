from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User, UserRole, UserStatus
import re

auth_bp = Blueprint('auth', __name__)

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

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 验证必填字段
    required_fields = ['email', 'password', 'name', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({'error': '缺少必填字段'}), 400
    
    # 验证邮箱格式
    email = data['email']
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'error': '邮箱格式不正确'}), 400
    
    # 验证邮箱域名
    valid_domains = current_app.config.get('VALID_EMAIL_DOMAINS', ['edu.cn'])
    email_domain = email.split('@')[-1]
    if not any(email_domain.endswith(domain) for domain in valid_domains):
        return jsonify({'error': '只允许学校邮箱注册'}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已被注册'}), 400
    
    # 检查学号是否已存在（如果提供）
    student_id = data.get('student_id')
    if student_id and User.query.filter_by(student_id=student_id).first():
        return jsonify({'error': '学号已被注册'}), 400
    
    # 创建用户
    role = UserRole.STUDENT if data['role'] == 'student' else UserRole.ADMIN
    user = User(
        email=email,
        name=data['name'],
        student_id=data.get('student_id'),
        phone=data.get('phone'),
        role=role,
        status=UserStatus.PENDING if role == UserRole.ADMIN else UserStatus.ACTIVE
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # 管理员需要审核，学生直接激活
    if role == UserRole.STUDENT:
        # 这里可以添加发送激活邮件的逻辑
        pass
    
    return jsonify({
        'message': '注册成功',
        'user_id': user.id,
        'status': user.status.value
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 验证必填字段
    if not all(k in data for k in ('email', 'password')):
        return jsonify({'error': '请提供邮箱和密码'}), 400
    
    # 查找用户
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': '邮箱或密码错误'}), 401
    
    # 检查用户状态
    if user.status != UserStatus.ACTIVE:
        return jsonify({'error': '账户未激活或已被禁用'}), 403
    
    # 创建JWT令牌 - 修改identity为字符串
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'email': user.email,
            'role': user.role.value
        }
    )
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_user_id_from_jwt()
    if current_user_id is None:
        return jsonify({'error': '无效的JWT令牌格式'}), 401
        
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({'user': user.to_dict(include_reservations=True)}), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = get_user_id_from_jwt()
    if current_user_id is None:
        return jsonify({'error': '无效的JWT令牌格式'}), 401
        
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 验证旧密码
    if not user.check_password(data.get('old_password', '')):
        return jsonify({'error': '旧密码不正确'}), 401
    
    # 设置新密码
    user.set_password(data.get('new_password'))
    db.session.commit()
    
    return jsonify({'message': '密码修改成功'}), 200 