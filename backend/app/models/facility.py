from app import db
from datetime import datetime
import enum
import json

class RoomType(enum.Enum):
    QUIET = 'quiet'       # 安静区
    DISCUSSION = 'discussion'  # 讨论区
    GENERAL = 'general'    # 普通区
    POWER = 'power'       # 电源区

class RoomStatus(enum.Enum):
    OPEN = 'open'         # 开放
    CLOSED = 'closed'     # 关闭
    MAINTENANCE = 'maintenance'  # 维护中

class SeatType(enum.Enum):
    NORMAL = 'normal'  # 普通座位
    WINDOW = 'window'  # 靠窗座位
    POWER = 'power'  # 带插座座位
    GROUP = 'group'  # 四人桌

class SeatStatus(enum.Enum):
    AVAILABLE = 'available'  # 可用
    OCCUPIED = 'occupied'  # 已占用/已预约
    MAINTENANCE = 'maintenance'  # 维修中
    DISABLED = 'disabled'  # 禁用

class StudyRoom(db.Model):
    __tablename__ = 'study_rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    building = db.Column(db.String(50), nullable=False)
    room_type = db.Column(db.Enum(RoomType), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum(RoomStatus), nullable=False, default=RoomStatus.OPEN)
    zones_json = db.Column(db.Text, nullable=True)  # 存储区域信息的JSON字符串
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    seats = db.relationship('Seat', back_populates='room', lazy='dynamic')
    
    @property
    def zones(self):
        """获取区域列表"""
        if not self.zones_json:
            return []
        try:
            return json.loads(self.zones_json)
        except:
            return []
    
    @zones.setter
    def zones(self, value):
        """设置区域列表"""
        if isinstance(value, list):
            self.zones_json = json.dumps(value)
        else:
            self.zones_json = None
    
    def to_dict(self, include_seats=False):
        data = {
            'id': self.id,
            'name': self.name,
            'floor': self.floor,
            'building': self.building,
            'room_type': self.room_type.value,
            'capacity': self.capacity,
            'open_time': self.open_time.strftime('%H:%M'),
            'close_time': self.close_time.strftime('%H:%M'),
            'status': self.status.value,
            'zones': self.zones,
            'description': self.description
        }
        
        if include_seats:
            data['seats'] = [seat.to_dict() for seat in self.seats]
            
        return data

class Seat(db.Model):
    __tablename__ = 'seats'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('study_rooms.id'), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    seat_type = db.Column(db.Enum(SeatType), nullable=False, default=SeatType.NORMAL)
    status = db.Column(db.Enum(SeatStatus), nullable=False, default=SeatStatus.AVAILABLE)
    x_position = db.Column(db.Integer, nullable=False)  # 在地图上的X坐标
    y_position = db.Column(db.Integer, nullable=False)  # 在地图上的Y坐标
    qrcode_url = db.Column(db.String(255), nullable=True)  # 座位二维码URL
    maintenance_note = db.Column(db.Text, nullable=True)  # 维修备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    reservations = db.relationship('Reservation', backref='seat', lazy='dynamic')
    maintenance_logs = db.relationship('MaintenanceLog', backref='seat', lazy='dynamic')
    room = db.relationship('StudyRoom', back_populates='seats')
    
    def to_dict(self, include_reservations=False, include_room=False):
        data = {
            'id': self.id,
            'room_id': self.room_id,
            'seat_number': self.seat_number,
            'seat_type': self.seat_type.value,
            'status': self.status.value,
            'x_position': self.x_position,
            'y_position': self.y_position,
            'qrcode_url': self.qrcode_url,
            'maintenance_note': self.maintenance_note
        }
        
        if include_reservations:
            active_reservations = [r.to_dict() for r in self.reservations.filter_by(status='active').all()]
            data['active_reservations'] = active_reservations
            
        if include_room and self.room:
            data['room'] = {
                'id': self.room.id,
                'name': self.room.name,
                'building': self.room.building,
                'floor': self.room.floor,
                'room_type': self.room.room_type.value if self.room.room_type else None
            }
            
        return data

class MaintenanceLog(db.Model):
    __tablename__ = 'maintenance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='in_progress')  # in_progress, completed
    
    # 关系
    admin = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'seat_id': self.seat_id,
            'admin_id': self.admin_id,
            'admin_name': self.admin.name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'reason': self.reason,
            'status': self.status
        } 