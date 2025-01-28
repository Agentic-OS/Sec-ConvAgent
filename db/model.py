import os
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import VectorStoreRetrieverMemory
from cryptography.fernet import Fernet
from src.encypt import encrypt_message, generate_key
from src.decypt import decrypt_message, is_encrypted
import logging
from langchain.memory import ConversationBufferMemory

logger = logging.getLogger(__name__)

def generate_encryption_key():
    """Generate a new encryption key."""
    return generate_key()

def init_vector_store():
    """Initialize the vector store with embeddings."""
    try:
        vector_db_path = os.getenv("VECTOR_DB_PATH", "./vector_db")
        os.makedirs(vector_db_path, exist_ok=True)
        
        # Fix the API endpoint URL format - remove /v1 suffix
        base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip('/v1')
        
        # Initialize embeddings with correct API endpoint
        embeddings = OllamaEmbeddings(
            base_url=base_url,
            model=os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
        )
        
        # Initialize Chroma with correct settings
        vectorstore = Chroma(
            collection_name="encrypted_chat_history",
            embedding_function=embeddings,
            persist_directory=vector_db_path
        )
        
        logger.info("Vector store initialized with embeddings")
        return vectorstore, embeddings
        
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {str(e)}")
        raise

def init_retriever(vectorstore: Chroma):
    """Initialize the vector store retriever."""
    try:
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
    except Exception as e:
        logger.error(f"Failed to initialize retriever: {str(e)}")
        raise

def init_memory(retriever):
    """Initialize the conversation memory."""
    try:
        memory = ConversationBufferMemory(
            memory_key="history",
            input_key="input",
            return_messages=True
        )
        return memory
        
    except Exception as e:
        logger.error(f"Failed to initialize memory: {str(e)}")
        raise

def store_encrypted_message_to_vector_db(vectorstore, message, encryption_key):
    """Store an encrypted message in the vector database.
    
    Args:
        vectorstore: The vector store instance
        message (str): The message to encrypt and store
        encryption_key (bytes): The encryption key
        embedding: The message embedding vector
    """
    try:
        # Encrypt message if not already encrypted
        if not is_encrypted(message):
            encrypted_message = encrypt_message(message, encryption_key)
        else:
            encrypted_message = message
            
        # Store in vector database
        save_encrypted_message(vectorstore, encrypted_message)
        vectorstore.persist()
        
    except Exception as e:
        raise Exception(f"Failed to store encrypted message: {str(e)}")

def retrieve_decrypted_message_from_vector_db(vectorstore, query_embedding, encryption_key, k=5):
    """Retrieve and decrypt messages from the vector database.
    
    Args:
        vectorstore: The vector store instance
        query_embedding: The query embedding vector
        encryption_key (bytes): The decryption key
        k (int): Number of results to retrieve
        
    Returns:
        list: List of decrypted messages
    """
    try:
        # Search similar vectors
        results = vectorstore.similarity_search(
            query_embedding,
            k=k
        )
        
        # Decrypt results
        decrypted_results = []
        for doc in results:
            try:
                if is_encrypted(doc.page_content):
                    decrypted_text = decrypt_message(doc.page_content, encryption_key)
                else:
                    decrypted_text = doc.page_content
                decrypted_results.append(decrypted_text)
            except Exception as e:
                print(f"Error decrypting message: {e}")
                continue
                
        return decrypted_results
        
    except Exception as e:
        raise Exception(f"Failed to retrieve messages: {str(e)}")

def save_encrypted_message(vectorstore, encrypted_message, embedding):
    """Save an encrypted message to the vector store.
    
    Args:
        vectorstore: The vector store instance
        encrypted_message (bytes): The encrypted message to store
        embedding: The message embedding vector
    """
    try:
        vectorstore.add_texts(
            texts=[encrypted_message.decode() if isinstance(encrypted_message, bytes) else encrypted_message],
        )
        vectorstore.persist()
    except Exception as e:
        raise Exception(f"Failed to save encrypted message: {str(e)}")

def save_message_to_vectorstore(vectorstore: Chroma, embeddings: OllamaEmbeddings, message: str, cipher_suite: Fernet):
    """Save encrypted message to vector store."""
    try:
        # Log original message
        logger.info("\n=== Starting Message Encryption ===")
        logger.info(f"Original Message: '{message}'")
        logger.info(f"Original Length: {len(message)} chars")
        
        # Encrypt message
        encrypted_message = cipher_suite.encrypt(message.encode())
        encrypted_text = encrypted_message.decode()
        
        # Log encrypted result
        logger.info(f"Encrypted Message: '{encrypted_text}'")
        logger.info(f"Encrypted Length: {len(encrypted_text)} chars")
        logger.info(f"Encryption Ratio: {len(encrypted_text)/len(message):.2f}x")
        logger.info("=== Encryption Complete ===\n")
        
        # Generate embeddings
        embedding = embeddings.embed_query(message)
        
        # Save to vector store
        vectorstore.add_texts(
            texts=[encrypted_text],
            embeddings=[embedding]
        )
        vectorstore.persist()
        logger.info("Successfully saved encrypted message to vector store")
        
    except Exception as e:
        logger.error(f"Failed to save message to vector store: {str(e)}")
        raise

def retrieve_messages(vectorstore: Chroma, embeddings: OllamaEmbeddings, query: str, cipher_suite: Fernet, k: int = 5):
    """Retrieve and decrypt relevant messages."""
    try:
        logger.info("\n=== Starting Message Retrieval ===")
        logger.info(f"Search Query: '{query}'")
        
        # Generate query embedding
        query_embedding = embeddings.embed_query(query)
        
        # Search vector store
        results = vectorstore.similarity_search_by_vector(
            embedding=query_embedding,
            k=k
        )
        logger.info(f"Found {len(results)} matching messages")
        
        # Decrypt results
        messages = []
        for i, doc in enumerate(results, 1):
            try:
                encrypted_text = doc.page_content
                logger.info(f"\n--- Decrypting Message {i}/{len(results)} ---")
                logger.info(f"Encrypted Message: '{encrypted_text}'")
                
                decrypted_text = cipher_suite.decrypt(encrypted_text.encode()).decode()
                logger.info(f"Decrypted Message: '{decrypted_text}'")
                logger.info(f"Decryption Length: {len(decrypted_text)} chars")
                
                messages.append(decrypted_text)
                logger.info(f"Successfully decrypted message {i}")
            except Exception as e:
                logger.error(f"Failed to decrypt message {i}: {str(e)}")
                continue
        
        logger.info(f"\nSuccessfully retrieved and decrypted {len(messages)} messages")
        logger.info("=== Retrieval Complete ===\n")
        return messages
        
    except Exception as e:
        logger.error(f"Failed to retrieve messages: {str(e)}")
        raise



