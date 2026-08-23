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
if not api_key:
    print("WARNING: GEMINI_API_KEY not set. The /chat endpoint will fail until it is configured.")

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

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at top, #1e293b 0%, var(--bg) 55%);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
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
      margin: 0 0 12px 0;
      font-size: clamp(2rem, 4vw, 2.4rem);
      font-weight: 700;
      color: var(--text);
    }

    p {
      margin: 0 0 20px 0;
      color: var(--muted);
      line-height: 1.6;
      font-size: 14px;
    }

    .status {
      min-height: 28px;
      margin: 18px 0;
      padding: 8px;
      color: var(--accent);
      font-weight: 600;
      font-size: 14px;
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
      font-family: "Monaco", "Courier New", monospace;
      font-size: 13px;
      overflow-y: auto;
      max-height: 400px;
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
    (function() {
      const statusEl = document.getElementById('status');
      const outputEl = document.getElementById('output');
      let recognitionActive = false;

      function setStatus(message) {
        statusEl.textContent = message;
        console.log('[Status]', message);
      }

      function displayOutput(userText, aiResponse) {
        let output = 'Siz: ' + userText;
        if (aiResponse) {
          output = output + '\\n\\nSteve: ' + aiResponse;
        }
        outputEl.textContent = output;
      }

      async function sendToServer(message) {
        if (!message || message.trim().length === 0) {
          throw new Error('Bo\\'sh xabar yuborish mumkin emas.');
        }

        const response = await fetch('/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ message: message.trim() })
        });

        if (!response.ok) {
          let errorDetail = 'Server xatosi';
          try {
            const errorData = await response.json();
            errorDetail = errorData.detail || errorData.message || errorDetail;
          } catch (e) {
            errorDetail = 'HTTP ' + response.status + ': ' + response.statusText;
          }
          throw new Error(errorDetail);
        }

        const data = await response.json();
        if (!data.response) {
          throw new Error('Serverdan bo\\'sh javob keldi.');
        }

        return data.response;
      }

      function startListening() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
          setStatus('❌ Bu brauzer ovozni tanishni qo\\'llab-quvvatlamaydi.');
          outputEl.textContent = 'Iltimos, Chrome, Edge yoki Firefox brauzerini ishlating.';
          return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'uz-UZ';
        recognition.interimResults = false;
        recognition.continuous = false;

        recognition.onstart = function() {
          recognitionActive = true;
          setStatus('🎤 Mikrofon yoqildi. Gaplaringizni tinglayapman...');
        };

        recognition.onresult = async function(event) {
          const isFinal = event.results[0].isFinal;
          const transcript = event.results[0][0].transcript.trim();

          if (!transcript || !isFinal) {
            return;
          }

          recognitionActive = false;
          setStatus('⏳ Gap qabul qilindi. Serverga yuborilmoqda...');
          displayOutput(transcript, null);

          try {
            const aiResponse = await sendToServer(transcript);
            displayOutput(transcript, aiResponse);
            setStatus('✅ Javob ekranga chiqarildi. Qayta gapirish uchun vaqtini kuting...');

            setTimeout(function() {
              setStatus('🔄 Qayta boshlanmoqda...');
              startListening();
            }, 1000);
          } catch (error) {
            const errorMsg = error.message || 'Noma\\'lum xatolik';
            displayOutput(transcript, 'Xatolik: ' + errorMsg);
            setStatus('❌ Xatolik yuz berdi. Qayta urinib ko\\'ramiz...');

            setTimeout(function() {
              setStatus('🔄 Qayta boshlanmoqda...');
              startListening();
            }, 2000);
          }
        };

        recognition.onerror = function(event) {
          let errorMsg = event.error;
          const errorMap = {
            'network': 'Tarmoq xatosi',
            'audio-capture': 'Mikrofon qayd qilina olmadi',
            'not-allowed': 'Mikrofon uchun ruxsat berilmadi',
            'no-speech': 'Gapirish aniqlanmadi',
            'service-not-allowed': 'Servis qo\\'llabilmadi'
          };
          errorMsg = errorMap[event.error] || errorMsg;

          setStatus('❌ Mikrofon xatosi: ' + errorMsg);
          recognitionActive = false;

          setTimeout(function() {
            setStatus('🔄 Qayta urinib ko\\'ramiz...');
            startListening();
          }, 2000);
        };

        recognition.onend = function() {
          recognitionActive = false;
          if (statusEl.textContent.includes('Javob') || statusEl.textContent.includes('Qayta boshlanmoqda')) {
            return;
          }
          console.log('[Info] Recognition ended');
        };

        recognition.start();
      }

      if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
          navigator.serviceWorker.register('/service-worker.js').catch(function(err) {
            console.warn('Service worker ro\\'yxatdan o\\'tishda muammo bo\\'ldi:', err);
          });
        });
      }

      window.addEventListener('load', function() {
        setStatus('🚀 Ilovaga xush kelibsiz!');
        setTimeout(function() {
          startListening();
        }, 500);
      });

      window.addEventListener('beforeunload', function() {
        if (recognitionActive) {
          setStatus('Sahifani tark etish...');
        }
      });
    })();
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
                system_instruction="You are Steve, a helpful AI assistant. Answer clearly and briefly."
            ),
        )
        return {"response": response.text, "status": "success"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gemini API xatosi: {str(exc)}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
