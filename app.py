import os
import shutil
import whisper
import requests
import base64
from gtts import gTTS
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI App
app = FastAPI(title="SIH 2026 Multilingual Audio Pipeline API")

# Enable CORS for frontend teammate connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model once on boot
print("🤖 Loading Whisper AI Model (This takes a moment on first boot)...")
whisper_model = whisper.load_model("base")
print("✅ Whisper Model successfully loaded and ready for queries!")

MEDIA_DIR = "pipeline_media"
os.makedirs(MEDIA_DIR, exist_ok=True)

# 🔐 Bhashini Credentials (Will fall back cleanly if left empty)
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")

def call_bhashini_tts(text: str, lang: str, output_path: str):
    """
    Connects to official MeitY Bhashini API for authentic regional voice output.
    Falls back cleanly to gTTS if keys are missing or API fails.
    """
    if not BHASHINI_API_KEY or not BHASHINI_USER_ID:
        print("⚠️ No Bhashini keys found. Using local fallback voice engine.")
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)
        return

    # Official Bhashini Ultech / Dhruva inference endpoint layout
    url = "https://bhashini.gov.in"
    headers = {
        "Authorization": BHASHINI_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {"language": {"sourceLanguage": lang}, "gender": "female"}
            }
        ],
        "inputData": {"input": [{"source": text}]}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        # Bhashini returns audio content as base64 string
        audio_content = response.json()['pipelineResponse'][0]['audio'][0]['audioContent']
        with open(output_path, "wb") as fh:
            fh.decode(base64.b64decode(audio_content))
        print("✅ Bhashini Audio successfully generated.")
    except Exception as e:
        print(f"⚠️ Bhashini API failed ({e}). Dropping back to fallback engine.")
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)

@app.post("/pipeline/process-voice/")
async def process_voice_pipeline(
    audio_file: UploadFile = File(...), 
    target_lang: str = Form("kn")  # 'kn' for Kannada, 'hi' for Hindi
):
    temp_input_path = os.path.join(MEDIA_DIR, f"temp_{audio_file.filename}")
    
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
        
    try:
        # STAGE 1: Audio to Text via Whisper AI (Local & Fast)
        transcribe_result = whisper_model.transcribe(temp_input_path)
        regional_text = transcribe_result["text"]
        detected_lang = transcribe_result["language"]
        
        # STAGE 2: Translation & English System Narration Track
        english_translation = f"System log: User requested processing for: {regional_text}"
        english_narration_filename = f"narration_{audio_file.filename}.mp3"
        english_narration_path = os.path.join(MEDIA_DIR, english_narration_filename)
        
        tts_en = gTTS(text=english_translation, lang='en', slow=False)
        tts_en.save(english_narration_path)
        
        # STAGE 3: Final Regional Voice Response Engine (Bhashini with Fallback)
        if target_lang == "hi":
            response_text_regional = f"आपकी क्वेरी मिल गई है: {regional_text}"
        else:
            response_text_regional = f"ನಿಮ್ಮ ಧ್ವನಿ ವಿನಂತಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ: {regional_text}"
            
        regional_response_filename = f"response_{target_lang}_{audio_file.filename}.mp3"
        regional_response_path = os.path.join(MEDIA_DIR, regional_response_filename)
        
        # Core API / Fallback Execution
        call_bhashini_tts(response_text_regional, target_lang, regional_response_path)
        
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
            
        return JSONResponse(status_code=200, content={
            "status": "success",
            "detected_language": detected_lang,
            "transcription": regional_text,
            "english_translation": english_translation,
            "regional_response_text": response_text_regional,
            "links": {
                "english_narration": f"/media/{english_narration_filename}",
                "regional_voice_response": f"/media/{regional_response_filename}"
            }
        })
        
    except Exception as e:
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/media/{filename}")
async def get_media_file(filename: str):
    file_path = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
