import streamlit as st
import os
from dotenv import load_dotenv
from src.agent import create_ollama_agent, create_chat_prompt, process_message
from db.model import init_vector_store, init_retriever, init_memory, generate_encryption_key, save_message_to_vectorstore
from utils.utils import ChatUI, get_env
from src.exceptions import EncryptionError
import logging.config
from datetime import datetime
from langchain.memory import ConversationBufferMemory
import time
from typing import Iterator
from cryptography.fernet import Fernet

# Configure logging
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'mode': 'a',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def initialize_session_state():
    """Initialize session state variables."""
    try:
        if 'chat_ui' not in st.session_state:
            st.session_state.chat_ui = ChatUI()
        if 'cipher_suite' not in st.session_state:
            # Generate and store Fernet cipher suite
            key = Fernet.generate_key()
            st.session_state.cipher_suite = Fernet(key)
        if 'start_time' not in st.session_state:
            st.session_state.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if 'total_tokens' not in st.session_state:
            st.session_state.total_tokens = 0
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        raise

def display_sidebar_info():
    """Display information and controls in the sidebar."""
    with st.sidebar:
        # Chat messages container
        messages_container = st.container(height=300)
        
        # Model information
        st.subheader("🤖 Model Information")
        st.write(f"Model: {get_env('OLLAMA_MODEL')}")
        st.write(f"Temperature: {get_env('TEMPERATURE')}")
        
        # Chat statistics
        st.subheader("📊 Chat Statistics")
        messages = st.session_state.chat_ui.load_chat_history()
        stats = ChatUI.get_chat_stats(messages)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Messages", stats["total_messages"])
            st.metric("User Messages", stats["user_messages"])
        with col2:
            st.metric("Assistant Messages", stats["assistant_messages"])
            avg_response = f"{stats['avg_assistant_length']:.0f} chars"
            st.metric("Avg Response Length", avg_response)
        
        # Controls
        st.subheader("🎮 Controls")
        if st.button("Clear History"):
            st.session_state.chat_ui.clear_chat_history()
            st.experimental_rerun()
        if st.button("Export Chat"):
            export_chat_history()

def initialize_chat_components():
    """Initialize all chat components."""
    try:
        # Initialize vector store and get embeddings
        vectorstore, embeddings = init_vector_store()
        logger.info("Vector store initialized successfully")
        
        # Initialize retriever - pass only vectorstore from tuple
        retriever = init_retriever(vectorstore)
        logger.info("Retriever initialized successfully")
        
        # Store in session state
        st.session_state['vectorstore'] = vectorstore
        st.session_state['embeddings'] = embeddings
        
        # Create agent with retriever
        agent = create_ollama_agent(retriever)
        logger.info("Chat agent created successfully")
        
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize chat components: {str(e)}")
        raise

def process_streamed_response(agent_response: str) -> str:
    """Process the agent response for streaming."""
    try:
        words = agent_response.split()
        response_text = ""
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            response_text += chunk
            yield chunk
            time.sleep(0.05)
            
        # Save assistant response to chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response_text.strip(),
            'timestamp': datetime.now().isoformat(),
            'encrypted': True
        })
        
    except Exception as e:
        logger.error(f"Error processing streamed response: {str(e)}")
        yield agent_response  # Fallback to returning full response

def save_to_vectorstore(message: str, cipher_suite: Fernet):
    """Save message to vector store with proper error handling."""
    try:
        # Save to vector store
        save_message_to_vectorstore(
            st.session_state.get('vectorstore'),
            st.session_state.get('embeddings'),
            message,
            cipher_suite
        )
        logger.debug("Message saved to vector store successfully")
        
        # Ensure message is added to chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            
        # Add message with timestamp
        st.session_state.chat_history.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat(),
            'encrypted': True
        })
        
    except Exception as e:
        logger.error(f"Failed to save message to vector store: {str(e)}")
        raise

