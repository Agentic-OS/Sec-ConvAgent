from cryptography.fernet import Fernet, InvalidToken
from src.encypt import validate_key
import base64

def decrypt_message(encrypted_message, key):
    """Decrypt a message using Fernet symmetric encryption.
    
    Args:
        encrypted_message (bytes): The encrypted message
        key (bytes): The decryption key
        
    Returns:
        str: The decrypted message
        
    Raises:
        ValueError: If the key is invalid
        InvalidToken: If the message cannot be decrypted
        TypeError: If the encrypted_message is not bytes
    """
    try:
        if not isinstance(encrypted_message, bytes):
            raise TypeError("Encrypted message must be bytes")
            
        key = validate_key(key)
        fernet = Fernet(key)
        decrypted_message = fernet.decrypt(encrypted_message).decode()
        return decrypted_message
    except InvalidToken:
        raise InvalidToken("Failed to decrypt message: Invalid token or corrupted data")
    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")

def is_encrypted(message):
    """Check if a message appears to be encrypted.
    
    Args:
        message: The message to check
        
    Returns:
        bool: True if the message appears to be encrypted
    """
    try:
        if not isinstance(message, bytes):
            return False
        base64.b64decode(message)
        return True
    except Exception:
        return False


