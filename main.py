import os

import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse

from google import genai
from google.genai import types

from pydantic import BaseModel


# =========================================================
# ENV
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Steve Assistant",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# PWA ENDPOINTS (PWABuilder uchun to'g'ridan-to'g'ri javoblar)
# =========================================================

@app.get("/manifest.json")
def get_manifest():
    return {
        "name": "Steve Assistant",
        "short_name": "Steve",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#0f172a",
        "icons": [
            {
                "src": "https://pwabuilder.com/assets/images/icon_512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }


@app.get("/static/service-worker.js")
def get_service_worker():
    sw_code = """
    self.addEventListener('install', (event) => {
        self.skipWaiting();
    });
    self.addEventListener('activate', (event) => {
        event.clients.claim();
    });
    self.addEventListener('fetch', (event) => {
        event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
    });
    """
    return PlainTextResponse(sw_code, media_type="application/javascript")


# =========================================================
# REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    message: str


# =========================================================
# HTML
# =========================================================

HTML_PAGE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steve Assistant</title>
    <link rel="manifest" href="/manifest.json">
    <script>
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/service-worker.js');
      }
    </script>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #0f172a;
            color: #f8fafc;
            font-family: Arial, sans-serif;
            padding: 15px;
        }
        .card {
            background: #1e293b;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            width: 100%;
            max-width: 600px;
            text-align: center;
            border: 1px solid #334155;
        }
        h1 {
            margin: 0 0 5px 0;
            color: #38bdf8;
            font-size: 32px;
        }
        .sub {
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 15px;
        }
        #status {
            color: #38bdf8;
            margin-bottom: 10px;
            font-weight: bold;
            font-size: 14px;
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
            min-height: 130px;
            max-height: 300px;
            text-align: left;
            margin-bottom: 15px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.6;
        }
        .input-group {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
        }
        input[type="text"] {
            flex: 1;
            min-width: 0;
            padding: 12px 14px;
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
            transition: 0.2s;
        }
        button:hover {
            background: #0369a1;
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .voice-btn {
            width: 100%;
            background: #334155;
            margin-top: 5px;
        }
        .voice-btn:hover {
            background: #475569;
        }
        .user-name {
            color: #38bdf8;
            font-weight: bold;
        }
        .steve-name {
            color: #4ade80;
            font-weight: bold;
        }
        .error-name {
            color: #f87171;
            font-weight: bold;
        }
        @media (max-width: 500px) {
            .card {
                padding: 18px;
            }
            .input-group {
                flex-direction: column;
            }
            button {
                width: 100%;
            }
        }
    </style>
</head>
<body>

<div class="card">
    <h1>Steve</h1>
    <div class="sub">Sun'iy intellekt yordamchisi</div>
    <div id="status">Tizim tayyor. Matn yozing yoki ovozli tugmani bosing...</div>
    <div id="chat-box">
        <span>Suhbat tarixi shu yerda ko'rsatiladi...</span>
    </div>

    <div class="input-group">
        <input type="text" id="user-input" placeholder="Xabaringizni yozing..." onkeydown="checkEnter(event)">
        <button id="send-button" onclick="sendTextMessage()">Yuborish ➔</button>
    </div>

    <button id="voice-button" class="voice-btn" onclick="startVoice()">Ovoz bilan gapirish 🎤</button>
</div>

<script>
    const statusEl = document.getElementById("status");
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");
    const voiceButton = document.getElementById("voice-button");

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function checkEnter(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendTextMessage();
        }
    }

    async function sendTextMessage() {
        const text = userInput.value.trim();
        if (!text) return;
        userInput.value = "";
        await processMessage(text);
    }

    async function processMessage(messageText) {
        const safeMessage = escapeHtml(messageText);
        chatBox.innerHTML = '<span class="user-name">Siz:</span> ' + safeMessage;
        statusEl.innerText = "⏳ Steve o'ylayapti...";
        sendButton.disabled = true;
        voiceButton.disabled = true;

        try {
            const res = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: messageText })
            });

            if (!res.ok) {
                let errorMessage = "Server xatosi";
                try {
                    const errorData = await res.json();
                    if (errorData.detail) errorMessage = errorData.detail;
                } catch (e) {
                    errorMessage = `Server xatosi: ${res.status}`;
                }
                throw new Error(errorMessage);
            }

            const data = await res.json();
            const reply = data.response || "Javob topilmadi.";
            const safeReply = escapeHtml(reply);

            chatBox.innerHTML += "<br><br>" + '<span class="steve-name">Steve:</span> ' + safeReply;
            statusEl.innerText = "✅ Tayyor. Yana savol berishingiz mumkin.";
        } catch (err) {
            const errMsg = err.message || "Xatolik yuz berdi";
            chatBox.innerHTML += "<br><br>" + '<span class="error-name">Xatolik:</span> ' + escapeHtml(errMsg);
            statusEl.innerText = "❌ Xatolik yuz berdi.";
            console.error("CHAT ERROR:", err);
        } finally {
            sendButton.disabled = false;
            voiceButton.disabled = false;
            userInput.focus();
        }
    }

    function startVoice() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            statusEl.innerText = "❌ Brauzeringiz ovozni tanishni qo'llab-quvvatlamaydi.";
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = "uz-UZ";
        recognition.interimResults = false;
        recognition.continuous = false;

        recognition.onstart = function() {
            statusEl.innerText = "🎤 Eshitayapman, marhamat gapiring...";
            voiceButton.disabled = true;
        };

        recognition.onerror = function(event) {
            console.error("VOICE ERROR:", event);
            statusEl.innerText = "❌ Ovozni aniqlashda xatolik bo'ldi.";
            voiceButton.disabled = false;
        };

        recognition.onend = function() {
            voiceButton.disabled = false;
        };

        recognition.onresult = async function(event) {
            const userSpeech = event.results[0][0].transcript.trim();
            if (!userSpeech) {
                statusEl.innerText = "❌ Gapirish aniqlanmadi.";
                return;
            }
            await processMessage(userSpeech);
        };

        try {
            recognition.start();
        } catch (error) {
            console.error("VOICE START ERROR:", error);
            statusEl.innerText = "❌ Ovozni ishga tushirishda xatolik.";
        }
    }
</script>

</body>
</html>
"""


# =========================================================
# HOME PAGE
# =========================================================

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_PAGE)


# =========================================================
# CHAT API
# =========================================================

@app.post("/chat")
def chat_with_ai(chat_request: ChatRequest):
    user_message = chat_request.message.strip()

    if not user_message:
        raise HTTPException(
            status_code=400,
            detail="message is required"
        )

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY topilmadi. .env faylni tekshiring."
        )

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction="Siz Steve ismli aqlli va foydali sun'iy intellekt yordamchisisiz. O'zbek tilida qisqa, aniq va professional javob bering.",
                max_output_tokens=1000
            )
        )

        reply = response.text

        if not reply:
            reply = "Kechirasiz, javob olinmadi."

        return {
            "response": reply,
            "status": "success"
        }

    except Exception as exc:
        print("\n==============================")
        print("GEMINI XATOSI:")
        print(repr(exc))
        print("==============================\n")

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )