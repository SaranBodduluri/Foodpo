import os
from openai import OpenAI
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# Create a static public folder where we can serve the audio clip from
STATIC_AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'services', 'web', 'audio')
os.makedirs(STATIC_AUDIO_DIR, exist_ok=True)

def generate_voice(coach_text: str, style: str) -> str:
    """
    Calls the OpenAI TTS API to generate the coach voice.
    Saves the .mp3 to the web directory and returns the local URL.
    """
    # Map our internal styles to OpenAI's available voices
    voice_map = {
        "hype": "onyx",     # Deeper, punchier
        "gentle": "nova",   # Softer, more pleasant
        "neutral": "alloy"  # Standard
    }
    
    openai_voice = voice_map.get(style, "alloy")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "" # Fail gracefully if key is missing
        
    try:
        client = OpenAI(api_key=api_key)
        
        audio_filename = f"response_{int(time.time())}.mp3"
        audio_path = os.path.join(STATIC_AUDIO_DIR, audio_filename)
        
        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice=openai_voice,
            input=coach_text
        ) as response:
            response.stream_to_file(audio_path)
        
        return f"./audio/{audio_filename}"
        
    except Exception as e:
        print(f"OpenAI TTS failed: {e}")
        return ""
