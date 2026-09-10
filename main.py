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
    version="2.1.0"
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
        "background_color": "#090d16",
        "theme_color": "#090d16",
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
    const CACHE_NAME = 'steve-cache-v7';
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
# HTML & MODERN FRONTEND
# =========================================================

HTML_PAGE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steve Assistant</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#090d16">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/static/service-worker.js');
        });
      }
    </script>
    <style>
        :root {
            --bg-main: #090d16;
            --bg-card: #111827;
            --bg-input: #1f2937;
            --border-color: #374151;
            --accent-color: #3b82f6;
            --accent-hover: #2563eb;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --bot-bubble: #1f2937;
            --user-bubble: #2563eb;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            background-color: var(--bg-main);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }

        .app-container {
            width: 100%;
            max-width: 800px;
            height: 100%;
            max-height: 900px;
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4);
            overflow: hidden;
        }

        @media (max-width: 840px) {
            .app-container {
                height: 100%;
                max-height: 100vh;
                border-radius: 0;
                border: none;
            }
        }

        /* Header */
        .app-header {
            padding: 16px 20px;
            background-color: rgba(17, 24, 39, 0.8);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .header-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            color: white;
            box-shadow: 0 4px 12px rgba(59, 130, 246,.3);
        }

        .title-group h1 {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-main);
        }

        .title-group span {
            font-size: 12px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .title-group span::before {
            content: '';
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
        }

        .header-actions {
            display: flex;
            gap: 8px;
        }

        .icon-btn {
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            width: 36px;
            height: 36px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .icon-btn:hover {
            background-color: var(--bg-input);
            color: var(--text-main);
            border-color: var(--text-muted);
        }

        /* Chat Area */
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            scroll-behavior: smooth;
        }

        .message {
            max-width: 75%;
            padding: 12px 16px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.5;
            word-break: break-word;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
            background-color: var(--user-bubble);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .message.bot {
            background-color: var(--bot-bubble);
            color: var(--text-main);
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border: 1px solid var(--border-color);
        }

        .message.error {
            background-color: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #f87171;
            align-self: center;
            text-align: center;
            width: 100%;
            max-width: 100%;
        }

        .welcome-card {
            text-align: center;
            margin: auto;
            padding: 40px 20px;
            color: var(--text-muted);
        }

        .welcome-card h2 {
            color: var(--text-main);
            font-size: 20px;
            margin-bottom: 8px;
        }

        /* File Preview Container */
        .file-preview-bar {
            padding: 8px 20px;
            background-color: rgba(31, 41, 55, 0.5);
            border-top: 1px solid var(--border-color);
            display: none;
            align-items: center;
            justify-content: space-between;
            font-size: 13px;
            color: var(--accent-color);
        }

        .file-preview-info {
            display: flex;
            align-items: center;
            gap: 8px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .remove-file {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 16px;
        }
        .remove-file:hover { color: #f87171; }

        /* Input Area */
        .input-area {
            padding: 16px 20px;
            background-color: var(--bg-card);
            border-top: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .input-wrapper {
            display: flex;
            align-items: center;
            background-color: var(--bg-input);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 6px 8px;
            transition: border-color 0.2s;
        }

        .input-wrapper:focus-within {
            border-color: var(--accent-color);
        }

        .chat-input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-main);
            padding: 10px 12px;
            font-size: 14px;
            outline: none;
        }

        .chat-input::placeholder {
            color: var(--text-muted);
        }

        .action-icon-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            width: 38px;
            height: 38px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: 0.2s;
        }

        .action-icon-btn:hover {
            background-color: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
        }

        .send-btn {
            background-color: var(--accent-color);
            color: white;
            border: none;
            width: 38px;
            height: 38px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: 0.2s;
        }

        .send-btn:hover {
            background-color: var(--accent-hover);
        }

        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Status bar small text */
        .status-bar {
            font-size: 11px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 4px;
        }
    </style>
</head>
<body>

<div class="app-container">
    <!-- Header -->
    <div class="app-header">
        <div class="header-info">
            <div class="avatar">S</div>
            <div class="title-group">
                <h1>Steve Assistant</h1>
                <span id="status-text">Faol va tayyor</span>
            </div>
        </div>
        <div class="header-actions">
            <button class="icon-btn" onclick="startVoice()" title="Ovozli qidiruv">🎤</button>
            <button class="icon-btn" onclick="clearChatHistory()" title="Suhbatni tozalash">🔄</button>
        </div>
    </div>

    <!-- Chat Messages Container -->
    <div class="chat-messages" id="chat-box">
        <div class="welcome-card" id="welcome-card">
            <h2>Assalomu alaykum!</h2>
            <p>Men Steve, sizning sun'iy intellekt yordamchingizman. Bugun sizga qanday yordam bera olaman?</p>
        </div>
    </div>

    <!-- File Preview Bar -->
    <div class="file-preview-bar" id="file-preview-bar">
        <div class="file-preview-info">
            <span>📎 Fayl:</span>
            <span id="file-name-title" style="font-weight: 500;"></span>
        </div>
        <button class="remove-file" onclick="removeSelectedFile()" title="O'chirish">&times;</button>
    </div>

    <!-- Input Form -->
    <div class="input-area">
        <div class="input-wrapper">
            <input type="file" id="file-input" style="display: none;" accept="image/*,audio/*,application/pdf,.txt,.py,.js" onchange="handleFileSelect(event)">
            <button class="action-icon-btn" onclick="document.getElementById('file-input').click()" title="Fayl biriktirish">
                <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
            </button>
            <input type="text" id="user-input" class="chat-input" placeholder="Xabaringizni yozing..." onkeydown="checkEnter(event)">
            <button class="send-btn" id="send-button" onclick="sendMessage()" title="Yuborish">
                <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M12 5l7 7-7 7"></path></svg>
            </button>
        </div>
        <div class="status-bar">
            <span id="sub-status">Gemini 3.5 Flash modeli</span>
            <span>Steve v2.1</span>
        </div>
    </div>
</div>

<script>
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");
    const statusText = document.getElementById("status-text");
    const fileInput = document.getElementById("file-input");
    const filePreviewBar = document.getElementById("file-preview-bar");
    const fileNameTitle = document.getElementById("file-name-title");
    const welcomeCard = document.getElementById("welcome-card");

    let selectedFile = null;

    function checkEnter(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    }

    function handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            selectedFile = file;
            fileNameTitle.textContent = file.name;
            filePreviewBar.style.display = "flex";
            statusText.textContent = "Fayl biriktirildi";
        }
    }

    function removeSelectedFile() {
        selectedFile = null;
        fileInput.value = "";
        filePreviewBar.style.display = "none";
        statusText.textContent = "Faol va tayyor";
    }

    function clearChatHistory() {
        chatBox.innerHTML = `
            <div class="welcome-card" id="welcome-card">
                <h2>Suhbat tozalandi</h2>
                <p>Yangi mavzuni boshlashingiz mumkin.</p>
            </div>
        `;
        statusText.textContent = "Tarix tozalandi";
    }

    function appendMessage(sender, text, isError = false) {
        if (welcomeCard && welcomeCard.parentNode) {
            welcomeCard.remove();
        }

        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${sender} ${isError ? 'error' : ''}`;
        
        if (sender === 'bot' && !isError) {
            msgDiv.innerHTML = `<strong>Steve:</strong><br>${escapeHtml(text)}`;
        } else if (sender === 'user') {
            msgDiv.innerHTML = `<strong>Siz:</strong><br>${escapeHtml(text)}`;
        } else {
            msgDiv.textContent = text;
        }

        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text && !selectedFile) return;

        const displayMsg = text + (selectedFile ? ` [Fayl: ${selectedFile.name}]` : "");
        appendMessage('user', displayMsg);

        userInput.value = "";
        const currentFile = selectedFile;
        removeSelectedFile();

        statusText.textContent = "Steve o'ylayapti...";
        sendButton.disabled = true;

        const formData = new FormData();
        formData.append("message", text || "Faylni tahlil qil");
        if (currentFile) formData.append("file", currentFile);

        try {
            const res = await fetch("/chat", { method: "POST", body: formData });
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Server xatosi");
            }
            const data = await res.json();
            appendMessage('bot', data.response);
            statusText.textContent = "Faol va tayyor";
        } catch (err) {
            appendMessage('bot', `Xatolik: ${err.message}`, true);
            statusText.textContent = "Xatolik yuz berdi";
        } finally {
            sendButton.disabled = false;
            userInput.focus();
        }
    }

    function startVoice() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            statusText.textContent = "Ovozli qidiruv qo'llab-quvvatlanmaydi";
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.lang = "uz-UZ";
        recognition.onstart = () => statusText.textContent = "Eshitayapman...";
        recognition.onerror = () => statusText.textContent = "Ovozni aniqlashda xato";
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