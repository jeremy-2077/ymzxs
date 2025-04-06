from app import create_app, db
from app.models.reservation import Reservation

def check_reservations():
    """检查最近的10条预约记录"""
    app = create_app()
    with app.app_context():
        reservations = Reservation.query.order_by(Reservation.id.desc()).limit(10).all()
        
        if not reservations:
            print("没有找到任何预约记录")
            return
            
        print(f"找到 {len(reservations)} 条预约记录:")
        for r in reservations:
            r_dict = r.to_dict(include_seat=True)
            print(f"ID: {r_dict['id']}")
            print(f"  用户ID: {r_dict['user_id']}")
            print(f"  座位ID: {r_dict['seat_id']}")
            print(f"  开始时间: {r_dict['start_time']}")
            print(f"  结束时间: {r_dict['end_time']}")
            print(f"  状态: {r_dict['status']}")
            print(f"  创建时间: {r_dict['created_at']}")
            if 'seat' in r_dict and r_dict['seat']:
                print(f"  座位编号: {r_dict['seat'].get('seat_number', '未知')}")
            print("------")

if __name__ == '__main__':
    check_reservations() 