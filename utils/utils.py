from streamlit import secrets
import os
import json
from streamlit import chat_message, text_input, text_area, sidebar
from streamlit import cache_data, cache_resource
import logging
from typing import List, Dict, Optional
from datetime import datetime
import streamlit as st
logger = logging.getLogger(__name__)

@cache_data(ttl=600)
def get_secret(key: str) -> str:
    """Get a secret from Streamlit's secrets manager with caching."""
    return secrets.get(key)

@cache_data(ttl=600)
def get_env(key: str) -> str:
    """Get an environment variable with caching."""
    return os.getenv(key)

class ChatUI:
    """Handles the Streamlit chat interface and message management."""
    
    def __init__(self):
        """Initialize the chat UI components."""
        self.messages = []
        self.input_placeholder = "Type your message here..."
        self.max_messages = 100
        self.message_container = st.container()
        self.setup_chat_container()
    
    def setup_chat_container(self):
        """Setup chat container with custom CSS."""
        st.markdown("""
            <style>
                .stChatMessage {
                    padding: 1rem;
                    border-radius: 0.5rem;
                    margin-bottom: 1rem;
                }
                .stChatMessage[data-role="user"] {
                    background: var(--primary-color-light);
                }
                .stChatMessage[data-role="assistant"] {
                    background: var(--secondary-color-light);
                }
                div[data-testid="stChatInputContainer"] {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: var(--background-color);
                    padding: 1rem;
                    z-index: 999;
                }
            </style>
        """, unsafe_allow_html=True)
    
    def load_chat_history(self) -> List[Dict[str, str]]:
        """Load chat history from session state."""
        try:
            import streamlit as st
            return st.session_state.get('chat_history', [])
        except Exception as e:
            logger.error(f"Error loading chat history: {str(e)}")
            return []
    
    def save_chat_history(self, messages: List[Dict[str, str]]) -> None:
        """Save chat history to session state."""
        try:
            import streamlit as st
            if len(messages) > self.max_messages:
                messages = messages[-self.max_messages:]
            st.session_state['chat_history'] = messages
        except Exception as e:
            logger.error(f"Error saving chat history: {str(e)}")
    
    def display_message(self, message: Dict[str, str]) -> None:
        """Display a single chat message."""
        try:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        except Exception as e:
            logger.error(f"Error displaying message: {str(e)}")
    
    def display_chat_stats(self):
        """Display chat statistics in a clean format."""
        try:
            messages = self.load_chat_history()
            stats = self.get_chat_stats(messages)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Messages", stats["total_messages"])
                st.metric("User Messages", stats["user_messages"])
            with col2:
                st.metric("Assistant Messages", stats["assistant_messages"])
                avg_response = f"{stats['avg_assistant_length']:.0f} chars"
                st.metric("Avg Response Length", avg_response)
                
            if stats["last_message_time"]:
                st.text(f"Last message: {stats['last_message_time']}")
                
        except Exception as e:
            logger.error(f"Error displaying chat stats: {str(e)}")

    def display_chat_history(self) -> None:
        """Display chat history with improved layout."""
        try:
            messages = self.load_chat_history()
            
            # Container for scrollable chat history
            chat_placeholder = st.container()
            
            with chat_placeholder:
                for msg in messages:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])
                        if "timestamp" in msg:
                            st.caption(f"Sent at {msg['timestamp']}")
                            
        except Exception as e:
            logger.error(f"Error displaying chat history: {str(e)}")
    
    def get_user_input(self) -> Optional[str]:
        """Get user input using Streamlit's chat_input."""
        try:
            prompt = st.chat_input(self.input_placeholder)
            return prompt
        except Exception as e:
            logger.error(f"Error getting user input: {str(e)}")
            return None
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the chat history."""
        try:
            messages = self.load_chat_history()
            messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            self.save_chat_history(messages)
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
    
    def clear_chat_history(self) -> None:
        """Clear the chat history."""
        try:
            import streamlit as st
            st.session_state['chat_history'] = []
            self.messages = []
        except Exception as e:
            logger.error(f"Error clearing chat history: {str(e)}")
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_chat_stats(messages: List[Dict[str, str]]) -> Dict[str, any]:
        """Get statistics about the chat history."""
        try:
            total_messages = len(messages)
            user_messages = sum(1 for m in messages if m["role"] == "user")
            assistant_messages = sum(1 for m in messages if m["role"] == "assistant")
            
            user_lengths = [len(m["content"]) for m in messages if m["role"] == "user"]
            assistant_lengths = [len(m["content"]) for m in messages if m["role"] == "assistant"]
            
            return {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "avg_user_length": sum(user_lengths) / len(user_lengths) if user_lengths else 0,
                "avg_assistant_length": sum(assistant_lengths) / len(assistant_lengths) if assistant_lengths else 0,
                "last_message_time": messages[-1].get("timestamp") if messages else None
            }
        except Exception as e:
            logger.error(f"Error getting chat stats: {str(e)}")
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "avg_user_length": 0,
                "avg_assistant_length": 0,
                "last_message_time": None
            }
    
    def export_chat_history(self) -> str:
        """Export chat history as encrypted JSON string."""
        try:
            messages = self.load_chat_history()
            if not messages:
                logger.warning("No messages found in chat history")
                return "[]"
            
            logger.info(f"Exporting {len(messages)} messages from chat history")
            
            # Get cipher suite from session state
            cipher_suite = st.session_state.get('cipher_suite')
            if not cipher_suite:
                logger.error("No encryption key found")
                return "[]"
            
            # Format and encrypt messages for export
            export_data = []
            for msg in messages:
                try:
                    # Encrypt the content
                    content = msg['content']
                    encrypted_content = cipher_suite.encrypt(content.encode()).decode()
                    
                    formatted_msg = {
                        'role': msg['role'],
                        'content': encrypted_content,
                        'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                        'encrypted': True
                    }
                    export_data.append(formatted_msg)
                    logger.info(f"Added encrypted message to export: {msg['role']}")
                except Exception as e:
                    logger.error(f"Error encrypting message for export: {str(e)}")
                    continue
            
            if not export_data:
                logger.warning("No messages were encrypted for export")
                return "[]"
            
            export_json = json.dumps(export_data, indent=2, default=str)
            logger.info(f"Successfully exported {len(export_data)} encrypted messages")
            return export_json
            
        except Exception as e:
            logger.error(f"Error exporting chat history: {str(e)}")
            return "[]"

    def stream_message(self, role: str, content_generator) -> None:
        """Stream a message with typing effect."""
        try:
            with st.chat_message(role):
                message_placeholder = st.empty()
                full_content = ""
                
                # Stream the content
                for content_chunk in content_generator:
                    full_content += content_chunk
                    message_placeholder.write(full_content)
                
                # Save the complete message
                self.add_message(role, full_content)
                
        except Exception as e:
            logger.error(f"Error streaming message: {str(e)}")
            # Fallback to normal display
            self.add_message(role, "".join(content_generator))

    def get_recent_messages(self, limit: int = 5) -> List[Dict[str, str]]:
        """Get the most recent messages from chat history."""
        try:
            messages = self.load_chat_history()
            return messages[-limit:] if messages else []
        except Exception as e:
            logger.error(f"Error getting recent messages: {str(e)}")
            return []

    def format_message_preview(self, message: Dict[str, str], max_length: int = 100) -> str:
        """Format a message for preview display."""
        try:
            content = message.get("content", "")
            if len(content) > max_length:
                return content[:max_length] + "..."
            return content
        except Exception as e:
            logger.error(f"Error formatting message preview: {str(e)}")
            return "Error displaying message"



        
        
