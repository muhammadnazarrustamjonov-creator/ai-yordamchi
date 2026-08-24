import os
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

class ChatRequest(BaseModel):
    message: str

HTML_PAGE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steve Assistant</title>
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
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            width: 90%;
            max-width: 550px;
            text-align: center;
            border: 1px solid #334155;
        }
        h1 { margin-bottom: 5px; color: #38bdf8; }
        .sub { color: #94a3b8; font-size: 13px; margin-bottom: 15px; }
        #status { 
            color: #38bdf8; 
            margin-bottom: 10px; 
            font-weight: bold; 
            font-size: 14px;
            padding: 8px;
            background: #0f172a;
            border-radius: 8px;
            border: 1px solid #334155;
        }
        #chat-box {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 15px;
            min-height: 130px;
            max-height: 220px;
            text-align: left;
            margin-bottom: 15px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.5;
        }
        .input-group {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid #334155;
            background: #0f172a;
            color: #f8fafc;
            font-size: 15px;
            outline: none;
        }
        input[type="text"]:focus {
            border-color: #38bdf8;
        }
        button {
            background: #0284c7;
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            font-weight: bold;
            transition: background 0.2s;
        }
        button:hover { background: #0369a1; }
        .voice-btn {
            width: 100%;
            background: #334155;
            margin-top: 5px;
        }
        .voice-btn:hover { background: #475569; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Steve</h1>
        <div class="sub">Sun'iy intellekt yordamchisi</div>
        <div id="status">Tizim tayyor. Matn yozing yoki ovozli tugmani bosing...</div>
        
        <div id="chat-box">Suhbat tarixi shu yerda ko'rsatiladi...</div>

        <!-- Matnli yozish qismi -->
        <div class="input-group">
            <input type="text" id="user-input" placeholder="Xabaringizni yozing..." onkeydown="checkEnter(event)">
            <button onclick="sendTextMessage()">Yuborish ➔</button>
        </div>

        <!-- Ovozli yordamchi tugmasi -->
        <button class="voice-btn" onclick="startVoice()">Ovoz bilan gapirish 🎤</button>
    </div>

    <script>
        const statusEl = document.getElementById('status');
        const chatBox = document.getElementById('chat-box');
        const userInput = document.getElementById('user-input');

        function checkEnter(event) {
            if (event.key === 'Enter') {
                sendTextMessage();
            }
        }

        async function sendTextMessage() {
            const text = userInput.value.trim();
            if (!text) return;
            
            userInput.value = '';
            await processMessage(text);
        }

        async function processMessage(messageText) {
            chatBox.innerHTML = "<b>Siz:</b> " + messageText;
            statusEl.innerText = "⏳ O'ylayapman...";

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: messageText })
                });

                if (!res.ok) {
                    throw new Error('Server xatosi: ' + res.statusText);
                }

                const data = await res.json();
                const reply = data.response || "Javob topilmadi.";

                chatBox.innerHTML += "<br><br><b>Steve:</b> " + reply;
                statusEl.innerText = "✅ Tayyor. Yana savol berishingiz mumkin.";

            } catch (err) {
                const errMsg = err.message || 'Xatolik yuz berdi';
                statusEl.innerText = "❌ Xatolik yuz berdi.";
                chatBox.innerHTML += "<br><br><b>Xatolik:</b> " + errMsg;
            }
        }

        function startVoice() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                statusEl.innerText = "❌ Brauzeringiz ovozni tanishni qo'llab-quvvatlamaydi.";
                return;
            }

            const recognition = new SpeechRecognition();
            recognition.lang = 'uz-UZ';
            recognition.interimResults = false;
            recognition.continuous = false;

            recognition.onstart = function() {
                statusEl.innerText = "🎤 Eshitayapman, marhamat gapiring...";
            };

            recognition.onerror = function(event) {
                statusEl.innerText = "❌ Ovozni aniqlashda xatolik bo'ldi.";
            };

            recognition.onresult = async function(event) {
                const userSpeech = event.results[0][0].transcript.trim();
                if (!userSpeech) {
                    statusEl.innerText = "❌ Gapirish aniqlanmadi.";
                    return;
                }
                await processMessage(userSpeech);
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
        os.environ["GEMINI_API_KEY"] = api_key
        client = genai.Client()
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=user_message,
            config=genai.types.GenerateContentConfig(
                system_instruction="Sizning ismingiz Steve. Siz aqlli va yordamchi assistentsiz. Qisqa, aniq va professional tarzda o'zbek tilida javob bering."
            ),
        )
        return {"response": response.text, "status": "success"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)