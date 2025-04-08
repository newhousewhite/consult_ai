from openai import OpenAI
from dotenv import load_dotenv
import os
import base64
import requests
from typing import List, Dict
import json


class GPT4oAudioClient:
    def __init__(self, api_key, system_prompt, output_audio_config, model="gpt-4o-audio-preview", input_audio_format="wav", max_retry=3):
        """
        Initialize the client with the provided API key.
        """
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = system_prompt
        self.output_audio_config = output_audio_config
        self.model = model
        self.input_audio_format = input_audio_format
        self.chat_history = []
        self.max_retry = max_retry


    def _gen_convo_history_turn(self, user_query: str, ai_response: str):
        return [
            {"role": "user", "content": user_query.strip()},
            {"role": "assistant", "content": ai_response.strip()}
        ]

    def _create_message_with_convo_history(self, user_data, data_type="text", convo_history:List = []) -> List[Dict]:
        """
        :param user_data: current user's query
        :param data_type: "text" or "audio"
        :return: list of dictionary
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        messages += self.chat_history
        if   data_type == "text":
            messages += convo_history + [{"role": "user", "content": user_data}]
        elif data_type == "audio":
            messages += convo_history + [{
                "role": "user",
                "content": "...",
                "type": "input_audio",
                "input_audio": {
                    "data": user_data,
                    "format": self.input_audio_format
                }
            }]

        return messages

    def chat_completion_text_input(self, user_query, f_out_wav=None, convo_history: List = []):
        """
        Calls GPT-4o audio chat with retries if audio is missing.
        On retry, it shortens context and prompts for a briefer response.
        """
        original_messages = self._create_message_with_convo_history(
            user_query, data_type="text", convo_history=convo_history
        )
        print("Messages for chat_completion_text_input:", json.dumps(original_messages, indent=4))

        attempt = 0
        last_message = None

        while attempt < self.max_retry:
            try:
                print(f"🔁 Attempt {attempt + 1} of {self.max_retry}")

                # On first attempt, use full messages; on retry, shorten + simplify
                if attempt == 0:
                    messages = original_messages
                else:
                    # Keep system + last user question only
                    system_msg = original_messages[0]
                    last_user_msg = [msg for msg in reversed(original_messages) if msg["role"] == "user"][0]
                    messages = [
                        system_msg,
                        last_user_msg,
                        {"role": "user", "content": "Please answer briefly (under 10 words), kindly and supportively."}
                    ]

                response = self.client.chat.completions.create(
                    model=self.model,
                    modalities=["text", "audio"],
                    audio=self.output_audio_config,
                    messages=messages,
                )

                if not response or not response.choices:
                    raise ValueError("Invalid response or no choices")

                last_message = response.choices[0].message
                print("GPT response message:", last_message)

                # Check if audio was returned
                if hasattr(last_message, "audio") and last_message.audio and getattr(last_message.audio, "data", None):
                    if f_out_wav:
                        wav_bytes = base64.b64decode(last_message.audio.data)
                        with open(f_out_wav, "wb") as f:
                            f.write(wav_bytes)
                    return last_message.audio

                print("⚠️ No audio in response. Retrying...")
                attempt += 1

            except (AttributeError, ValueError) as e:
                print(f"{type(e).__name__} caught:", e)
                attempt += 1
            except Exception as e:
                print("Unexpected error:", e)
                break

        print("❌ Failed to get audio response after max retries.")
        return dict()


    def chat_completion_audio_input(self, url, f_out_wav=None):
        # Fetch the audio file and convert it to a base64 encoded string
        response = requests.get(url)
        response.raise_for_status()
        wav_data = response.content
        encoded_string = base64.b64encode(wav_data).decode('utf-8')

        response = self.client.chat.completions.create(
            model=self.model,
            modalities=["text", "audio"],
            audio=self.output_audio_config,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.system_prompt
                        },
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": encoded_string,
                                "format": self.input_audio_format
                            }
                        }
                    ]
                },
            ]
        )

        # print text output
        print(response.choices[0].message.audio.transcript)

        # save wav output
        if f_out_wav:
            wav_bytes = base64.b64decode(response.choices[0].message.audio.data)
            with open(f_out_wav, "wb") as f:
                f.write(wav_bytes)

        return response.choices[0].message.audio

    def chat_and_speak(self, user_text: str) -> tuple[str, str]:
        response = self.chat_completion_text_input(user_text)
        transcript = response.transcript if hasattr(response, "transcript") else ""
        audio_data = response.data if hasattr(response, "data") else ""
        return transcript, audio_data

def test_text_input():
    # Define the user text query.
    system_prompt = (
        "You are an experienced counselor specializing in adolescent issues."
        "Provide empathetic advice and thoughtful support in 10 or less words based on the user's text message. "
        "Do not make response longer than 15 words."
    )
    user_text = "I feel overwhelmed with school work and social pressures."
    output_audio_config = {"voice": "alloy", "format": "wav"}
    f_out_wav = "out_wav_text_input.wav"


    load_dotenv()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY is not set in the environment or .env file!")

    client = GPT4oAudioClient(api_key=OPENAI_API_KEY,
                              system_prompt=system_prompt,
                              output_audio_config=output_audio_config)

    # Call the chat_completion method using the client's attribute.
    response_out = client.chat_completion_text_input(user_text, f_out_wav)


def test_audio_input():
    system_prompt = (
        "What is in this recording?  Summarize it in 10 words or less."
    )
    output_audio_config = {"voice": "alloy", "format": "wav"}
    # URL of audio recording file
    url = "https://cdn.openai.com/API/docs/audio/alloy.wav"
    f_out_wav = "out_wav_audio_input.wav"


    load_dotenv()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY is not set in the environment or .env file!")

    client = GPT4oAudioClient(api_key=OPENAI_API_KEY,
                              system_prompt=system_prompt,
                              output_audio_config=output_audio_config)

    # Call the chat_completion method using the client's attribute.
    response_out = client.chat_completion_audio_input(url, f_out_wav)


# Example usage:
if __name__ == '__main__':
    # test_text_input()
    test_audio_input()
