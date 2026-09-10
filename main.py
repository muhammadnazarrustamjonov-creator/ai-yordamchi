import os
import uvicorn
import tempfile
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from google import genai
from google.genai import types

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
    version="2.0.0"
)

# =========================================================
# STATIC FILES
# =========================================================
app.mount("/static", StaticFiles(directory="static"), name="static")

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
# GLOBAL CHAT SESSION
# =========================================================
client = genai.Client(api_key=api_key) if api_key else None

chat_session = None
if client:
    chat_session = client.chats.create(
        model="gemini-3.5-flash",
        config=types.GenerateContentConfig(
            system_instruction="Siz Steve ismli aqlli, do'stona va professional sun'iy intellekt yordamchisisiz. O'zbek tilida aniq va tushunarli javob bering.",
            max_output_tokens=2000
        )
    )

# =========================================================
# PWA MANIFEST & SERVICE WORKER
# =========================================================

@app.get("/manifest.json")
def get_manifest(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse({
        "id": "/",
        "name": "Steve Assistant",
        "short_name": "Steve",
        "description": "Sun'iy intellekt yordamchisi",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#0f172a",
        "orientation": "portrait",
        "lang": "uz",
        "dir": "ltr",
        "icons": [
            {
                "src": f"{base_url}/static/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": f"{base_url}/static/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any"
            }
        ]
    })


@app.get("/static/service-worker.js")
def get_service_worker():
    sw_code = """
    const CACHE_NAME = 'steve-cache-v6';
    const urlsToCache = [
        '/',
        '/manifest.json',
        '/static/icon-192.png',
        '/static/icon-512.png'
    ];

    self.addEventListener('install', (event) => {
        event.waitUntil(
            caches.open(CACHE_NAME).then((cache) => {
                return cache.addAll(urlsToCache);
            })
        );
        self.skipWaiting();
    });

    self.addEventListener('activate', (event) => {
        event.waitUntil(
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
        );
        event.clients.claim();
    });

    self.addEventListener('fetch', (event) => {
        event.respondWith(
            fetch(event.request)
                .catch(() => caches.match(event.request))
        );
    });
    """
    return PlainTextResponse(sw_code, media_type="application/javascript")


# =========================================================
# HTML & FRONTEND
# =========================================================

HTML_PAGE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steve Assistant</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0f172a">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/static/service-worker.js');
        });
      }
    </script>
    <style>
        * { box-sizing: border-box; }
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
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
            width: 100%;
            max-width: 650px;
            text-align: center;
            border: 1px solid #334155;
        }
        h1 { margin: 0 0 5px 0; color: #38bdf8; font-size: 28px; }
        .sub { color: #94a3b8; font-size: 13px; margin-bottom: 12px; }
        #status {
            color: #38bdf8;
            margin-bottom: 10px;
            font-weight: bold;
            font-size: 13px;
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
            min-height: 150px;
            max-height: 320px;
            text-align: left;
            margin-bottom: 12px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.6;
        }
        .file-preview {
            font-size: 12px;
            color: #38bdf8;
            margin-bottom: 8px;
            text-align: left;
            display: none;
        }
        .input-group {
            display: flex;
            gap: 6px;
            margin-bottom: 8px;
            align-items: center;
        }
        input[type="text"] {
            flex: 1;
            min-width: 0;
            padding: 10px 12px;
            border-radius: 8px;
            border: 1px solid #334155;
            background: #0f172a;
            color: #f8fafc;
            font-size: 14px;
            outline: none;
        }
        input[type="text"]:focus { border-color: #38bdf8; }
        .file-btn {
            background: #334155;
            color: white;
            padding: 10px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            border: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .file-btn:hover { background: #475569; }
        input[type="file"] { display: none; }
        button {
            background: #0284c7;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: 0.2s;
        }
        button:hover { background: #0369a1; }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .actions-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
        }
        .voice-btn { background: #334155; }
        .voice-btn:hover { background: #475569; }
        .user-msg { color: #38bdf8; font-weight: bold; }
        .steve-msg { color: #4ade80; font-weight: bold; }
        .error-msg { color: #f87171; font-weight: bold; }
    </style>
</head>
<body>

<div class="card">
    <h1>Steve</h1>
    <div class="sub">Sun'iy intellekt yordamchisi</div>
    <div id="status">Tizim tayyor. Matn yozing yoki rasm/fayl yuklang...</div>
    
    <div id="chat-box">
        <span>Suhbat tarixi shu yerda ko'rsatiladi...</span>
    </div>

    <div id="file-name-display" class="file-preview">Biriktirilgan fayl: <span id="file-title"></span></div>

    <div class="input-group">
        <input type="text" id="user-input" placeholder="Xabaringizni yozing..." onkeydown="checkEnter(event)">
        <label for="file-input" class="file-btn" title="Fayl yuklash">📁 Fayl</label>
        <input type="file" id="file-input" accept="image/*,audio/*,application/pdf,.txt,.py,.js" onchange="handleFileSelect(event)">
        <button id="send-button" onclick="sendMessage()">Yuborish ➔</button>
    </div>

    <div class="actions-grid">
        <button id="voice-button" class="voice-btn" onclick="startVoice()">Ovoz bilan 🎤</button>
        <button onclick="clearChatHistory()" style="background: #475569;">Tozalash 🔄</button>
    </div>
</div>

<script>
    const statusEl = document.getElementById("status");
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");
    const fileInput = document.getElementById("file-input");
    const fileDisplay = document.getElementById("file-name-display");
    const fileTitle = document.getElementById("file-title");

    let selectedFile = null;
    let chatHistoryHtml = "";

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function checkEnter(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    }

    function handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            selectedFile = file;
            fileTitle.textContent = file.name;
            fileDisplay.style.display = "block";
            statusEl.innerText = `📎 Fayl tanlandi: ${file.name}`;
        }
    }

    function clearChatHistory() {
        chatHistoryHtml = "";
        chatBox.innerHTML = '<span>Suhbat tarixi tozalandi...</span>';
        statusEl.innerText = "🔄 Tarix tozalandi.";
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text && !selectedFile) return;

        const displayMessage = text + (selectedFile ? ` [Fayl: ${selectedFile.name}]` : "");
        chatHistoryHtml += `<br><br><span class="user-msg">Siz:</span> ${escapeHtml(displayMessage)}`;
        chatBox.innerHTML = chatHistoryHtml;
        chatBox.scrollTop = chatBox.scrollHeight;

        userInput.value = "";
        statusEl.innerText = "⏳ Steve o'ylayapti...";
        sendButton.disabled = true;

        const formData = new FormData();
        formData.append("message", text || "Faylni tahlil qil");
        if (selectedFile) formData.append("file", selectedFile);

        try {
            const res = await fetch("/chat", { method: "POST", body: formData });
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Server xatosi");
            }
            const data = await res.json();
            chatHistoryHtml += `<br><br><span class="steve-msg">Steve:</span> ${escapeHtml(data.response)}`;
            chatBox.innerHTML = chatHistoryHtml;
            chatBox.scrollTop = chatBox.scrollHeight;
            statusEl.innerText = "✅ Tayyor.";
        } catch (err) {
            chatHistoryHtml += `<br><br><span class="error-msg">Xatolik:</span> ${escapeHtml(err.message)}`;
            chatBox.innerHTML = chatHistoryHtml;
            statusEl.innerText = "❌ Xatolik.";
        } finally {
            sendButton.disabled = false;
            selectedFile = null;
            fileInput.value = "";
            fileDisplay.style.display = "none";
            userInput.focus();
        }
    }

    function startVoice() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            statusEl.innerText = "❌ Brauzer ovozni qo'llab-quvvatlamaydi.";
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.lang = "uz-UZ";
        recognition.onstart = () => statusEl.innerText = "🎤 Eshitayapman...";
        recognition.onerror = () => statusEl.innerText = "❌ Xatolik.";
        recognition.onresult = async (event) => {
            userInput.value = event.results[0][0].transcript.trim();
            await sendMessage();
        };
        recognition.start();
    }
</script>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML_PAGE)


# =========================================================
# CHAT API (FILE UPLOAD SUPPORT)
# =========================================================

@app.post("/chat")
async def chat_with_ai(
    message: str = Form(...),
    file: UploadFile = File(None)
):
    if not api_key or not chat_session:
        raise HTTPException(status_code=500, detail="Gemini API kaliti topilmadi.")

    temp_file_path = None
    uploaded_file_ref = None

    try:
        contents = [message]
        
        if file:
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                contents_bytes = await file.read()
                temp_file.write(contents_bytes)
                temp_file_path = temp_file.name

            uploaded_file_ref = client.files.upload(file=temp_file_path)
            contents.append(uploaded_file_ref)

        response = chat_session.send_message(contents)
        return {"response": response.text if response else "Javob olinmadi.", "status": "success"}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)