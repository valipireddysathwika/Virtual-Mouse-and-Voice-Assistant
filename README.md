# 🎯 Virtual Mouse & Voice Assistant (macOS)

A dual-purpose desktop automation project developed in Python that includes:

- A Virtual Mouse controlled via hand gestures using computer vision.
- A Voice Assistant capable of executing tasks via natural language commands.

**Supports macOS systems only.**

## 🚀 Features

### Virtual Mouse
- Control mouse movement using hand gestures via webcam.
- Click, drag, and scroll with intuitive finger gestures.
- Powered by OpenCV and MediaPipe for hand tracking.

### Voice Assistant
- Recognizes voice commands using SpeechRecognition.
- Executes commands like opening apps, searching Google, system info, etc.
- Provides voice feedback via pyttsx3.

## 🛠️ Installation

**Clone the repository:**
```bash
git clone https://github.com/yourusername/virtual-mouse-voice-assistant.git
cd virtual-mouse-voice-assistant
```

**Create a virtual environment (optional but recommended):**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## ▶️ Usage

### Virtual Mouse
```bash
python virtual_mouse.py
```
- Ensure your webcam is active.
- Perform hand gestures to move and click.

### Voice Assistant
```bash
python voice_assistant.py
```
- Speak naturally after the prompt.
- Ensure microphone access is enabled.

## 📦 Requirements
- Python 3.8+
- macOS (tested on Monterey and later)
- Installed Python packages:
  - opencv-python
  - mediapipe
  - pyttsx3
  - speechrecognition
  - pyobjc (for macOS integrations)

## 📸 Screenshots
(Add screenshots or screen recordings demonstrating the project in action.)

## 💡 Future Improvements
- Add GUI dashboard.
- Support for other platforms (Windows/Linux).
- Smarter NLP integration with GPT or other LLMs.

## 📄 License
MIT License. See LICENSE for more info.
