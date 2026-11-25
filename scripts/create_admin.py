
import os

from app.database.connection import SessionLocal
from app.models.user import User
from app.core.security import hash_password


db = SessionLocal()

try:
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    if not email or not password:
        raise ValueError(
            "ADMIN_EMAIL and ADMIN_PASSWORD must be configured in the environment."
        )

    email = email.strip().lower()

    existing_admin = db.query(User).filter(
        User.email == email
    ).first()

    if existing_admin:
        print("Admin already exists.")
    else:
        admin = User(
            email=email,
            password_hash=hash_password(password),
            role="admin"
        )

        db.add(admin)
        db.commit()

        print("Admin created successfully.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
