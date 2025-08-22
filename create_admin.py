from app.models.user import User
from app.utils.security import hash_password
from app.database import SessionLocal

db = SessionLocal()
admin = User(
    username="admin",
    email="admin@example.com",
    hashed_password=hash_password("password123"),
    role="admin"
)
db.add(admin)
db.commit()
db.close()
print("[INFO] Admin created!")
