import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import google.genai as genai
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Steve Assistant", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

api_key = os.getenv("GEMINI_API_KEY")

MANIFEST_PATH = Path(__file__).with_name("manifest.json")

class ChatRequest(BaseModel):
    message: str

HTML_PAGE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steve</title>
    <style>
        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #0f172a;
            color: #f8fafc;
            font-family: Arial, sans-serif;
        }
        .card {
            background: #1e293b;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            width: 90%;
            max-width: 550px;
            text-align: center;
            border: 1px solid #334155;
        }
        h1 { margin-bottom: 5px; color: #38bdf8; }
        .sub { color: #94a3b8; font-size: 13px; margin-bottom: 20px; }
        #status { 
            color: #38bdf8; 
            margin-bottom: 15px; 
            font-weight: bold; 
            font-size: 15px;
            padding: 10px;
            background: #0f172a;
            border-radius: 8px;
            border: 1px solid #334155;
        }
        #chat-box {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 15px;
            min-height: 140px;
            text-align: left;
            margin-bottom: 15px;
            overflow-y: auto;
            max-height: 250px;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.5;
        }
        button {
            background: #0284c7;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        button:hover { background: #0369a1; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Steve</h1>
        <div class="sub">Ovozli yordamchi</div>
        <div id="status">Tizimga xush kelibsiz. Tugmani bosing va gapiring...</div>
        <div id="chat-box">Suhbat tarixi shu yerda chiqadi...</div>
        <button onclick="startVoice()">Steve'ni faollashtirish 🎤</button>
    </div>

    <script>
        const statusEl = document.getElementById('status');
        const chatBox = document.getElementById('chat-box');

        function speakText(text) {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'uz-UZ';
                window.speechSynthesis.speak(utterance);
            }
        }

        function startVoice() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Brauzeringiz ovozni tanishni qo'llab-quvvatlamaydi.");
                return;
            }

            const recognition = new SpeechRecognition();
            recognition.lang = 'uz-UZ';
            recognition.interimResults = false;
            recognition.continuous = false;

            recognition.onstart = function() {
                statusEl.innerText = "🎤 Eshitayapman, marhamat gapiring...";
            };

            recognition.onresult = async function(event) {
                const userSpeech = event.results[0][0].transcript;
                chatBox.innerHTML = "<b>Siz:</b> " + userSpeech;
                statusEl.innerText = "⏳ O'ylayapman...";

                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: userSpeech })
                    });
                    const data = await res.json();
                    const reply = data.response || "Javob topilmadi.";
                    
                    chatBox.innerHTML += "<br><br><b>Steve:</b> " + reply;
                    statusEl.innerText = "🔊 Javob berilmoqda...";
                    
                    speakText(reply);

                    setTimeout(() => {
                        startVoice();
                    }, 4000);

                } catch (err) {
                    statusEl.innerText = "❌ Xatolik yuz berdi.";
                }
            };

            recognition.onerror = function(event) {
                statusEl.innerText = "Mikrofon xatosi. Qayta urinilmoqda...";
                setTimeout(() => {
                    startVoice();
                }, 2000);
            };

            recognition.start();
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=HTML_PAGE)

@app.post("/chat")
async def chat_with_ai(chat_request: ChatRequest):
    user_message = chat_request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="message is required")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction="Sizning ismingiz Steve. Siz aqlli va yordamchi ovozli assistentsiz. Qisqa, aniq va professional tarzda o'zbek tilida javob bering."
            ),
        )
        return {"response": response.text, "status": "success"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)