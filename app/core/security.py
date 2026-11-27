import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

password_hasher = PasswordHasher(
    time_cost=3,  # number of iteations. Higher the iteration more the computation.
    memory_cost=65536,  # Memory used during hash, in KiB.
    parallelism=4,  # number of parallel computational lanes.
    hash_len=32,  # Length of the generated hash, in bytes.
    salt_len=16,  # Length of the random salt, in bytes.
)


# converting the normal password into the hash password....
def hash_password(password: str) -> str:
    # Converting the plain-text password into an Argon2 hash.
    return password_hasher.hash(password)


# Verify the plain password with the hashed one....
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verify the plain-text password against its stored hash.
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# if the parameters gets changed then the user hashed password gets updated next time he log in
def needs_rehash(hashed_password: str) -> bool:
    # Check whether a stored hash needs updated parameters.
    return password_hasher.check_needs_rehash(hashed_password)


# Creating the access token at the time of login
def create_access_token(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY,algorithm=settings.ALGORITHM)
    
