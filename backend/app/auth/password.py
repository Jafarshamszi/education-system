"""
Password hashing and verification utilities
"""

import base64
import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt

    Args:
        password: Plaintext password string

    Returns:
        Hashed password string
    """
    # Convert string to bytes
    password_bytes = password.encode('utf-8')
    # Generate salt and hash
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password using bcrypt

    Args:
        plain_password: Plaintext password to verify
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    try:
        # Convert to bytes
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        # Verify using bcrypt
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def decode_base64_password(encoded_password: str) -> str:
    """
    Decode a base64 encoded password (for legacy compatibility)
    
    Args:
        encoded_password: Base64 encoded password
        
    Returns:
        Decoded password string
    """
    try:
        decoded_bytes = base64.b64decode(encoded_password)
        return decoded_bytes.decode('utf-8')
    except Exception:
        # If decoding fails, return as-is
        return encoded_password


def verify_legacy_password(plain_password: str, stored_password: str) -> bool:
    """
    Verify password against legacy base64 encoded password
    
    Args:
        plain_password: Plaintext password to verify
        stored_password: Base64 encoded password from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        decoded_stored = decode_base64_password(stored_password)
        return plain_password == decoded_stored
    except Exception:
        return False