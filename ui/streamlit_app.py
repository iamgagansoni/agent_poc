import streamlit as st
import requests
import json
from typing import Dict, Any, List, Optional
from enum import Enum

class AgentType(str, Enum):
    OPENAI = "openai"
    GROQ = "groq"

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Multi-Agent Chat",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("Multi-Agent LLM Chat")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Agent selection
        agent_type = st.selectbox(
            "Select Agent",
            options=[AgentType.OPENAI, AgentType.GROQ],
            format_func=lambda x: x.value.capitalize()
        )
        
        # API URL configuration
        api_url = st.text_input("API URL", value="http://localhost:8000")
        
        # Conversation ID
        st.subheader("Current Conversation")
        st.text(f"ID: {st.session_state.conversation_id or 'New Conversation'}")
        
        # New conversation button
        if st.button("New Conversation"):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.success("Started new conversation")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Display tool results if any
            if "tool_results" in message and message["tool_results"]:
                st.subheader("Tool Results")
                
                for tool_result in message["tool_results"]:
                    tool_name = tool_result.get("tool_name", "Unknown Tool")
                    with st.expander(f"{tool_name} Result"):
                        st.json(tool_result)
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Call API
        with st.spinner("Processing..."):
            try:
                response = requests.post(
                    f"{api_url}/api/chat",
                    json={
                        "message": prompt,
                        "agent_type": agent_type.value,
                        "conversation_id": st.session_state.conversation_id
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Save conversation ID
                    st.session_state.conversation_id = result.get("conversation_id")
                    
                    # Display assistant response
                    with st.chat_message("assistant"):
                        st.write(result.get("response", ""))
                        
                        # Display tool results if any
                        if result.get("tool_results"):
                            st.subheader("Tool Results")
                            
                            for tool_result in result.get("tool_results", []):
                                tool_name = tool_result.get("tool_name", "Unknown Tool")
                                with st.expander(f"{tool_name} Result"):
                                    st.json(tool_result)
                    
                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": result.get("response", ""),
                        "tool_results": result.get("tool_results", [])
                    })
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Error connecting to API: {str(e)}")

if __name__ == "__main__":
    main()