def main():
    """Main application function."""
    try:
        # Page configuration must be the first Streamlit command
        st.set_page_config(
            page_title="🔒 Secure Chat",
            page_icon="🔒",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize components
        initialize_session_state()
        agent = initialize_chat_components()
        
        # Sidebar
        with st.sidebar:
            st.title("Settings & Info")
            
            # Model info
            with st.expander("🤖 Model Information", expanded=True):
                st.write(f"Model: {get_env('OLLAMA_MODEL')}")
                st.write(f"Temperature: {get_env('TEMPERATURE')}")
                st.metric("Total Tokens", st.session_state.total_tokens)
            
            # Chat stats and history
            with st.expander("📊 Chat Overview", expanded=True):
                display_chat_stats()
            
            # Recent conversations
            with st.expander("💬 Recent Conversations", expanded=True):
                messages = st.session_state.chat_ui.load_chat_history()
                if messages:
                    for msg in messages[-5:]:  # Show last 5 messages
                        with st.container():
                            st.markdown(f"**{msg['role'].title()}** - {msg.get('timestamp', '')}")
                            st.text(msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"])
                            st.divider()
                else:
                    st.info("No conversation history yet")
            
            # Controls
            with st.expander("🎮 Controls", expanded=True):
                if st.button("Clear History", use_container_width=True):
                    st.session_state.chat_ui.clear_chat_history()
                    st.session_state.total_tokens = 0
                    st.experimental_rerun()
                if st.button("Export Chat", use_container_width=True):
                    export_chat_history()
        
        # Main chat area
        st.title("🔒 Secure Local Chatbot")
        st.caption("Your conversations are encrypted and stored securely.")
        
        # Chat container with messages
        chat_container = st.container()
        with chat_container:
            st.session_state.chat_ui.display_chat_history()
        
        # Input area at bottom
        with st.container():
            if user_input := st.chat_input("Type your message here..."):
                process_user_input(user_input, agent)
                
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An error occurred. Please try again.")
        if st.checkbox("Show error details"):
            st.exception(e)

def process_user_input(user_input: str, agent):
    """Process user input and generate response."""
    try:
        # Add user message first
        st.session_state.chat_ui.add_message("user", user_input)
        
        # Process message and get response
        with st.spinner("Assistant is thinking..."):
            response, encrypted_response = process_message(
                agent,
                user_input,
                st.session_state.cipher_suite
            )
        
        if response:
            # Stream the assistant's response
            st.session_state.chat_ui.stream_message(
                "assistant",
                process_streamed_response(response)
            )
            
            # Only try to save to vector store if encryption was successful
            if encrypted_response:
                try:
                    save_to_vectorstore(response, st.session_state.cipher_suite)
                except Exception as e:
                    logger.error(f"Failed to save to vector store: {str(e)}")
            
            # Rerun to update UI
            st.rerun()  # Updated from experimental_rerun
            
    except Exception as e:
        logger.error(f"Error processing user input: {str(e)}")
        st.error("Failed to process your message. Please try again.")
        if st.checkbox("Show error details"):
            st.exception(e)

def export_chat_history():
    """Export chat history as downloadable encrypted JSON."""
    try:
        chat_json = st.session_state.chat_ui.export_chat_history()
        if chat_json == "[]":
            st.warning("No messages to export")
            return
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"encrypted_chat_history_{timestamp}.json"
        
        st.download_button(
            "Download Encrypted Chat History",
            chat_json,
            file_name=filename,
            mime="application/json",
            help="Download your chat history in encrypted format"
        )
        
        st.info("Your chat history has been encrypted for secure export")
        
    except Exception as e:
        logger.error(f"Failed to export chat history: {str(e)}")
        st.error("Failed to export chat history")

def display_chat_stats():
    """Display chat statistics in the sidebar."""
    try:
        # Get chat history and stats
        messages = st.session_state.chat_ui.load_chat_history()
        stats = ChatUI.get_chat_stats(messages)
        
        # Display metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Messages", stats["total_messages"])
            st.metric("User Messages", stats["user_messages"])
        with col2:
            st.metric("Assistant Messages", stats["assistant_messages"])
            avg_response = f"{stats['avg_assistant_length']:.0f} chars"
            st.metric("Avg Response Length", avg_response)
        
        # Display recent conversation history in a table instead of nested expanders
        if messages:
            st.markdown("### Recent Conversations")
            for msg in messages[-5:]:  # Show last 5 messages
                st.markdown(f"**{msg['role'].title()}** - {msg.get('timestamp', 'No time')}")
                st.text(msg["content"])
                st.divider()
                    
    except Exception as e:
        logger.error(f"Error displaying chat stats: {str(e)}")
        st.error("Failed to display chat statistics")

if __name__ == "__main__":
    main()

