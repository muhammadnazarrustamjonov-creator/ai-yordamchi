import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from google import genai
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
if not api_key:
    print("WARNING: GEMINI_API_KEY not set. The /chat endpoint will fail until it is configured.")
client = genai.Client(api_key=api_key)

MANIFEST_PATH = Path(__file__).with_name("manifest.json")


class ChatRequest(BaseModel):
    message: str


HTML_PAGE = """
<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="theme-color" content="#0f172a" />
  <meta name="description" content="Steve AI yordamchisi" />
  <title>Steve AI</title>
  <link rel="manifest" href="/manifest.json" />
  <link rel="icon" href="/static/icon-192.png" type="image/png" />
  <style>
    :root {
      --bg: #0f172a;
      --bg-soft: #111827;
      --panel: #1f2937;
      --text: #f8fafc;
      --muted: #cbd5e1;
      --accent: #60a5fa;
      --line: #334155;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at top, #1e293b 0%, var(--bg) 55%);
      color: var(--text);
      font-family: Arial, sans-serif;
    }

    .card {
      width: min(90vw, 720px);
      background: rgba(17, 24, 39, 0.9);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
    }

    h1 {
      margin: 0 0 12px;
      font-size: clamp(2rem, 4vw, 2.4rem);
    }

    p {
      margin: 0;
      color: var(--muted);
      line-height: 1.6;
    }

    .status {
      min-height: 28px;
      margin: 18px 0;
      color: var(--accent);
      font-weight: 600;
    }

    .output {
      min-height: 140px;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      line-height: 1.7;
      white-space: pre-wrap;
      word-break: break-word;
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>Steve AI</h1>
    <p>Ovozli mikrofondan gapni qabul qilib, matn ko'rinishida serverga yuboradi.</p>
    <div class="status" id="status">Mikrofon tayyorlanmoqda...</div>
    <div class="output" id="output">Gapingizni ayting...</div>
  </div>

  <script>
    const statusEl = document.getElementById('status');
    const outputEl = document.getElementById('output');

    function setStatus(message) {
      statusEl.textContent = message;
    }

    function displayUserText(text) {
      outputEl.textContent = 'Siz: ' + text;
    }

    function sendToServer(message) {
      return fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      }).then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || 'Server javob bermadi.');
        }
        return data.response || 'Javob yo\'q';
      });
    }

    function startListening() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (!SpeechRecognition) {
        setStatus('Bu brauzer ovozni tanishni qo\'llab-quvvatlamaydi.');
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.lang = 'uz-UZ';
      recognition.interimResults = false;
      recognition.continuous = false;

      recognition.onstart = function () {
        setStatus('Mikrofon yoqildi. Gaplaringizni tinglayapman...');
      };

      recognition.onresult = async function (event) {
        const transcript = event.results[0][0].transcript.trim();

        if (!transcript) {
          setStatus('Hech narsa tushunilmadi. Qayta urinib ko\'ramiz...');
          recognition.start();
          return;
        }

        displayUserText(transcript);
        setStatus('Gap qabul qilindi. Serverga yuborilmoqda...');

        try {
          const aiText = await sendToServer(transcript);
          outputEl.textContent = 'Siz: ' + transcript + '\n\nSteve: ' + aiText;
          setStatus('Javob ekranga chiqarildi.');
        } catch (error) {
          outputEl.textContent = 'Xatolik: ' + (error.message || 'Noma\'lum xatolik');
          setStatus('Xatolik yuz berdi.');
        }
      };

      recognition.onerror = function (event) {
        setStatus('Mikrofon xatosi: ' + event.error);
      };

      recognition.onend = function () {
        setStatus('Mikrofon yopildi. Qayta boshlanmoqda...');
        setTimeout(startListening, 400);
      };

      recognition.start();
    }

    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function () {
        navigator.serviceWorker.register('/service-worker.js').catch(function () {
          console.warn('Service worker ro\'yxatdan o\'tishda muammo bo\'ldi.');
        });
      });
    }

    window.addEventListener('load', startListening);
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(content=HTML_PAGE)


@app.get("/manifest.json")
async def get_manifest() -> JSONResponse:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return JSONResponse(content=manifest)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="manifest.json not found") from exc


@app.get("/service-worker.js")
async def service_worker() -> HTMLResponse:
    return HTMLResponse(
        content="""
const CACHE_NAME = 'steve-ai-v1';
const ASSETS = ['/', '/manifest.json'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
        return response;
      }).catch(() => caches.match('/'));
    })
  );
});
        """,
        media_type="application/javascript",
    )


@app.post("/chat")
async def chat_with_ai(request: Request):
    data = await request.json()
    user_message = (data.get("message") or "").strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="message is required")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message,
            config={"system_instruction": "You are Steve, a helpful AI assistant. Answer clearly and briefly."},
        )
        return {"response": response.text}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
