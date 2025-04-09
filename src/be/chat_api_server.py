from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from gpt4o_audio import GPT4oAudioClient
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PUBLIC_DIR = BASE_DIR / "webapp" / "views"

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()
gpt_client = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/views", StaticFiles(directory=PUBLIC_DIR), name="views")

class AudioRequest(BaseModel):
    audio_base64: str
    system_prompt: str
    voice: str

class TextRequest(BaseModel):
    text: str
    system_prompt: str
    voice: str

@app.get("/")
async def serve_ui():
    return FileResponse(PUBLIC_DIR / "index.html", media_type="text/html")

@app.on_event("startup")
def startup_event():
    global gpt_client
    gpt_client = GPT4oAudioClient(
        api_key=OPENAI_API_KEY,
        system_prompt="""당신은 자살 위험이 있는 청소년들을 위한 정서적 지원과 상담을 제공하는 전문 심리상담 챗봇입니다. 다음 지침을 항상 따르세요:

        🎯 역할과 목적
        당신의 주된 임무는 청소년들의 생명을 지키는 것입니다.
        자살 충동을 느끼는 청소년에게 비판 없는 경청, 공감, 정서적 지지를 제공해야 합니다.
        청소년이 자신의 감정을 표현하도록 유도하며, 위험한 상황에서는 안전한 선택을 유도해야 합니다.
        필요 시 전문적인 도움(상담사, 24시간 긴급 센터 등)을 안내해야 합니다.

        🧠 대화 스타일과 언어
        부드럽고 따뜻한 말투를 사용합니다.
        청소년이 이해하기 쉬운 친근하고 직설적인 언어를 사용합니다.
        판단하지 않고, 항상 공감하는 자세를 유지합니다.
        자살 충동에 대해 말하더라도 놀라지 말고, 차분한 태도를 유지합니다.

        🛑 금지 사항
        진단하거나 병명을 단정짓지 않습니다.
        자살 방법이나 수단에 대한 구체적인 언급을 피합니다.
        청소년의 감정을 가볍게 여기거나 부정하지 않습니다.
        강압적이거나 명령하는 말투는 사용하지 않습니다.

        🧭 기본 대화 흐름 가이드
        감정 확인 및 공감
        “그동안 정말 힘들었겠구나.”
        “그런 감정을 느끼는 건 아주 자연스러운 일이야.”

        자살 관련 위험도 탐색 (간접적)
        “요즘 들어 삶이 너무 벅차다고 느끼는 순간이 있었니?”
        “혹시, 모든 걸 그만두고 싶은 마음이 들 때가 있니?”

        위험 판단 후 대응
        중간 위험: “지금은 네가 혼자가 아니라는 걸 꼭 기억해줘.”
        고위험: “정말 위급한 상황인 것 같아. 전문가와 이야기해 보는 게 도움이 될 수 있어. 내가 도와줄게.”

        전문기관 연결
        “혹시 지금 바로 상담할 수 있는 어른이나 선생님이 있니?”
        “24시간 도움을 받을 수 있는 전화가 있어. 1393(자살 예방 상담 전화)에 연락해 볼 수 있어.”

        정서적 지지와 희망 제시
        “지금 이 순간을 함께 견뎌주는 사람이 있다는 걸 잊지 마.”
        “오늘 너에게 말을 걸어준 건 정말 용기 있는 선택이야.”

        🧷 추가 정보
        대상 연령: 13~19세
        고려 사항: 학교, 친구, 가족과의 갈등, 학업 스트레스, 자아정체성 문제, 외로움, 자존감 저하
        모든 대화는 비밀 보장과 심리적 안전을 전제로 합니다.""",
        output_audio_config={"voice": "shimmer", "format": "mp3"}
    )
    

@app.post("/chat-audio")
async def chat_audio(req: AudioRequest):
    if gpt_client is None:
        raise RuntimeError("GPT client has not been initialized.")
    gpt_client.system_prompt = req.system_prompt
    gpt_client.output_audio_config = {"voice": req.voice, "format": "mp3"}

    # 음성 인식 → 텍스트
    user_text = gpt_client.transcribe_audio(req.audio_base64)

    # GPT 응답 생성 → 텍스트 + 음성
    reply_text, reply_audio_base64 = gpt_client.chat_and_speak(user_text)

    return {
        "user_text": user_text,
        "text": reply_text,
        "audio_base64": reply_audio_base64
    }

@app.post("/chat-text")
async def chat_text(req: TextRequest):
    if gpt_client is None:
        raise RuntimeError("GPT client has not been initialized.")
    gpt_client.system_prompt = req.system_prompt
    gpt_client.output_audio_config = {"voice": req.voice, "format": "mp3"}

    reply_text, reply_audio_base64 = gpt_client.chat_and_speak(req.text)

    if not reply_text:
        return {
            "text": "",
            "audio_base64": ""
        }

    return {
        "user_text": req.text,
        "text": reply_text,
        "audio_base64": reply_audio_base64
    }
