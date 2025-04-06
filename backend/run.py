from app import create_app, db, socketio
from app.utils.scheduler import init_scheduler
import os

app = create_app()

# 初始化数据库模型
with app.app_context():
    from app.models.user import User
    from app.models.facility import Seat, StudyRoom, MaintenanceLog
    from app.models.reservation import Reservation, CheckIn

# 初始化定时任务
init_scheduler(app)

if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 启动应用（使用socketio运行）
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    
    socketio.run(app, host=host, port=port, debug=True, allow_unsafe_werkzeug=True) 