import os
import shutil
import whisper
import requests
import base64
from gtts import gTTS
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Load environment keys from .env file securely
load_dotenv()

app = FastAPI(title="SIH 2026 Multilingual Audio Pipeline API - Production Build")

# Enable CORS for cross-origin frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Whisper model globally
print("🤖 Initializing production Whisper AI engine...")
whisper_model = whisper.load_model("base")
print("✅ Whisper engine active and listening!")

MEDIA_DIR = "pipeline_media"
os.makedirs(MEDIA_DIR, exist_ok=True)

# Fetch secure system parameters
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")
BHASHINI_USER_ID = os.getenv("BHASHINI_USER_ID", "")

def generate_bhashini_tts(text: str, target_lang: str, output_path: str):
    """
    Executes an authorized HTTP inference request to the official MeitY Bhashini TTS cluster.
    Provides a high-fidelity local fallback loop if credentials evaluate as empty.
    """
    if not BHASHINI_API_KEY or not BHASHINI_USER_ID:
        print("⚠️ Credentials unassigned. Initiating localized fallback processing...")
        fallback_tts = gTTS(text=text, lang=target_lang, slow=False)
        fallback_tts.save(output_path)
        return

    # Official Bhashini Dhruva gateway configurations
    url = "https://bhashini.gov.in"
    headers = {
        "Authorization": BHASHINI_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Standard MeitY inference schema payload mapping
    payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {"sourceLanguage": target_lang},
                    "gender": "female"
                }
            }
        ],
        "inputData": {"input": [{"source": text}]}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=6)
        response.raise_for_status()
        
        # Bhashini returns audio compressed in a base64 string stream
        response_data = response.json()
        audio_base64 = response_data['pipelineResponse'][0]['audio'][0]['audioContent']
        
        with open(output_path, "wb") as audio_file:
            audio_file.write(base64.b64decode(audio_base64))
        print(f"✅ Authentic Bhashini voice response compiled to: {output_path}")
        
    except Exception as error:
        print(f"⚠️ Bhashini core gateway exception: {error}. Deploying local fallback audio recovery...")
        fallback_tts = gTTS(text=text, lang=target_lang, slow=False)
        fallback_tts.save(output_path)

@app.post("/pipeline/process-voice/")
async def process_voice_pipeline(
    audio_file: UploadFile = File(...), 
    target_lang: str = Form("kn")  # 'kn' (Kannada) or 'hi' (Hindi)
):
    temp_input = os.path.join(MEDIA_DIR, f"temp_{audio_file.filename}")
    
    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
        
    try:
        # STAGE 1: Offline Speech-to-Text Processing via Whisper
        transcription_data = whisper_model.transcribe(temp_input)
        raw_transcription = transcription_data["text"]
        detected_language = transcription_data["language"]
        
        # STAGE 2: English Structural Narration Processing
        english_narration_script = f"System log context: User queried processing for: {raw_transcription}"
        narration_filename = f"narration_{audio_file.filename}.mp3"
        narration_output_path = os.path.join(MEDIA_DIR, narration_filename)
        
        narration_engine = gTTS(text=english_narration_script, lang='en', slow=False)
        narration_engine.save(narration_output_path)
        
        # STAGE 3: Multilingual Voice Synthesis (Bhashini Engine with Fallback Protection)
        if target_lang == "hi":
            response_script = f"आपकी क्वेरी सफलतापूर्वक संसाधित हो गई है: {raw_transcription}"
        else:
            response_script = f"ನಿಮ್ಮ ಧ್ವನಿ ವಿನಂತಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗಿದೆ: {raw_transcription}"
            
        response_filename = f"response_{target_lang}_{audio_file.filename}.mp3"
        response_output_path = os.path.join(MEDIA_DIR, response_filename)
        
        generate_bhashini_tts(response_script, target_lang, response_output_path)
        
        # Cleanup cached audio chunk from machine memory
        if os.path.exists(temp_input):
            os.remove(temp_input)
            
        return JSONResponse(status_code=200, content={
            "status": "success",
            "detected_language": detected_language,
            "transcription": raw_transcription,
            "english_narration_text": english_narration_script,
            "regional_response_text": response_script,
            "links": {
                "english_narration": f"/media/{narration_filename}",
                "regional_voice_response": f"/media/{response_filename}"
            }
        })
        
    except Exception as pipeline_error:
        if os.path.exists(temp_input):
            os.remove(temp_input)
        raise HTTPException(status_code=500, detail=str(pipeline_error))

@app.get("/media/{filename}")
async def get_media_file(filename: str):
    file_path = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Resource not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
