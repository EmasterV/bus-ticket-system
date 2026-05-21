import hashlib
import secrets

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)