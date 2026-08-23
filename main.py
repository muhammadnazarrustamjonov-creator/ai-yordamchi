import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from google import genai
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Steve AI Serveri")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
SYSTEM_INSTRUCTION = "You are Steve, a helpful AI assistant. Always introduce yourself as Steve."


class ChatRequest(BaseModel):
    message: str


@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html lang="uz">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Steve AI</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    background: #111827;
                    color: #f9fafb;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                }
                .card {
                    width: min(90vw, 700px);
                    background: rgba(17, 24, 39, 0.9);
                    border: 1px solid #374151;
                    border-radius: 16px;
                    padding: 24px;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35);
                }
                h1 {
                    margin-top: 0;
                    font-size: 28px;
                }
                #status {
                    color: #93c5fd;
                    margin-bottom: 16px;
                    min-height: 24px;
                }
                #result {
                    white-space: pre-wrap;
                    background: #0f172a;
                    border: 1px solid #334155;
                    border-radius: 10px;
                    padding: 16px;
                    line-height: 1.6;
                    min-height: 120px;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Steve AI</h1>
                <div id="status">Mikrofon ishga tayyorlanmoqda...</div>
                <div id="result">Gapingizni ayting...</div>
            </div>

            <script>
                const statusEl = document.getElementById('status');
                const resultEl = document.getElementById('result');

                function setStatus(message) {
                    statusEl.textContent = message;
                }

                function startListening() {
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

                    if (!SpeechRecognition) {
                        setStatus('Bu brauzer ovozli kirishni qo\'llab-quvvatlamaydi.');
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

                        resultEl.textContent = 'Foydalanuvchi: ' + transcript;
                        setStatus('Gap qabul qilindi. Serverga yuborilmoqda...');

                        try {
                            const response = await fetch('/chat', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ message: transcript })
                            });

                            const data = await response.json();

                            if (!response.ok) {
                                throw new Error(data.detail || 'Serverdan javob olinmadi.');
                            }

                            resultEl.textContent = 'Foydalanuvchi: ' + transcript + '\n\nSteve: ' + (data.response || 'Javob yo\'q');
                            setStatus('Javob ekranga chiqarildi.');
                        } catch (error) {
                            resultEl.textContent = 'Xatolik: ' + (error.message || 'Noma\'lum xatolik');
                            setStatus('Xatolik yuz berdi.');
                        }
                    };

                    recognition.onerror = function (event) {
                        setStatus('Mikrofon xatosi: ' + event.error);
                    };

                    recognition.onend = function () {
                        setStatus('Mikrofon o\'chdi. Qayta boshlanmoqda...');
                        setTimeout(startListening, 300);
                    };

                    recognition.start();
                }

                window.addEventListener('load', startListening);
            </script>
        </body>
        </html>
        """
    )


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