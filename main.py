import os
import uvicorn
import tempfile
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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
    version="2.1.1"
)

# =========================================================
# STATIC FILES & TEMPLATES
# =========================================================
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction="Siz Steve ismli aqlli, do'stona va professional sun'iy intellekt yordamchisisiz. O'zbek tilida aniq va tushunarli javob bering.",
            max_output_tokens=2000
        )
    )

# =========================================================
# HTML ROUTE (TEMPLATES)
# =========================================================

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


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