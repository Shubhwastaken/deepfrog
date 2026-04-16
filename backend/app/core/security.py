from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings
import logging
import base64

# Set up centralized logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("customs_brain")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class EmailEncryptor:
    def __init__(self, key: str = settings.ENCRYPTION_KEY):
        # We don't use the key for base64 but keep the signature same
        pass

    def encrypt(self, data: str) -> str:
        if not data: return data
        return base64.b64encode(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        if not encrypted_data: return encrypted_data
        try:
            return base64.b64decode(encrypted_data.encode()).decode()
        except:
            return encrypted_data

encryptor = EmailEncryptor()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_email_hash(email: str):
    import hashlib
    # We use a salt (SECRET_KEY) to make it a keyed hash (HMAC-like)
    return hashlib.sha256((email + settings.SECRET_KEY).encode()).hexdigest()

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
