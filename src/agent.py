import os
import logging
from dotenv import load_dotenv
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from src.encypt import encrypt_message
from src.decypt import decrypt_message
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaConfig(BaseModel):
    """Configuration for Ollama model."""
    model: str = Field(default="deepseek-r1:1.5b")
    base_url: str = Field(default="http://localhost:11434/v1")
    temperature: float = Field(default=0.7)
    streaming: bool = Field(default=True)
    verbose: bool = Field(default=True)

def test_ollama_connection(base_url: str) -> bool:
    """Test connection to Ollama server."""
    try:
        import requests
        response = requests.get(f"{base_url}/models")
        if response.status_code != 200:
            logger.error(f"Failed to connect to Ollama: {response.status_code}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error testing Ollama connection: {str(e)}")
        return False

def init_ollama_model() -> ChatOpenAI:
    """Initialize ChatOpenAI with configuration for Ollama compatibility."""
    try:
        # Load configuration
        config = OllamaConfig(
            model=os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b"),
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434/v1"),
            temperature=float(os.getenv("TEMPERATURE", "0.7"))
        )
        
        # Test connection first
        if not test_ollama_connection(config.base_url):
            logger.error("Unable to connect to Ollama server")
            raise ConnectionError("Unable to connect to Ollama server")
        
        logger.info(f"Initializing ChatOpenAI for model {config.model}")
        
        # Configure callbacks
        callbacks = [StreamingStdOutCallbackHandler()]
        
        # Initialize ChatOpenAI with Ollama configuration
        chat = ChatOpenAI(
            openai_api_base=config.base_url,
            openai_api_key="sk-no-key-required",
            model_name=config.model,
            temperature=config.temperature,
            streaming=config.streaming,
            verbose=config.verbose,
            callbacks=callbacks
        )
        
        # Test the model
        test_message = HumanMessage(content="Test connection")
        test_response = chat.invoke([test_message])
        logger.info("Successfully tested Ollama model connection")
        
        return chat
        
    except Exception as e:
        logger.error(f"Failed to initialize ChatOpenAI model: {str(e)}")
        raise

def create_ollama_agent(retriever) -> ConversationChain:
    """Create an Ollama-based chat agent with memory.
    
    Args:
        retriever: Vector store retriever for conversation history
        
    Returns:
        ConversationChain: Configured conversation chain with memory
    """
    try:
        # Initialize Ollama model
        llm = init_ollama_model()
        
        # Initialize conversation memory
        memory = ConversationBufferMemory(
            memory_key="history",
            input_key="input",
            return_messages=True
        )
        
        # Create prompt template
        prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""
            System: You are a helpful AI assistant focused on security and privacy.
            
            Current conversation:
            {history}
            Human: {input}
            Assistant:"""
        )
        
        # Create conversation chain
        conversation = ConversationChain(
            llm=llm,
            memory=memory,
            prompt=prompt,
            verbose=True
        )
        
        logger.info("Successfully created Ollama agent with memory")
        return conversation
        
    except Exception as e:
        logger.error(f"Failed to create Ollama agent: {str(e)}")
        raise

def create_chat_prompt():
    """Create the chat prompt template with system message."""
    try:
        system_message = SystemMessage(content="""You are a helpful AI assistant. 
        Your responses should be informative, engaging, and safe.""")
        
        prompt = f"""
        System: {system_message.content}
        
        Current conversation:
        {{history}}
        Human: {{input}}
        Assistant:"""
        
        return prompt
        
    except Exception as e:
        logger.error(f"Failed to create chat prompt: {str(e)}")
        raise

def process_message(agent: ConversationChain, message: str, cipher_suite: Fernet) -> tuple[str, bytes]:
    """Process a message through the agent with encryption."""
    try:
        logger.info("Processing new message")
        
        # Get response from agent first
        response = agent.predict(input=message)
        logger.debug("Received response from agent")
        
        # Encrypt using Fernet
        try:
            encrypted_message = cipher_suite.encrypt(message.encode())
            encrypted_response = cipher_suite.encrypt(response.encode())
            logger.debug("Successfully encrypted messages")
            
            return response, encrypted_response
            
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            # Return response even if encryption fails
            return response, None
            
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return None, None
