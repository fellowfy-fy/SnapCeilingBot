from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str
    HF_TOKEN: str
    LEADS_CHAT_ID: int | str
    HF_MODEL_ID: str
    LOG_LEVEL: str

def get_settings() -> Settings:
    bot = os.getenv("BOT_TOKEN", "").strip()
    hf = os.getenv("HF_TOKEN", "").strip()
    model = os.getenv("HF_MODEL_ID", "openai/gpt-oss-120b").strip()
    leads_chat = os.getenv("LEADS_CHAT_ID", "").strip()
    if not bot:
        raise RuntimeError("[CONFIG] BOT_TOKEN не задан в .env")
    if not hf:
        raise RuntimeError("[CONFIG] HF_TOKEN не задан в .env")
    return Settings(BOT_TOKEN=bot,
                     HF_TOKEN=hf,
                    LEADS_CHAT_ID=leads_chat,
                       HF_MODEL_ID=model,
                         LOG_LEVEL=os.getenv("LOG_LEVEL","INFO"), )

settings = get_settings()
