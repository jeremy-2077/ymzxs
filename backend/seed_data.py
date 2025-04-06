from app import create_app, db
from app.models.facility import Seat, StudyRoom, SeatStatus
from app.models.user import User, UserRole

import random

app = create_app()

def create_study_rooms():
    """创建自习室数据"""
    rooms = [
        {
            'id': 1,
            'name': '一号自习室（静音区）',
            'description': '适合安静学习，禁止交谈',
            'location': '图书馆一楼东侧',
            'total_seats': 80,
            'open_time': '08:00',
            'close_time': '22:00',
            'status': 'open'
        },
        {
            'id': 2,
            'name': '二号自习室（讨论区）',
            'description': '可以小声讨论',
            'location': '图书馆一楼西侧',
            'total_seats': 60,
            'open_time': '08:00',
            'close_time': '22:00',
            'status': 'open'
        },
        {
            'id': 3,
            'name': '三号自习室（电源区）',
            'description': '所有座位都配有电源插座',
            'location': '图书馆二楼',
            'total_seats': 40,
            'open_time': '08:00',
            'close_time': '22:00',
            'status': 'open'
        }
    ]
    
    for room_data in rooms:
        # 检查自习室是否已存在
        room = StudyRoom.query.get(room_data['id'])
        if not room:
            room = StudyRoom(
                id=room_data['id'],
                name=room_data['name'],
                description=room_data['description'],
                location=room_data['location'],
                total_seats=room_data['total_seats'],
                open_time=room_data['open_time'],
                close_time=room_data['close_time'],
                status=room_data['status']
            )
            db.session.add(room)
    
    db.session.commit()
    print("自习室数据初始化完成")

def create_seats():
    """创建座位数据"""
    # 清空现有座位数据
    Seat.query.delete()
    db.session.commit()
    
    # 创建座位
    seat_id = 1
    
    # 一号自习室座位
    zones = ['A', 'B', 'C']
    for i in range(1, 81):
        zone = zones[random.randint(0, 2)]
        number = f"{zone}{str(i).zfill(2)}"
        
        seat = Seat(
            id=seat_id,
            room_id=1,
            number=number,
            zone=zone,
            status=SeatStatus.AVAILABLE,
            has_socket=random.random() > 0.5,
            is_window=zone == 'A',
            is_table=random.random() > 0.8
        )
        db.session.add(seat)
        seat_id += 1
    
    # 二号自习室座位
    zones = ['D', 'E', 'F']
    for i in range(1, 61):
        zone = zones[random.randint(0, 2)]
        number = f"{zone}{str(i).zfill(2)}"
        
        seat = Seat(
            id=seat_id,
            room_id=2,
            number=number,
            zone=zone,
            status=SeatStatus.AVAILABLE,
            has_socket=random.random() > 0.5,
            is_window=zone == 'D',
            is_table=random.random() > 0.8
        )
        db.session.add(seat)
        seat_id += 1
    
    # 三号自习室座位
    zones = ['G', 'H']
    for i in range(1, 41):
        zone = zones[random.randint(0, 1)]
        number = f"{zone}{str(i).zfill(2)}"
        
        seat = Seat(
            id=seat_id,
            room_id=3,
            number=number,
            zone=zone,
            status=SeatStatus.AVAILABLE,
            has_socket=True,  # 电源区所有座位都有电源
            is_window=zone == 'G',
            is_table=random.random() > 0.8
        )
        db.session.add(seat)
        seat_id += 1
    
    db.session.commit()
    print(f"座位数据初始化完成，共创建 {seat_id-1} 个座位")

def create_admin_user():
    """创建管理员用户"""
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            name='管理员',
            email='admin@example.com',
            password='admin123',
            role=UserRole.ADMIN
        )
        db.session.add(admin)
        db.session.commit()
        print("管理员用户创建成功")
    else:
        print("管理员用户已存在")

def init_data():
    """初始化所有数据"""
    with app.app_context():
        # 确保所有表已创建
        db.create_all()
        
        create_study_rooms()
        create_seats()
        create_admin_user()
        
        print("所有数据初始化完成")

if __name__ == '__main__':
    init_data() 