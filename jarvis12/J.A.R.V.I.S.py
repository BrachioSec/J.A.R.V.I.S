import sys
import os
import tempfile
import threading
import queue
import time
import logging
from datetime import datetime
import sqlite3
import re
import random
import webbrowser
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Check for required modules
try:
    import tkinter as tk
    from tkinter import scrolledtext, messagebox, ttk
except ImportError as e:
    print(f"Tkinter not available: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

# Optional imports with fallbacks
MODULES = {
    'requests': False,
    'bs4': False,
    'wikipedia': False,
    'speech_recognition': False,
    'pygame': False,
    'gtts': False,
    'ollama': False
}

try:
    import pygame
    MODULES['pygame'] = True
    # Initialize pygame mixer
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
except ImportError:
    logger.warning("pygame not available - audio features disabled")

try:
    from gtts import gTTS
    MODULES['gtts'] = True
except ImportError:
    logger.warning("gTTS not available - Google TTS disabled")

try:
    import speech_recognition as sr
    MODULES['speech_recognition'] = True
except ImportError:
    logger.warning("speech_recognition not available - voice input disabled")

try:
    import requests
    MODULES['requests'] = True
except ImportError:
    logger.warning("requests not available - web features disabled")

try:
    from bs4 import BeautifulSoup
    MODULES['bs4'] = True
except ImportError:
    logger.warning("BeautifulSoup not available - web parsing disabled")

try:
    import wikipedia
    MODULES['wikipedia'] = True
    wikipedia.set_lang("en")
except ImportError:
    logger.warning("wikipedia not available - Wikipedia integration disabled")

try:
    import ollama
    MODULES['ollama'] = True
except ImportError:
    logger.warning("ollama not available - local AI features disabled")

# Color palette - Modern tech theme
COLORS = {
    'bg_dark': '#0a192f',
    'bg_medium': '#112240',
    'bg_light': '#233554',
    'accent': '#64ffda',
    'text_primary': '#e6f1ff',
    'text_secondary': '#8892b0',
    'success': '#64ffda',
    'warning': '#f8f851',
    'error': '#ff5c79',
    'highlight': '#00a8ff',
    'listening': '#ff5c79',
    'ai_thinking': '#a882ff'
}

# Modern fonts
FONTS = {
    'title': ('Segoe UI', 24, 'bold'),
    'heading': ('Segoe UI', 16, 'bold'),
    'body': ('Segoe UI', 11),
    'monospace': ('Consolas', 10),
    'small': ('Segoe UI', 9)
}

class OllamaIntegration:
    """Integration with Ollama for intelligent responses"""
    
    def __init__(self):
        self.available = MODULES['ollama']
        self.model = "llama3"  # Default model
        self.thinking = False
        
    def check_models(self):
        """Check available Ollama models"""
        if not self.available:
            return False
            
        try:
            models = ollama.list()
            return bool(models.get('models', []))
        except Exception as e:
            logger.error(f"Ollama check error: {e}")
            return False
    
    def generate_response(self, prompt, context=None):
        """Generate a response using Ollama"""
        if not self.available:
            return "Ollama integration is not available. Please install the ollama Python package."
        
        self.thinking = True
        
        try:
            # Prepare the message with context
            messages = []
            
            # Add context if provided
            if context:
                messages.append({"role": "system", "content": context})
            
            # Add the user's prompt
            messages.append({"role": "user", "content": prompt})
            
            # Generate response
            response = ollama.chat(model=self.model, messages=messages)
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
        finally:
            self.thinking = False
    
    def is_thinking(self):
        """Check if Ollama is currently processing"""
        return self.thinking

class WebAccess:
    """Handles web access and information retrieval"""
    
    def __init__(self):
        self.available = MODULES['requests'] and MODULES['bs4']
        
    def search_web(self, query):
        """Search the web for information"""
        if not self.available:
            return "Web access is not available. Please install requests and beautifulsoup4."
        
        try:
            # Use Google search
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Try to get a summary from Wikipedia first
            if MODULES['wikipedia']:
                try:
                    summary = wikipedia.summary(query, sentences=2)
                    return f"According to Wikipedia: {summary}"
                except wikipedia.exceptions.DisambiguationError as e:
                    # If it's a disambiguation, try the first option
                    try:
                        summary = wikipedia.summary(e.options[0], sentences=2)
                        return f"According to Wikipedia: {summary}"
                    except:
                        pass
                except:
                    pass
            
            # If Wikipedia fails, try a general web search
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to extract the featured snippet
            featured_snippet = soup.find('div', class_='BNeawe s3v9rd AP7Wnd')
            if featured_snippet:
                return f"According to web sources: {featured_snippet.get_text()}"
            
            # If no featured snippet, try to get the first result
            first_result = soup.find('div', class_='BNeawe vvjwJb AP7Wnd')
            if first_result:
                return f"According to web sources: {first_result.get_text()}"
            
            return "I couldn't find specific information about that topic."
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return "I encountered an error while searching for information."
    
    def open_website(self, site_name):
        """Open a website in the default browser"""
        sites = {
            'google': 'https://www.google.com',
            'youtube': 'https://www.youtube.com',
            'facebook': 'https://www.facebook.com',
            'twitter': 'https://www.twitter.com',
            'github': 'https://www.github.com',
            'wikipedia': 'https://www.wikipedia.org',
            'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com'
        }
        
        if site_name in sites:
            webbrowser.open(sites[site_name])
            return f"Opening {site_name.capitalize()} for you, sir."
        else:
            return f"I don't know how to open {site_name}, sir."

class SpeechRecognizer:
    """Handles speech recognition from microphone"""
    
    def __init__(self):
        self.available = MODULES['speech_recognition']
        self.recognizer = None
        self.microphone = None
        self.listening = False
        
        if self.available:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                
                # Adjust for ambient noise
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                logger.info("Speech recognition initialized")
            except Exception as e:
                logger.error(f"Speech recognition init error: {e}")
                self.available = False
    
    def listen(self):
        """Listen to microphone and return recognized text"""
        if not self.available:
            return None
            
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            text = self.recognizer.recognize_google(audio)
            return text.lower()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None

class IntegratedTTS:
    """Integrated TTS using Google's Text-to-Speech API with British accent"""
    
    def __init__(self):
        self.available = MODULES['gtts'] and MODULES['pygame']
        self.speaking = False
        self.temp_files = []
        
    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass
        self.temp_files = []
    
    def speak(self, text):
        """Speak text using Google TTS with British accent"""
        if not text.strip() or not self.available:
            return
            
        def speak_thread():
            self.speaking = True
            try:
                # Create a temporary file for the audio
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                    temp_path = tmp_file.name
                
                # Generate speech using Google TTS with British English
                tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
                tts.save(temp_path)
                self.temp_files.append(temp_path)
                
                # Load and play the audio
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                # Wait for the audio to finish playing
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                    
            except Exception as e:
                logger.error(f"TTS error: {e}")
            finally:
                self.speaking = False
                
        threading.Thread(target=speak_thread, daemon=True).start()
    
    def is_speaking(self):
        """Check if currently speaking"""
        return self.speaking
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup_temp_files()

class JarvisAssistant:
    """JARVIS application with speech recognition, TTS, web access, and Ollama integration"""
    
    def __init__(self, root):
        self.root = root
        self.setup_window()
        
        # Initialize components
        self.tts = IntegratedTTS()
        self.speech_recognizer = SpeechRecognizer()
        self.web_access = WebAccess()
        self.ollama = OllamaIntegration()
        self.init_database()
        
        # State variables
        self.conversation_history = []
        self.is_listening = False
        
        # Create GUI
        self.create_gui()
        
        # Message queue
        self.message_queue = queue.Queue()
        self.process_message_queue()
        
        # Welcome
        self.welcome_message()
    
    def setup_window(self):
        """Setup main window with modern styling"""
        self.root.title("JARVIS AI Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"800x600+{x}+{y}")
        
        # Configure styles
        self.configure_styles()
        
        # Make window resizable
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
    
    def configure_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        
        # Configure theme
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        # Configure styles
        style.configure('TFrame', background=COLORS['bg_dark'])
        style.configure('TLabel', background=COLORS['bg_dark'], 
                       foreground=COLORS['text_primary'], font=FONTS['body'])
        style.configure('Title.TLabel', font=FONTS['title'], 
                       foreground=COLORS['accent'])
        style.configure('Status.TLabel', font=FONTS['small'], 
                       foreground=COLORS['text_secondary'])
        style.configure('TEntry', fieldbackground=COLORS['bg_light'],
                       foreground=COLORS['text_primary'], borderwidth=1)
        style.configure('TScrollbar', background=COLORS['bg_light'],
                       troughcolor=COLORS['bg_dark'], borderwidth=0)
        style.configure('Mic.TButton', background=COLORS['accent'])
    
    def init_database(self):
        """Initialize database"""
        try:
            os.makedirs("data", exist_ok=True)
            self.conn = sqlite3.connect("data/jarvis.db", check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    speaker TEXT,
                    message TEXT
                )
            ''')
            self.conn.commit()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database init error: {e}")
            self.conn = None
            self.cursor = None
    
    def create_gui(self):
        """Create the modern GUI with microphone button"""
        # Main container with weighted layout
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.columnconfigure(1, weight=1)
        
        # Title with icon
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky="w")
        
        title = ttk.Label(title_frame, text="J.A.R.V.I.S.", style="Title.TLabel")
        title.pack(side=tk.LEFT)
        
        # Status area
        status_frame = ttk.Frame(header_frame)
        status_frame.grid(row=0, column=1, sticky="e")
        
        self.status_label = ttk.Label(status_frame, text="● ONLINE", 
                                    style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Conversation area with modern styling
        chat_frame = ttk.Frame(main_frame)
        chat_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 20))
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        
        # Create custom chat area with better styling
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, width=60, height=15,
            bg=COLORS['bg_medium'], fg=COLORS['text_primary'], 
            font=FONTS['monospace'],
            insertbackground=COLORS['accent'], 
            relief=tk.FLAT, 
            borderwidth=0,
            padx=15,
            pady=15
        )
        self.chat_area.grid(row=0, column=0, sticky="nsew")
        self.chat_area.config(state=tk.DISABLED)
        
        # Input area
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)
        
        # Modern input field
        self.text_input = ttk.Entry(input_frame, font=FONTS['body'])
        self.text_input.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.text_input.bind('<Return>', self.handle_text_input)
        
        # Send button
        send_btn = ttk.Button(input_frame, text="Send", 
                             command=self.handle_text_input)
        send_btn.grid(row=0, column=1, sticky="e", padx=(0, 10))
        
        # Microphone button
        self.mic_btn = ttk.Button(input_frame, text="🎤", width=3,
                                 command=self.toggle_listening)
        self.mic_btn.grid(row=0, column=2, sticky="e")
        
        # Configure grid weights
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        input_frame.columnconfigure(0, weight=1)
    
    def toggle_listening(self):
        """Toggle listening state"""
        if not self.speech_recognizer.available:
            self.add_message("SYSTEM", "Speech recognition is not available")
            return
            
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """Start listening for voice input"""
        self.is_listening = True
        self.mic_btn.config(text="🔴")
        self.status_label.config(text="● LISTENING")
        self.add_message("SYSTEM", "Listening...")
        
        # Start listening in a separate thread
        threading.Thread(target=self.listen_thread, daemon=True).start()
    
    def stop_listening(self):
        """Stop listening for voice input"""
        self.is_listening = False
        self.mic_btn.config(text="🎤")
        self.status_label.config(text="● ONLINE")
        self.add_message("SYSTEM", "Stopped listening")
    
    def listen_thread(self):
        """Thread for listening to voice input"""
        while self.is_listening:
            try:
                # Listen for audio
                text = self.speech_recognizer.listen()
                
                if text is None:
                    # Timeout or error
                    continue
                    
                if text == "":
                    # Speech was detected but not understood
                    self.add_message("SYSTEM", "I didn't catch that. Please try again.")
                    continue
                
                # Process the recognized text
                self.root.after(0, lambda: self.process_voice_input(text))
                
            except Exception as e:
                logger.error(f"Error in listen thread: {e}")
                self.root.after(0, lambda: self.stop_listening())
    
    def process_voice_input(self, text):
        """Process voice input text"""
        self.add_message("YOU (Voice)", text)
        self.save_conversation("YOU", text)
        self.process_command(text)
    
    def welcome_message(self):
        """Display welcome message"""
        msg = "Good day, sir. JARVIS systems online.\n"
        if self.tts.available:
            msg += "Voice synthesis: ACTIVE\n"
        else:
            msg += "Voice synthesis: DISABLED\n"
            
        if self.speech_recognizer.available:
            msg += "Voice recognition: ACTIVE\n"
        else:
            msg += "Voice recognition: DISABLED\n"
            
        if self.web_access.available:
            msg += "Web access: ACTIVE\n"
        else:
            msg += "Web access: DISABLED\n"
            
        if self.ollama.available:
            if self.ollama.check_models():
                msg += "Local AI: ACTIVE (Llama3)\n"
            else:
                msg += "Local AI: DISABLED (No models found)\n"
        else:
            msg += "Local AI: DISABLED\n"
            
        msg += "How may I assist you today?"
        
        self.add_message("JARVIS", msg)
        if self.tts.available:
            self.tts.speak("Good day, sir. JARVIS systems online. How may I assist you?")
    
    def handle_text_input(self, event=None):
        """Handle text input"""
        text = self.text_input.get().strip()
        if text:
            self.text_input.delete(0, tk.END)
            self.add_message("YOU", text)
            self.save_conversation("YOU", text)
            self.process_command(text)
    
    def process_command(self, command):
        """Process user commands"""
        cmd = command.lower().strip()
        
        # Direct commands
        if cmd in ["time", "what time", "what's the time"]:
            time_str = datetime.now().strftime("%H:%M:%S")
            self.add_jarvis_response(f"The current time is {time_str}, sir.")
            return
        
        if cmd in ["date", "what date", "what's the date"]:
            date_str = datetime.now().strftime("%A, %B %d, %Y")
            self.add_jarvis_response(f"Today is {date_str}, sir.")
            return
        
        if "clear" in cmd and "screen" in cmd:
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.delete(1.0, tk.END)
            self.chat_area.config(state=tk.DISABLED)
            self.add_jarvis_response("Display cleared, sir.")
            return
            
        if any(word in cmd for word in ["hello", "hi", "hey", "greetings"]):
            greetings = [
                "Hello, sir. How may I assist you?",
                "Good day, sir. What can I do for you?",
                "Hello there. How may I be of service?",
                "Greetings, sir. How can I help you today?"
            ]
            self.add_jarvis_response(random.choice(greetings))
            return
            
        if any(word in cmd for word in ["thank", "thanks", "appreciate"]):
            responses = [
                "You're welcome, sir.",
                "Always a pleasure to assist, sir.",
                "Happy to help, sir.",
                "At your service, sir."
            ]
            self.add_jarvis_response(random.choice(responses))
            return
            
        if any(word in cmd for word in ["how are you", "how do you do"]):
            responses = [
                "I'm functioning optimally, thank you for asking, sir.",
                "All systems are operational, sir. How may I assist you?",
                "I'm well, sir. Ready to assist with your needs.",
                "Operating at full capacity, sir. How can I help?"
            ]
            self.add_jarvis_response(random.choice(responses))
            return
            
        # Web search commands
        if cmd.startswith("search for ") or cmd.startswith("look up "):
            query = cmd.replace("search for ", "").replace("look up ", "")
            self.add_message("JARVIS", f"Searching for information about {query}...")
            result = self.web_access.search_web(query)
            self.add_jarvis_response(result)
            return
            
        if cmd.startswith("open "):
            site = cmd.replace("open ", "")
            result = self.web_access.open_website(site)
            self.add_jarvis_response(result)
            return
            
        if "weather" in cmd:
            self.add_message("JARVIS", "Checking weather information...")
            result = self.web_access.search_web("weather")
            self.add_jarvis_response(result)
            return
            
        if "news" in cmd:
            self.add_message("JARVIS", "Checking latest news...")
            result = self.web_access.search_web("latest news")
            self.add_jarvis_response(result)
            return
        
        # Use Ollama for intelligent responses to complex queries
        if self.ollama.available and self.ollama.check_models():
            # Show thinking indicator
            self.add_message("JARVIS", "Thinking...", thinking=True)
            
            # Process with Ollama in a separate thread
            def ollama_thread():
                # Create context from conversation history
                context = "You are JARVIS, an AI assistant. You have a British male voice and are polite but efficient. "
                context += "Respond concisely but helpfully to the user's queries."
                
                # Add recent conversation history for context
                if self.conversation_history:
                    context += "\n\nRecent conversation:\n"
                    for msg in self.conversation_history[-5:]:  # Last 5 messages
                        context += f"{msg['speaker']}: {msg['message']}\n"
                
                response = self.ollama.generate_response(command, context)
                
                # Update UI in the main thread
                self.root.after(0, lambda: self.add_jarvis_response(response))
            
            threading.Thread(target=ollama_thread, daemon=True).start()
        else:
            # Default response if Ollama is not available
            responses = [
                "How may I assist you further, sir?",
                "At your service, sir.",
                "I'm here to help, sir.",
                "What else can I do for you, sir?",
                "I didn't quite understand that, sir. Could you rephrase?",
                "I'm not sure how to help with that, sir. Perhaps try a web search?"
            ]
            self.add_jarvis_response(random.choice(responses))
    
    def add_jarvis_response(self, response):
        """Add JARVIS response with TTS"""
        self.add_message("JARVIS", response)
        self.save_conversation("JARVIS", response)
        if self.tts.available:
            self.tts.speak(response)
    
    def add_message(self, sender, message, thinking=False):
        """Add message to display queue"""
        self.message_queue.put((sender, message, datetime.now(), thinking))
    
    def process_message_queue(self):
        """Process message display queue"""
        try:
            while True:
                sender, message, timestamp, thinking = self.message_queue.get_nowait()
                
                self.chat_area.config(state=tk.NORMAL)
                
                time_str = timestamp.strftime("%H:%M:%S")
                
                # Add timestamp
                self.chat_area.insert(tk.END, f"[{time_str}] ", "timestamp")
                
                # Add sender with appropriate color
                if sender == "JARVIS":
                    if thinking:
                        self.chat_area.insert(tk.END, f"{sender}: ", "thinking_sender")
                    else:
                        self.chat_area.insert(tk.END, f"{sender}: ", "jarvis_sender")
                elif sender == "YOU":
                    self.chat_area.insert(tk.END, f"{sender}: ", "user_sender")
                elif "Voice" in sender:
                    self.chat_area.insert(tk.END, f"{sender}: ", "voice_sender")
                else:
                    self.chat_area.insert(tk.END, f"{sender}: ", "system_sender")
                
                # Add message
                self.chat_area.insert(tk.END, f"{message}\n\n")
                
                # Configure tags for styling
                self.chat_area.tag_config("timestamp", foreground=COLORS['text_secondary'])
                self.chat_area.tag_config("jarvis_sender", foreground=COLORS['accent'])
                self.chat_area.tag_config("thinking_sender", foreground=COLORS['ai_thinking'])
                self.chat_area.tag_config("user_sender", foreground=COLORS['success'])
                self.chat_area.tag_config("voice_sender", foreground=COLORS['highlight'])
                self.chat_area.tag_config("system_sender", foreground=COLORS['warning'])
                
                self.chat_area.config(state=tk.DISABLED)
                self.chat_area.see(tk.END)
                
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_message_queue)
    
    def save_conversation(self, speaker, message):
        """Save conversation to database and memory"""
        if self.cursor:
            try:
                timestamp = datetime.now().isoformat()
                self.cursor.execute(
                    "INSERT INTO conversations (timestamp, speaker, message) VALUES (?, ?, ?)",
                    (timestamp, speaker, message)
                )
                self.conn.commit()
            except Exception as e:
                logger.error(f"Database save error: {e}")
        
        # Keep in memory
        self.conversation_history.append({"speaker": speaker, "message": message})
        if len(self.conversation_history) > 20:
            self.conversation_history.pop(0)
    
    def cleanup_and_exit(self):
        """Clean shutdown"""
        self.is_listening = False
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        self.root.quit()

def main():
    """Main application entry point"""
    try:
        print("Starting JARVIS AI Assistant...")
        
        # Check for missing optional modules
        missing = []
        for module, available in MODULES.items():
            if not available:
                missing.append(module)
        
        if missing:
            print("\nOptional modules not found (some features may be limited):")
            for module in missing:
                if module == 'gtts':
                    print("  pip install gtts")
                elif module == 'pygame':
                    print("  pip install pygame")
                elif module == 'speech_recognition':
                    print("  pip install SpeechRecognition")
                    print("  pip install pyaudio (may require additional setup)")
                elif module == 'requests':
                    print("  pip install requests")
                elif module == 'bs4':
                    print("  pip install beautifulsoup4")
                elif module == 'wikipedia':
                    print("  pip install wikipedia")
                elif module == 'ollama':
                    print("  pip install ollama")
                    print("  Note: You also need to install Ollama itself from https://ollama.ai/")
                    print("  And download a model like: ollama pull llama3")
            print()
        
        # Start GUI
        root = tk.Tk()
        app = JarvisAssistant(root)
        root.protocol("WM_DELETE_WINDOW", app.cleanup_and_exit)
        
        print("JARVIS GUI started successfully!")
        root.mainloop()
        
    except Exception as e:
        import traceback
        error_msg = f"JARVIS startup error: {e}\n\nFull traceback:\n{traceback.format_exc()}"
        print(error_msg)
        
        try:
            messagebox.showerror("JARVIS Error", f"Failed to start JARVIS:\n\n{str(e)}")
        except:
            pass
        
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()