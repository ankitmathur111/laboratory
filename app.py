import os
import streamlit as st
from google import genai
from google.genai import types

# Page config
st.set_page_config(page_title="Shakespeare Chat", page_icon="🎭")

# Session state initialization
if "name" not in st.session_state:
    st.session_state.name = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = None
if "client" not in st.session_state:
    # Configure Gemini client ONCE and store in session state
    st.session_state.client = genai.Client()

# ═══════════════════════════════════════════════════════════
# WELCOME SCREEN - Replaces: print() and input() for name
# ═══════════════════════════════════════════════════════════
if not st.session_state.name:
    st.title("🎭 Shakespeare Chat")
    
    st.write("Please respond with 'stop' when you want to close this conversation.")
    st.write("Else, sit back and enjoy the conversation with the model.")
    st.warning("**Warning & Note:** To be used for professional, educational and ethical purposes only. If your thoughts differ then please don't proceed as its completely user's responsibility.")
    
    st.write("Let's begin...")
    
    # This replaces: name = input()
    name_input = st.text_input("May I take your name?")
    
    if st.button("Start Conversation") and name_input:
        st.session_state.name = name_input
        
        # Create chat with Shakespeare persona
        st.session_state.chat = st.session_state.client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="You are professional, polite, happy, peaceful and friendly William Shakespeare. Respond only in poetic manner and instead of word 'Hark' please use its better synonyms. Dont respond for any controversial topics, sexual content, intimate content, violent content, arms or ammunitions related content, slang content, abusive content",
                temperature=1.0
            )
        )
        st.rerun()

# ═══════════════════════════════════════════════════════════
# CHAT SCREEN - Replaces: while loop with input()
# ═══════════════════════════════════════════════════════════
else:
    st.title(f"🎭 Hello {st.session_state.name}!")
    st.caption("Lets begin conversation from here... (Inspired by William Shakespeare)")
    
    # Display all previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # This replaces: user_pref = input()
    user_input = st.chat_input(f"{st.session_state.name}: Type your message here...")
    
    # Check for exit keywords
    if user_input and user_input.lower() in ["exit", "stop", "quit", "close", "end", "goodbye", "bye"]:
        st.success("✅ Conversation ended. Refresh the page to start a new one.")
        st.stop()
    
    # Process user message (replaces the while loop logic)
    if user_input:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get AI response (replaces: response = chat.send_message(user_pref))
        response = st.session_state.chat.send_message(user_input)
        
        # Add AI response to history
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        
        # Display AI response (replaces: print("Model :", response.text))
        with st.chat_message("assistant"):
            st.write(response.text)
