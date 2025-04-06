from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta
from app import db, socketio
from app.models.reservation import Reservation, ReservationStatus
from app.models.facility import Seat, SeatStatus
from app.models.user import User
from flask import current_app
import logging
import time
import redis
import os

logger = logging.getLogger(__name__)

def init_scheduler(app):
    """初始化定时任务调度器"""
    redis_url = app.config.get('REDIS_URL')
    
    # 由于RedisJobStore存在兼容性问题，使用MemoryJobStore替代
    jobstores = {
        'default': MemoryJobStore()
    }
    
    executors = {
        'default': ThreadPoolExecutor(20)
    }
    
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults
    )
    
    # 添加定时任务
    # 每分钟检查一次过期的预约
    scheduler.add_job(
        check_expired_reservations,
        'interval',
        minutes=1,
        id='check_expired_reservations',
        replace_existing=True,
        args=[app]
    )
    
    # 每天凌晨重置失信次数计数器
    scheduler.add_job(
        reset_failed_checkins,
        'cron',
        hour=0,
        minute=0,
        id='reset_failed_checkins',
        replace_existing=True,
        args=[app]
    )
    
    scheduler.start()
    
    # 将调度器添加到应用上下文
    app.scheduler = scheduler
    
    return scheduler

def check_expired_reservations(app):
    """检查并处理过期的预约"""
    with app.app_context():
        now = datetime.now()
        
        # 查找已过期但未标记为过期的预约
        expired_reservations = Reservation.query.filter(
            Reservation.status == ReservationStatus.PENDING,
            Reservation.end_time < now
        ).all()
        
        for reservation in expired_reservations:
            # 将预约状态更新为过期
            reservation.status = ReservationStatus.EXPIRED
            
            # 释放座位
            seat = Seat.query.get(reservation.seat_id)
            if seat and seat.status == SeatStatus.OCCUPIED:
                seat.status = SeatStatus.AVAILABLE
                
                # 通过WebSocket广播座位状态更新
                socketio.emit('seat_status_changed', {
                    'seat_id': seat.id,
                    'status': seat.status.value
                })
        
        db.session.commit()
        
        logger.info(f"处理了 {len(expired_reservations)} 个过期预约")

def reset_failed_checkins(app):
    """每天凌晨重置用户失信次数"""
    with app.app_context():
        # 将所有用户的失信次数重置为0
        User.query.update({User.failed_checkins: 0})
        db.session.commit()
        
        logger.info("已重置所有用户的失信次数") 