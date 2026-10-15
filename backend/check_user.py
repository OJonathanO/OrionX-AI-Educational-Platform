from app.database import SessionLocal
from app.models import User
from app.core.security import verify_password

db = SessionLocal()
user = db.query(User).filter(User.email == 'masteradmin@orionx.com').first()
if user:
    print(f'User found: {user.email}, role={user.role}, active={user.is_active}')
    pw_ok = verify_password("lukemiranda2003", user.hashed_password)
    print(f'Password check: {pw_ok}')
else:
    print('User not found in database')
    users = db.query(User).all()
    print(f'Total users: {len(users)}')
    for u in users:
        print(f'  - {u.email} ({u.role})')
db.close()
