from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
import base64

def validate_key(key):
    """Validate the encryption key format."""
    try:
        if isinstance(key, str):
            key = key.encode()
        # Ensure key is valid base64
        base64.b64decode(key)
        return key
    except Exception:
        raise ValueError("Invalid encryption key format")

def encrypt_message(message, key):
    """Encrypt a message using Fernet symmetric encryption.
    
    Args:
        message (str): The message to encrypt
        key (bytes): The encryption key
        
    Returns:
        bytes: The encrypted message
        
    Raises:
        ValueError: If the key is invalid
        TypeError: If the message is not a string
    """
    try:
        if not isinstance(message, str):
            raise TypeError("Message must be a string")
            
        key = validate_key(key)
        fernet = Fernet(key)
        encrypted_message = fernet.encrypt(message.encode())
        return encrypted_message
    except Exception as e:
        raise Exception(f"Encryption failed: {str(e)}")

def generate_key():
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key()