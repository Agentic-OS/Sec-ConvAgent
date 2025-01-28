class VectorStoreError(Exception):
    """Raised when there's an error with vector store operations."""
    pass

class MemoryError(Exception):
    """Raised when there's an error with memory operations."""
    pass

class AgentError(Exception):
    """Raised when there's an error with agent operations."""
    pass

class EncryptionError(Exception):
    """Raised when there's an error with encryption/decryption."""
    pass 