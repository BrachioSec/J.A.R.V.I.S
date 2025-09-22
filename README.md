# J.A.R.V.I.S
*Inspired by Ironman, this AI is a speech-based assistant that can browse the web and more.*

[![JARVIS-Enhanced](https://img.shields.io/badge/JARVIS-Enhanced-blue?style=for-the-badge)](https://img.shields.io/badge/JARVIS-Enhanced-blue?style=for-the-badge)  
[![Python-3.8+](https://img.shields.io/badge/Python-3.8%252B-green?style=for-the-badge)](https://img.shields.io/badge/Python-3.8%252B-green?style=for-the-badge)  
[![AI-Assistant](https://img.shields.io/badge/AI-Assistant-orange?style=for-the-badge)](https://img.shields.io/badge/AI-Assistant-orange?style=for-the-badge)

---

## 🚀 Features

### Core Capabilities
- **Advanced Voice Recognition** – Enhanced speech-to-text with noise cancellation and multiple recognition engines  
- **Natural Text-to-Speech** – High-quality voice synthesis with British accent and intelligent text cleaning  
- **Smart Command Processing** – Context-aware command classification with pattern matching  
- **Web Search Integration** – Real-time information retrieval from Wikipedia and web sources  
- **Local AI Intelligence** – Ollama integration for intelligent conversation (requires Llama3 model)  

### Enhanced UI/UX
- **Modern Dark Theme** – Professional interface with Iron Man-inspired color scheme  
- **Real-time Status Monitoring** – Live component status indicators  
- **Priority Message Queue** – Intelligent message handling system  
- **Conversation History** – Persistent storage with SQLite database  
- **Visual Voice Feedback** – Animated indicators for listening/speaking states  

### Technical Features
- **Modular Architecture** – Extensible component-based design  
- **Error Handling** – Robust error recovery and graceful degradation  
- **Performance Monitoring** – Processing time tracking and optimization  
- **Cross-platform Support** – Works on Windows, macOS, and Linux  

---

## 📋 Prerequisites

### Required Software
- Python 3.8 or higher  
- Ollama(The ollama model must be running on the background I use llama 3 so fort me its ollama run llama3)  

### Python Packages
```bash
pip install gtts pygame SpeechRecognition pyaudio requests beautifulsoup4 wikipedia ollama pydub
```
Windows Users (if PyAudio fails):
```bash
pip install gtts pygame SpeechRecognition requests beautifulsoup4 wikipedia ollama pydub
pip install pipwin
pipwin install pyaudio
```

## 🎯 Getting Started

1. Clone the repository:

```bash
git clone https://github.com/yourusername/jarvis.git
cd jarvis
```
2. Install the prerequisites
3. Run JARVIS
```bash
python J.A.R.V.I.S
```
