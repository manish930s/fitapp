import secrets
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
import os

def generate_verification_token(email: str) -> str:
    """Generate a secure, time-limited verification token."""
    secret_key = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(email, salt='email-verification-salt')

def verify_token(token: str, max_age: int = 86400) -> str | None:
    """Verify token validity and extract email address. Default max_age is 24 hours (86400 seconds)."""
    secret_key = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        email = serializer.loads(
            token,
            salt='email-verification-salt',
            max_age=max_age
        )
        return email
    except Exception as e:
        print(f"Token verification failed: {str(e)}")
        return None

def get_token_expiry_time() -> datetime:
    """Get the expiry time for a new verification token (24 hours from now)."""
    return datetime.utcnow() + timedelta(hours=24)
