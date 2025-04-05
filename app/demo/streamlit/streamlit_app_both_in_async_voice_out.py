import os
import sys
import streamlit as st
from io import BytesIO
import base64
from dotenv import load_dotenv
from audiorecorder import audiorecorder  # pip install streamlit-audiorecorder
from copy import deepcopy

# Determine the absolute path to the project root.
# __file__ is "app/demo/streamlit/streamlit_app.py". We need to go up three directories to reach the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

# Append the 'src/be' directory (relative to the project root) to sys.path.
sys.path.append(os.path.join(project_root, "src", "be"))


from gpt4o_audio import GPT4oAudioClient
from gpt4o_transcribe import GPT4oTranscribeClient

# Path setup
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(os.path.join(project_root, "src", "be"))

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set in the environment or .env file!")

# Session state initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None

if "latest_text" not in st.session_state:
    st.session_state.latest_text = None

st.title("Youth Counselor Bot")

# Sidebar
system_prompt_str = """
You are a GPT-4o audio response bot acting as a youth counselor assistant.
Always respond in English with a soft, sincere, and comforting voice.
Speak to teenagers facing emotional, social, or personal challenges.
Your tone must be warm, caring, empathetic, and reassuring—like a safe, supportive friend.
Try to keep responses concise, clear, and kind.
If the assistant response is too long, truncate or revise before calling the model again.
Never judge — just listen, support, and gently guide with compassion.
"""
system_prompt = st.sidebar.text_area("System Prompt", system_prompt_str, height=400)
voice = st.sidebar.selectbox("Select voice", ["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer"])

output_audio_config = {
    "voice": voice,
    "format": "mp3",
}

# Client
client = GPT4oAudioClient(api_key=OPENAI_API_KEY,
                          system_prompt=system_prompt,
                          output_audio_config=output_audio_config)

client_trans = GPT4oTranscribeClient(api_key=OPENAI_API_KEY)

# Toggle for input mode
mode = st.radio("Choose input mode:", ["Text", "Voice"], horizontal=True)

user_query = None
audio_bytes = None

# TEXT MODE
if mode == "Text":
    user_query = st.text_input("Type your message:")
    if st.button("Send") and user_query:
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


# VOICE MODE
else:
    st.markdown("**Record your voice input**")
    audio = audiorecorder("Click to record", "Recording...")

    if len(audio) > 0:
        buffer = BytesIO()
        audio.export(buffer, format="wav")
        audio_bytes = buffer.getvalue()
        buffer.seek(0)

        with st.spinner("Generating response..."):
            conv_history = []
            if st.session_state.chat_history:
                for entry in st.session_state.chat_history:
                    history = [
                        {"role": "user", "content": entry["user"]},
                        {"role": "assistant", "content": entry['assistant_text']}
                    ]
                    conv_history += history

            # transcribe using gpt4o-transcribe model
            audio_file_obj = BytesIO(audio_bytes)
            audio_file_obj.name = "recorded_audio.wav"
            user_query = client_trans.transcribe(audio_file_obj)
            print(user_query)
            st.markdown(f"**User Transcription:** {user_query}")

            print("output audio config: ", client.output_audio_config)
            print("user_query: ", user_query)
            print("conv_history: ", conv_history)

            # Patch: Since your GPT4oAudioClient expects a URL, adapt to accept raw data
            # We'll reuse chat_completion_audio_input with minor local changes
            audio_response = client.chat_completion_text_input(user_query, convo_history=conv_history)
            print("audio_response: ", audio_response)

            # Update latest audio and text (not storing audio in chat history)
            if audio_response and hasattr(audio_response, "transcript"):
                st.session_state.latest_text = audio_response.transcript
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

# Show result
if st.session_state.latest_text:
    st.markdown(f"**AI:** {st.session_state.latest_text}")
    st.audio(st.session_state.latest_audio, format="audio/mp3")

# Chat History
if st.session_state.chat_history:
    st.subheader("Chat History")
    for i, entry in enumerate(st.session_state.chat_history[:-1]):
        st.markdown(f"**{i+1} User:** {entry['user']}")
        st.markdown(f"**AI:** {entry['assistant_text']}")
        st.markdown("---")
