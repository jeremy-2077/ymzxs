from app import create_app, db
from app.models.facility import Seat, SeatStatus

def reset_seats():
    """将所有座位状态重置为AVAILABLE"""
    app = create_app()
    with app.app_context():
        seats = Seat.query.all()
        updated = 0
        for seat in seats:
            if seat.status.value != 'available':
                seat.status = SeatStatus.AVAILABLE
                updated += 1
        db.session.commit()
        print(f'已重置 {updated} 个座位状态为可用')

if __name__ == '__main__':
    reset_seats() 