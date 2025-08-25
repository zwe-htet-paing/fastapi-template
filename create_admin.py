from app.models.user import User
from app.utils.security import hash_password
from app.database import SessionLocal
import getpass

# Prompt for admin credentials
username = input("Enter admin username: ")
email = input("Enter admin email: ")
password = getpass.getpass("Enter admin password: ")

# Create DB session
db = SessionLocal()

# Check if user already exists
existing_user = db.query(User).filter(User.username == username).first()
if existing_user:
    print(f"[INFO] User '{username}' already exists!")
else:
    admin = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role="admin"
    )
    db.add(admin)
    db.commit()
    print(f"[INFO] Admin '{username}' created successfully!")

db.close()
