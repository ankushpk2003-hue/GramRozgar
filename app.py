import os
import shutil
import whisper
from gtts import gTTS
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI App
app = FastAPI(
    title="SIH 2026 Multilingual Audio Pipeline API",
    description="Prototype backend for processing, translating, and generating regional voice responses."
)

# Enable CORS so your frontend teammate can easily connect from their local machine
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model once when the backend boots up to save processing time
print("🤖 Loading Whisper AI Model (This takes a moment on first boot)...")
whisper_model = whisper.load_model("base")
print("✅ Whisper Model successfully loaded and ready for queries!")

# Create a media directory to store generated audio files
MEDIA_DIR = "pipeline_media"
os.makedirs(MEDIA_DIR, exist_ok=True)

@app.post("/pipeline/process-voice/")
async def process_voice_pipeline(
    audio_file: UploadFile = File(...), 
    target_lang: str = Form("kn")  # 'kn' for Kannada, 'hi' for Hindi
):
    """
    Core SIH Audio Pipeline Endpoint:
    Takes regional audio, transcribes it via Whisper, generates an English narration,
    and returns a localized regional audio response file link.
    """
    # Create unique name for incoming file to avoid file overwriting
    temp_input_path = os.path.join(MEDIA_DIR, f"temp_{audio_file.filename}")
    
    # Save the incoming frontend recording file locally
    with open(temp_input_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
        
    try:
        print(f"\n--- Processing incoming audio: {audio_file.filename} ---")
        
        # STAGE 1: Audio to Text via Whisper AI (Auto-detects language)
        transcribe_result = whisper_model.transcribe(temp_input_path)
        regional_text = transcribe_result["text"]
        detected_lang = transcribe_result["language"]
        print(f"[Stage 1 Pass] Detected Language: {detected_lang}")
        print(f"[Stage 1 Pass] Transcribed Text: {regional_text}")
        
        # STAGE 2: Translation & English System Narration Track
        # Mock translation step (Replace with your direct LLM/Bhashini translate APIs here later)
        english_translation = f"System log: User requested processing for: {regional_text}"
        
        english_narration_filename = f"narration_{audio_file.filename}.mp3"
        english_narration_path = os.path.join(MEDIA_DIR, english_narration_filename)
        
        # Generate English narration audio track
        tts_en = gTTS(text=english_translation, lang='en', slow=False)
        tts_en.save(english_narration_path)
        print(f"[Stage 2 Pass] Saved English Track: {english_narration_filename}")
        
        # STAGE 3: Final Regional Voice Response Engine
        # Generate dynamic response text based on target language selected
        if target_lang == "hi":
            response_text_regional = f"आपकी क्वेरी मिल गई है: {regional_text}"
        else:
            response_text_regional = f"ನಿಮ್ಮ ಧ್ವನಿ ವಿನಂತಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ: {regional_text}"
            
        regional_response_filename = f"response_{target_lang}_{audio_file.filename}.mp3"
        regional_response_path = os.path.join(MEDIA_DIR, regional_response_filename)
        
        # Generate final regional audio feedback track
        tts_regional = gTTS(text=response_text_regional, lang=target_lang, slow=False)
        tts_regional.save(regional_response_path)
        print(f"[Stage 3 Pass] Generated Regional Response Audio track.")
        
        # Clean up the original heavy input sound file to save space
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
            
        # Return structured data and URLs back to your teammate's frontend app
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
        # Emergency cleanup if the AI pipeline crashes mid-way
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        print(f"❌ Error in pipeline processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/media/{filename}")
async def get_media_file(filename: str):
    """Serves the generated audio tracks back to the UI for audio playback."""
    file_path = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Requested file not found")

if __name__ == "__main__":
    import uvicorn
    # Start the server locally on port 8000
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
