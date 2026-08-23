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

app = FastAPI(title="Steve AI Assistant", version="1.0.0")
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
    <title>Steve AI</title>
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
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            width: 90%;
            max-width: 500px;
            text-align: center;
        }
        h1 { margin-bottom: 10px; color: #38bdf8; }
        #status { color: #94a3b8; margin-bottom: 20px; font-size: 14px; }
        #chat-box {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 15px;
            min-height: 120px;
            text-align: left;
            margin-bottom: 15px;
            overflow-y: auto;
            max-height: 200px;
            white-space: pre-wrap;
        }
        button {
            background: #0284c7;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #0369a1; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Steve AI</h1>
        <div id="status">Mikrofonni yoqish uchun tugmani bosing</div>
        <div id="chat-box">Gapiring...</div>
        <button onclick="startListening()">Ovozli gapirish 🎤</button>
    </div>

    <script>
        function startListening() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Sizning brauzeringiz ovozli qidiruvni qo'llab-quvvatlamaydi.");
                return;
            }

            const recognition = new SpeechRecognition();
            recognition.lang = 'uz-UZ';
            
            document.getElementById('status').innerText = "Tinglanmoqda... Gapiring!";

            recognition.onresult = async function(event) {
                const text = event.results[0][0].transcript;
                document.getElementById('chat-box').innerHTML = "<b>Siz:</b> " + text;
                document.getElementById('status').innerText = "AI javob bermoqda...";

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await response.json();
                    document.getElementById('chat-box').innerHTML += "<br><br><b>Steve:</b> " + (data.response || data.reply);
                    document.getElementById('status').innerText = "Tayyor";
                } catch (err) {
                    document.getElementById('status').innerText = "Xatolik yuz berdi!";
                }
            };

            recognition.onerror = function() {
                document.getElementById('status').innerText = "Mikrofonda xatolik!";
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
        )
        return {"response": response.text, "status": "success"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)