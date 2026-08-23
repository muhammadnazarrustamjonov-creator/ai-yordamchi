import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google import genai

app = FastAPI()

# Statik fayllar va manifest uchun papka sozlamalari
# (Agar static papkasi bo'lmasa, uni yaratib qo'yasiz)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Gemini API ni sozlash (Render'dagi Environment variable'dan kalitni oladi)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Steve AI Assistant</title>
        <!-- PWA uchun manifest ulanishi -->
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#1f1f1f">
        <style>
            body {
                background-color: #121212;
                color: #ffffff;
                font-family: Arial, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
                width: 90%;
                max-width: 400px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 18px;
                border-radius: 8px;
                cursor: pointer;
                margin-top: 20px;
            }
            button:active {
                background-color: #45a049;
            }
            #response {
                margin-top: 20px;
                font-size: 16px;
                line-height: 1.5;
                background: #1f1f1f;
                padding: 15px;
                border-radius: 8px;
                min-height: 50px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Steve AI Assistant</h2>
            <p>Gapirish uchun tugmani bosing:</p>
            <button onclick="startListening()">Mikrofonni yoqish</button>
            <div id="response">Tayyor...</div>
        </div>

        <script>
            async function startListening() {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                if (!SpeechRecognition) {
                    alert("Brauzeringiz ovozni tanishni qo'llab-quvvatlamaydi.");
                    return;
                }

                const recognition = new SpeechRecognition();
                recognition.lang = 'uz-UZ';
                
                recognition.onstart = function() {
                    document.getElementById('response').innerText = "Tinglayapman...";
                };

                recognition.onresult = async function(event) {
                    const text = event.results[0][0].transcript;
                    document.getElementById('response').innerText = "Siz: " + text;

                    // Serverga so'rov yuborish
                    try {
                        let res = await fetch('/ask', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ prompt: text })
                        });
                        let data = await res.json();
                        document.getElementById('response').innerText = data.answer;
                    } catch (err) {
                        document.getElementById('response').innerText = "Xatolik yuz berdi.";
                    }
                };

                recognition.start();
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/ask")
async def ask_ai(request: Request):
    data = await request.json()
    user_prompt = data.get("prompt", "")
    
    try:
        # Gemini 2.5 Flash yordamida javob olish
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt
        )
        return {"answer": response.text}
    except Exception as e:
        return {"answer": f"Xatolik: {str(e)}"}