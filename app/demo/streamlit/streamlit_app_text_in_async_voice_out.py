import os
import sys

# Determine the absolute path to the project root.
# __file__ is "app/demo/streamlit/streamlit_app.py". We need to go up three directories to reach the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

# Append the 'src/be' directory (relative to the project root) to sys.path.
sys.path.append(os.path.join(project_root, "src", "be"))

import streamlit as st
from io import BytesIO
import base64
from openai import OpenAI
from gpt4o_audio import GPT4oAudioClient  # Or paste the class directly above
from dotenv import load_dotenv
from copy import deepcopy

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None

if "latest_text" not in st.session_state:
    st.session_state.latest_text = None

# Streamlit UI
st.title("Youth Counselor Bot")

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set in the environment or .env file!")

# Sidebar inputs
system_prompt_str = """
You are a GPT-4o audio response bot acting as a youth counselor assistant.
Always respond in English with a soft, sincere, and comforting voice.
Speak to teenagers facing emotional, social, or personal challenges.
Your tone must be warm, caring, empathetic, and reassuring—like a safe, supportive friend.
Try to keep responses concise, clear, and kind.
If the assistant response is too long, truncate or revise before calling the model again.
Never judge — just listen, support, and gently guide with compassion.
"""
system_prompt = st.sidebar.text_area("System Prompt",
                                     system_prompt_str,
                                     height=400  # approx. 20+ lines depending on font size and line spacing
                                     )
voice = st.sidebar.selectbox("Select voice", ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer"])

# Input from user
user_query = st.text_input("Type your message:")

# Set audio output config
output_audio_config = {
    "voice": voice,
    "format": "mp3",
}

# Send button
if st.button("Send") and OPENAI_API_KEY and user_query:
    client = GPT4oAudioClient(api_key=OPENAI_API_KEY, system_prompt=system_prompt, output_audio_config=output_audio_config)

    # Generate response
    with st.spinner("Generating response..."):
        conv_history = []
        if st.session_state.chat_history:
            for entry in st.session_state.chat_history:
                history = [
                    {"role": "user", "content": entry["user"]},
                    {"role": "assistant", "content": entry['assistant_text']}
                ]
                conv_history += history

        print("output audio config: ", client.output_audio_config)
        print("user_query: ", user_query)
        print("conv_history: ", conv_history)
        audio_response = client.chat_completion_text_input(user_query, convo_history=conv_history)
        print("audio_response: ", audio_response)

    # Update latest audio and text (not storing audio in chat history)
    if audio_response and hasattr(audio_response, "transcript"):
        st.session_state.latest_text = audio_response.transcript
        st.session_state.latest_audio = base64.b64decode(audio_response.data)
    else:
        st.warning("No audio transcript returned.")
        st.session_state.latest_text = ""

    # Append to chat history (only text)
    st.session_state.chat_history.append({
        "user": user_query,
        "assistant_text": deepcopy(st.session_state.latest_text),
    })

    if audio_response and getattr(audio_response, "data", None):
        st.session_state.latest_audio = base64.b64decode(audio_response.data)
    else:
        st.warning("No audio data returned.")
        st.session_state.latest_audio = b""  # empty bytes for no audio


if st.session_state.latest_text:
    st.markdown(f"**AI:** {st.session_state.latest_text}")
    st.audio(st.session_state.latest_audio, format="audio/mp3")

# Display chat history (excluding latest audio)
if st.session_state.chat_history:
    st.subheader("Chat History")
    for i, entry in enumerate(st.session_state.chat_history[:-1]):
        st.markdown(f"**{i+1} User:** {entry['user']}")
        st.markdown(f"**AI:** {entry['assistant_text']}")
        st.markdown("---")
