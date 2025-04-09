import streamlit as st
from dotenv import load_dotenv
import os
from io import BytesIO
from audiorecorder import audiorecorder  # pip install streamlit-audiorecorder
from openai import OpenAI


# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is not set in the environment or .env file!")


st.title("Audio Recorder and Transcription App")
st.write("Click the button below to record audio from your microphone.")

# Record audio from the microphone

audio = audiorecorder("Click to record", "Recording...")

audio_bytes = b""
if len(audio) > 0:
    buffer = BytesIO()
    audio.export(buffer, format="wav")
    audio_bytes = buffer.getvalue()
    buffer.seek(0)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")

    if st.button("Transcribe"):
        # Call the OpenAI transcription endpoint with the custom model
        client_trans = OpenAI(api_key=OPENAI_API_KEY)

        # # Option 1: saving to a wav file, and load it
        # # Save the recorded audio temporarily
        # audio_filename = "recorded_audio.wav"
        # with open(audio_filename, "wb") as f:
        #     f.write(audio_bytes)

        # with open(audio_filename, "rb") as audio_file:
        #     transcription = client_trans.audio.transcriptions.create(
        #         model="gpt-4o-transcribe",
        #         file=audio_file,
        #         response_format="text"
        #     )
        #     print(transcription)


        # Option 2: without saving to a wav file
        audio_file_obj = BytesIO(audio_bytes)
        audio_file_obj.name = "recorded_audio.wav"
        transcription = client_trans.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio_file_obj,
            response_format="text"
        )
        print(transcription)



        st.subheader("Transcription:")
        st.write(transcription)
