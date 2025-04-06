from app import db
from datetime import datetime
import enum

class ReservationStatus(enum.Enum):
    PENDING = 'pending'  # 待签到
    ACTIVE = 'active'  # 已签到，使用中
    COMPLETED = 'completed'  # 已结束
    CANCELLED = 'cancelled'  # 已取消
    EXPIRED = 'expired'  # 超时未签到

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(ReservationStatus), nullable=False, default=ReservationStatus.PENDING)
    qrcode_url = db.Column(db.String(255), nullable=True)  # 预约二维码URL
    checkin_time = db.Column(db.DateTime, nullable=True)  # 签到时间
    checkout_time = db.Column(db.DateTime, nullable=True)  # 签退时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    checkin = db.relationship('CheckIn', backref='reservation', uselist=False)
    
    def to_dict(self, include_user=False, include_seat=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'seat_id': self.seat_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'status': self.status.value,
            'qrcode_url': self.qrcode_url,
            'checkin_time': self.checkin_time.isoformat() if self.checkin_time else None,
            'checkout_time': self.checkout_time.isoformat() if self.checkout_time else None,
            'created_at': self.created_at.isoformat()
        }
        
        if include_user:
            data['user'] = self.user.to_dict()
        
        if include_seat:
            data['seat'] = self.seat.to_dict(include_room=True)
            
        return data
    
    def is_active(self):
        """检查预约是否处于活跃状态（待签到或已签到）"""
        return self.status in [ReservationStatus.PENDING, ReservationStatus.ACTIVE]
    
    def can_checkin(self):
        """检查预约是否可以签到"""
        now = datetime.utcnow()
        # 预约开始前30分钟内可以签到
        return (self.status == ReservationStatus.PENDING and
                now >= self.start_time.replace(minute=self.start_time.minute - 30) and
                now <= self.end_time)
    
    def can_cancel(self):
        """检查预约是否可以取消"""
        now = datetime.utcnow()
        # 预约开始前30分钟可以取消
        return (self.status == ReservationStatus.PENDING and
                now <= self.start_time.replace(minute=self.start_time.minute - 30))

class CheckIn(db.Model):
    __tablename__ = 'checkins'
    
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), nullable=False, unique=True)
    checkin_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    checkout_time = db.Column(db.DateTime, nullable=True)
    checkin_location = db.Column(db.String(255), nullable=True)  # 签到位置（经纬度）
    checkout_location = db.Column(db.String(255), nullable=True)  # 签退位置
    duration = db.Column(db.Integer, nullable=True)  # 使用时长（分钟）
    
    def to_dict(self):
        return {
            'id': self.id,
            'reservation_id': self.reservation_id,
            'checkin_time': self.checkin_time.isoformat(),
            'checkout_time': self.checkout_time.isoformat() if self.checkout_time else None,
            'checkin_location': self.checkin_location,
            'checkout_location': self.checkout_location,
            'duration': self.duration
        } 