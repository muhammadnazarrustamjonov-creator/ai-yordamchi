import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Steve AI Serveri")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
SYSTEM_INSTRUCTION = "You are Steve, a helpful AI assistant. Always introduce yourself as Steve."


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {"status": "Steve AI Serveri is active!", "assistant": "Steve"}


@app.post("/chat")
def chat_with_ai(request: ChatRequest):
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found!")

    try:
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=request.message,
                config={"system_instruction": SYSTEM_INSTRUCTION},
            )
        except Exception as primary_error:
            message = str(primary_error).lower()
            if "not found" not in message and "404" not in message:
                raise
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=request.message,
                config={"system_instruction": SYSTEM_INSTRUCTION},
            )
        return {"response": response.text}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc