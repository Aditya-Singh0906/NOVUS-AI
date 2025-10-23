import pygame
import random
import asyncio
import edge_tts
import os
import uuid
from dotenv import dotenv_values
from Backend.Utils import resource_path


# Import STOP_ALL_TASKS directly from main.py
try:
    from Main import STOP_ALL_TASKS
except ImportError:
    STOP_ALL_TASKS = False

# Load environment variables
env_path = resource_path(".env")
env_vars = dotenv_values(env_path)
AssistantVoice = env_vars.get("AssistantVoice")

# --- Private Helper Functions ---

async def _text_to_audio_file(text: str) -> str:
    """
    Converts text to an MP3 file with a unique filename.
    Returns the path to the generated file.
    """
    file_path = resource_path(os.path.join("Data", f"speech_{uuid.uuid4().hex}.mp3"))
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(file_path)
    return file_path

def _play_audio(text: str, func=lambda: True):
    """
    Plays the generated audio file using pygame.
    Stops immediately if STOP_ALL_TASKS is True or func() returns False.
    Cleans up temporary files after playback.
    """
    global STOP_ALL_TASKS
    audio_file = None
    try:
        if STOP_ALL_TASKS:
            return

        audio_file = asyncio.run(_text_to_audio_file(text))

        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            if STOP_ALL_TASKS or func() is False:
                pygame.mixer.music.stop()
                return False
            pygame.time.Clock().tick(10)

    except Exception as e:
        print(f"Error in _play_audio: {e}")
    finally:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            # DO NOT quit mixer to keep audio device valid
        # Clean up temporary file
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
            except Exception as e:
                print(f"Failed to delete temporary audio file: {e}")

# --- Public Facing Function ---

def TextToSpeech(text: str, func=lambda: True):
    """
    Main TTS function. Handles long text splitting and adds a concluding response.
    """
    global STOP_ALL_TASKS
    if STOP_ALL_TASKS:
        return

    sentences = [s.strip() for s in str(text).split('.') if s.strip()]

    responses = [
        "The rest of the result is on your screen, sir.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on your screen.",
    ]

    if len(sentences) > 3 and len(text) > 250:
        speech_text = ". ".join(sentences[0:2]) + "."
        full_speech = f"{speech_text} {random.choice(responses)}"
        _play_audio(full_speech, func)
    else:
        _play_audio(text, func)

# --- Standalone Testing ---
if __name__ == "__main__":
    while True:
        user_text = input("Enter the text to speak (or 'exit' to quit): ")
        if user_text.lower() in ["exit", "quit"]:
            break
        print("\n--- Speaking ---")
        TextToSpeech(user_text)
        print("--- Done ---\n")
