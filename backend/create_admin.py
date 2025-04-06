from app import create_app, db
from app.models.user import User, UserRole, UserStatus

app = create_app()

with app.app_context():
    # 检查是否已存在管理员
    admin = User.query.filter_by(role=UserRole.ADMIN).first()
    if not admin:
        # 创建初始管理员
        admin = User(
            email="admin@example.com",
            name="系统管理员",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            phone="13800138000"
        )
        admin.set_password("admin123456")
        db.session.add(admin)
        db.session.commit()
        print("初始管理员创建成功：")
        print(f"邮箱: {admin.email}")
        print(f"密码: admin123456")
    else:
        print("管理员账号已存在，无需创建") 