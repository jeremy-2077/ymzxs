from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

class UserRole(enum.Enum):
    STUDENT = 'student'
    ADMIN = 'admin'

class UserStatus(enum.Enum):
    ACTIVE = 'active'
    DISABLED = 'disabled'
    PENDING = 'pending'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    student_id = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    status = db.Column(db.Enum(UserStatus), nullable=False, default=UserStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    failed_checkins = db.Column(db.Integer, default=0)  # 失信次数
    last_penalty_at = db.Column(db.DateTime, nullable=True)  # 上次处罚时间
    
    # 关系
    reservations = db.relationship('Reservation', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_reservations=False):
        data = {
            'id': self.id,
            'email': self.email,
            'student_id': self.student_id,
            'name': self.name,
            'phone': self.phone,
            'role': self.role.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'failed_checkins': self.failed_checkins
        }
        
        if include_reservations:
            data['reservations'] = [r.to_dict() for r in self.reservations]
            
        return data
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
        
    def is_active(self):
        return self.status == UserStatus.ACTIVE
    
    def can_make_reservation(self):
        """检查用户是否可以预约（未被禁用且没有达到失信处罚限制）"""
        return (self.status == UserStatus.ACTIVE and 
                (self.failed_checkins < 3 or 
                 (self.last_penalty_at and 
                  (datetime.utcnow() - self.last_penalty_at).total_seconds() > 24 * 3600))) 