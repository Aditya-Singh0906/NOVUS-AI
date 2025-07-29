# 🧠 Novus AI - Your Personal AI-Powered Desktop Assistant

**Novus AI** is a smart desktop-based voice assistant built with Python. It combines an interactive animated GUI, real-time speech recognition, system automation, AI-generated responses, and online search capabilities — all wrapped in an intuitive and responsive interface.

---

## 🚀 Features

- 🎤 **Voice-controlled commands**
- 🖼️ **Animated graphical interface (GUI)**
- 🔎 **Real-time Google search & YouTube search**
- 🤖 **AI-powered content generation (poems, letters, essays, etc.)**
- 📁 **System-level automation**:
  - Open/close applications
  - Control volume (mute/unmute, volume up/down)
  - Search content on web
- 📄 **Text-to-Speech feedback**
- 🧠 **LLM integration using Groq’s LLaMA-3**

---

## 🛠️ Tech Stack

- **Python 3.10+**
- `pygame` – for GUI rendering
- `speech_recognition` – for voice input
- `gTTS` / `pyttsx3` – for voice output
- `groq` – for AI chat completions (LLaMA-3)
- `AppOpener`, `keyboard`, `webbrowser` – for automation
- `dotenv` – for managing API keys
- `serpapi` – for real-time Google search
- `pywhatkit` – for quick YouTube playback & Google search
- `Pillow` – for image handling

---

## 📂 Project Structure

Novus_AI_Assistant/
│
├── Backend/
│ ├── Main.py # Main execution logic
│ ├── Automation.py # Command translation and system control
│ ├── Chatbot.py # LLM-based response generator
│ ├── SpeechToText.py # Converts speech to text
│ ├── TextToSpeech.py # Converts text to speech
│ ├── ImageGeneration.py # Image generation logic
│ └── ...
│
├── Frontend/
│ ├── GUI.py # GUI rendering and animation
│ └── Files/ # Chat history and image prompt files
│
├── Data/ # Stores generated images and logs
├── .env # API keys (Groq, SerpAPI)
├── requirements.txt # Python dependencies
└── README.md
