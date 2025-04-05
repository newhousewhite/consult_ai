
from openai import OpenAI

class GPT4oTranscribeClient:
    def __init__(self, api_key, model="gpt-4o-transcribe"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def transcribe(self, audio_file_obj):
        transcription = self.client.audio.transcriptions.create(
            model=self.model,
            file=audio_file_obj,
            response_format="text"
        )
        print(type(transcription))
        print(transcription)
        return transcription

