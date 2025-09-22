# J.A.R.V.I.S
This is an AI thats inspired from Ironmans jarvis hence the name its a speech based AI that browse the web and more.

https://img.shields.io/badge/JARVIS-Enhanced-blue?style=for-the-badge
https://img.shields.io/badge/Python-3.8%252B-green?style=for-the-badge
https://img.shields.io/badge/AI-Assistant-orange?style=for-the-badge

🚀 Features
Core Capabilities
Advanced Voice Recognition - Enhanced speech-to-text with noise cancellation and multiple recognition engines

Natural Text-to-Speech - High-quality voice synthesis with British accent and intelligent text cleaning

Smart Command Processing - Context-aware command classification with pattern matching

Web Search Integration - Real-time information retrieval from Wikipedia and web sources

Local AI Intelligence - Ollama integration for intelligent conversation (requires Llama3 model)

Enhanced UI/UX
Modern Dark Theme - Professional interface with Iron Man-inspired color scheme

Real-time Status Monitoring - Live component status indicators

Priority Message Queue - Intelligent message handling system

Conversation History - Persistent storage with SQLite database

Visual Voice Feedback - Animated indicators for listening/speaking states

Technical Features
Modular Architecture - Extensible component-based design

Error Handling - Robust error recovery and graceful degradation

Performance Monitoring - Processing time tracking and optimization

Cross-platform Support - Works on Windows, macOS, and Linux

📋 Prerequisites
Required Software
Python 3.8 or higher

Ollama

PREQUISETS

bash
pip install gtts pygame SpeechRecognition pyaudio requests beautifulsoup4 wikipedia ollama pydub
For Windows users (if pyaudio fails):

bash
pip install gtts pygame SpeechRecognition requests beautifulsoup4 wikipedia ollama pydub
pip install pipwin
pipwin install pyaudio
Alternative for pyaudio issues:

bash
pip install gtts pygame SpeechRecognition requests beautifulsoup4 wikipedia ollama pydub
python -m pip install pyaudio --index-url=https://pypi.org/simple/ --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
One-liner with error handling:

bash
pip install gtts pygame SpeechRecognition requests beautifulsoup4 wikipedia ollama pydub && pip install pyaudio || python -m pip install pyaudio --index-url=https://pypi.org/simple/ --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

