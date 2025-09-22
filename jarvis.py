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
import asyncio
from pathlib import Path
from contextlib import contextmanager

# Configure advanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
    logger.error(f"Tkinter not available: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

# Enhanced module detection with version checking
MODULES = {
    'requests': {'available': False, 'version': None},
    'bs4': {'available': False, 'version': None},
    'wikipedia': {'available': False, 'version': None},
    'speech_recognition': {'available': False, 'version': None},
    'pygame': {'available': False, 'version': None},
    'gtts': {'available': False, 'version': None},
    'ollama': {'available': False, 'version': None},
    'pydub': {'available': False, 'version': None},
    'pyaudio': {'available': False, 'version': None}
}

def check_module(module_name, import_name=None):
    """Enhanced module checking with version detection"""
    if import_name is None:
        import_name = module_name
    
    try:
        module = __import__(import_name)
        MODULES[module_name]['available'] = True
        if hasattr(module, '__version__'):
            MODULES[module_name]['version'] = module.__version__
        return module
    except ImportError:
        logger.warning(f"{module_name} not available")
        return None

# Initialize modules
pygame = check_module('pygame')
if pygame:
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        logger.info("Pygame mixer initialized")
    except pygame.error as e:
        logger.error(f"Pygame mixer init failed: {e}")
        MODULES['pygame']['available'] = False

gtts_module = check_module('gtts')
speech_recognition = check_module('speech_recognition')
requests = check_module('requests')
bs4 = check_module('bs4')
wikipedia = check_module('wikipedia')
ollama = check_module('ollama')
pydub = check_module('pydub')
pyaudio = check_module('pyaudio')

# Enhanced color palette
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
    'ai_thinking': '#a882ff',
    'voice_active': '#00ff88',
    'system': '#ffa500'
}

FONTS = {
    'title': ('Segoe UI', 26, 'bold'),
    'heading': ('Segoe UI', 18, 'bold'),
    'body': ('Segoe UI', 12),
    'monospace': ('Consolas', 11),
    'small': ('Segoe UI', 10),
    'micro': ('Segoe UI', 8)
}

class AudioManager:
    """Advanced audio management for better TTS and speech recognition"""
    
    def __init__(self):
        self.temp_files = []
        self.audio_lock = threading.Lock()
        self.current_audio = None
        
    def cleanup_temp_files(self):
        """Clean up temporary audio files safely"""
        with self.audio_lock:
            for file_path in self.temp_files[:]:  # Copy list to avoid modification during iteration
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                        self.temp_files.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {file_path}: {e}")
    
    @contextmanager
    def temp_audio_file(self, suffix='.mp3'):
        """Context manager for temporary audio files"""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        self.temp_files.append(temp_path)
        try:
            yield temp_path
        finally:
            # File will be cleaned up by cleanup_temp_files
            pass

class EnhancedTTS:
    """Enhanced Text-to-Speech with improved voice quality and error handling"""
    
    def __init__(self):
        self.available = MODULES['gtts']['available'] and MODULES['pygame']['available']
        self.speaking = False
        self.audio_manager = AudioManager()
        self.voice_settings = {
            'lang': 'en',
            'tld': 'co.uk',  # British accent
            'slow': False
        }
        self.speech_queue = queue.Queue()
        self.worker_thread = None
        self.stop_worker = False
        
        if self.available:
            self.start_worker()
    
    def start_worker(self):
        """Start the TTS worker thread"""
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()
    
    def _speech_worker(self):
        """Worker thread for processing TTS requests"""
        while not self.stop_worker:
            try:
                text = self.speech_queue.get(timeout=1)
                if text is None:  # Poison pill
                    break
                self._speak_sync(text)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TTS worker error: {e}")
    
    def speak(self, text, interrupt=False):
        """Queue text for speaking"""
        if not text.strip() or not self.available:
            return
        
        if interrupt:
            self.stop_speaking()
            
        # Clean text for better TTS
        cleaned_text = self._clean_text(text)
        self.speech_queue.put(cleaned_text)
    
    def _clean_text(self, text):
        """Clean text for better TTS pronunciation"""
        # Remove excessive punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Replace common abbreviations with full words
        replacements = {
            'sir.': 'sir',
            'Mr.': 'Mister',
            'Mrs.': 'Missus',
            'Dr.': 'Doctor',
            'etc.': 'etcetera',
            'e.g.': 'for example',
            'i.e.': 'that is',
            'vs.': 'versus'
        }
        
        for abbr, full in replacements.items():
            text = text.replace(abbr, full)
        
        return text
    
    def _speak_sync(self, text):
        """Synchronous speech generation and playback"""
        self.speaking = True
        try:
            with self.audio_manager.temp_audio_file() as temp_path:
                # Generate TTS audio
                from gtts import gTTS
                tts = gTTS(
                    text=text,
                    lang=self.voice_settings['lang'],
                    tld=self.voice_settings['tld'],
                    slow=self.voice_settings['slow']
                )
                tts.save(temp_path)
                
                # Load and play audio
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                # Wait for completion with interruption support
                while pygame.mixer.music.get_busy() and self.speaking:
                    pygame.time.wait(100)
                    
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
        finally:
            self.speaking = False
    
    def stop_speaking(self):
        """Stop current speech"""
        self.speaking = False
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    def is_speaking(self):
        """Check if currently speaking"""
        return self.speaking
    
    def change_voice(self, lang='en', tld='co.uk', slow=False):
        """Change voice settings"""
        self.voice_settings = {'lang': lang, 'tld': tld, 'slow': slow}
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_worker = True
        if self.worker_thread:
            self.speech_queue.put(None)  # Poison pill
            self.worker_thread.join(timeout=1)
        self.audio_manager.cleanup_temp_files()

class EnhancedSpeechRecognizer:
    """Enhanced speech recognition with better accuracy and noise handling"""
    
    def __init__(self):
        self.available = MODULES['speech_recognition']['available']
        self.recognizer = None
        self.microphone = None
        self.listening = False
        self.calibrated = False
        
        if self.available:
            self._initialize_recognizer()
    
    def _initialize_recognizer(self):
        """Initialize speech recognizer with optimal settings"""
        try:
            import speech_recognition as sr
            
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Enhanced recognizer settings
            self.recognizer.energy_threshold = 300  # Lower threshold for better sensitivity
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.dynamic_energy_adjustment_damping = 0.15
            self.recognizer.dynamic_energy_ratio = 1.5
            self.recognizer.pause_threshold = 0.8  # Shorter pause for responsiveness
            self.recognizer.operation_timeout = None
            
            logger.info("Enhanced speech recognition initialized")
        except Exception as e:
            logger.error(f"Speech recognition init error: {e}")
            self.available = False
    
    def calibrate(self):
        """Calibrate microphone for ambient noise"""
        if not self.available:
            return False
        
        try:
            import speech_recognition as sr
            with self.microphone as source:
                logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                self.calibrated = True
                logger.info(f"Calibration complete. Energy threshold: {self.recognizer.energy_threshold}")
                return True
        except Exception as e:
            logger.error(f"Microphone calibration error: {e}")
            return False
    
    def listen_for_wake_word(self, wake_words=None):
        """Listen for wake words (always listening mode)"""
        if wake_words is None:
            wake_words = ['jarvis', 'hey jarvis', 'okay jarvis']
        
        if not self.available:
            return None
        
        try:
            import speech_recognition as sr
            with self.microphone as source:
                logger.debug("Listening for wake word...")
                audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
            
            text = self.recognizer.recognize_google(audio).lower()
            
            for wake_word in wake_words:
                if wake_word in text:
                    return text
            
            return None
            
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            logger.debug(f"Wake word detection error: {e}")
            return None
    
    def listen(self, timeout=10, phrase_limit=None):
        """Enhanced listening with better error handling and noise rejection"""
        if not self.available:
            return None
        
        if not self.calibrated:
            self.calibrate()
        
        try:
            import speech_recognition as sr
            
            with self.microphone as source:
                logger.debug(f"Listening with timeout={timeout}, phrase_limit={phrase_limit}")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_limit
                )
            
            # Try multiple recognition engines for better accuracy
            text = self._recognize_with_fallback(audio)
            
            if text:
                logger.info(f"Recognized: {text}")
                return text.lower().strip()
            
            return ""
            
        except sr.WaitTimeoutError:
            logger.debug("Speech recognition timeout")
            return None
        except sr.UnknownValueError:
            logger.debug("Speech not understood")
            return ""
        except Exception as e:
            logger.error(f"Speech recognition error: {e}")
            return None
    
    def _recognize_with_fallback(self, audio):
        """Try multiple recognition engines for better accuracy"""
        import speech_recognition as sr
        
        # Primary: Google (most accurate)
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            logger.warning(f"Google recognition service error: {e}")
        
        # Fallback: Google with alternative API key (if available)
        try:
            return self.recognizer.recognize_google_cloud(audio)
        except:
            pass
        
        # Last resort: Sphinx (offline, less accurate but always available)
        try:
            return self.recognizer.recognize_sphinx(audio)
        except:
            pass
        
        return None
    
    def test_microphone(self):
        """Test microphone functionality"""
        if not self.available:
            return False, "Speech recognition not available"
        
        try:
            import speech_recognition as sr
            
            # Test microphone list
            mics = sr.Microphone.list_microphone_names()
            if not mics:
                return False, "No microphones detected"
            
            # Test recording
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=2)
            
            if len(audio.get_raw_data()) == 0:
                return False, "No audio captured"
            
            return True, f"Microphone test successful. {len(mics)} microphone(s) detected."
            
        except Exception as e:
            return False, f"Microphone test failed: {e}"

class SmartCommandProcessor:
    """Enhanced command processing with better pattern matching and context awareness"""
    
    def __init__(self):
        self.command_patterns = {
            'time': [
                r'\b(what\s+time|current\s+time|time\s+is|tell\s+me\s+the\s+time)\b',
                r'\btime\b'
            ],
            'date': [
                r'\b(what\s+date|current\s+date|date\s+is|today\s+is)\b',
                r'\bdate\b'
            ],
            'weather': [
                r'\b(weather|temperature|forecast|climate)\b'
            ],
            'search': [
                r'^(search\s+for|look\s+up|find\s+information\s+about|tell\s+me\s+about)\s+(.+)',
                r'^(what\s+is|who\s+is|where\s+is|when\s+is|how\s+is)\s+(.+)',
                r'^(define|explain|describe)\s+(.+)'
            ],
            'open_website': [
                r'^open\s+(.+)',
                r'^go\s+to\s+(.+)',
                r'^navigate\s+to\s+(.+)'
            ],
            'greeting': [
                r'\b(hello|hi|hey|greetings|good\s+morning|good\s+afternoon|good\s+evening)\b'
            ],
            'thanks': [
                r'\b(thank\s+you|thanks|appreciate|grateful)\b'
            ],
            'status': [
                r'\b(how\s+are\s+you|status|condition|state)\b'
            ],
            'clear': [
                r'\b(clear\s+screen|clear\s+display|clean\s+screen)\b'
            ]
        }
        
        # Compile regex patterns for better performance
        self.compiled_patterns = {}
        for command, patterns in self.command_patterns.items():
            self.compiled_patterns[command] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def classify_command(self, text):
        """Classify command using pattern matching"""
        text = text.strip().lower()
        
        for command, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    # Extract relevant parts from the match
                    groups = match.groups()
                    return command, groups if groups else None
        
        # If no pattern matches, treat as a general query
        return 'general', text
    
    def extract_search_query(self, text, groups=None):
        """Extract search query from text"""
        if groups and len(groups) > 0:
            # Use the captured group as the query
            return groups[-1].strip()
        
        # Fallback: remove common prefixes
        prefixes = [
            'search for', 'look up', 'find information about', 'tell me about',
            'what is', 'who is', 'where is', 'when is', 'how is',
            'define', 'explain', 'describe'
        ]
        
        text_lower = text.lower()
        for prefix in prefixes:
            if text_lower.startswith(prefix):
                return text[len(prefix):].strip()
        
        return text

class EnhancedWebAccess:
    """Enhanced web access with better search capabilities and caching"""
    
    def __init__(self):
        self.available = MODULES['requests']['available'] and MODULES['bs4']['available']
        self.wikipedia_available = MODULES['wikipedia']['available']
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        
        if self.wikipedia_available:
            wikipedia.set_lang("en")
    
    def search_web(self, query):
        """Enhanced web search with caching and multiple sources"""
        # Check cache first
        cache_key = query.lower()
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                return result
        
        result = self._search_web_uncached(query)
        
        # Cache the result
        self.cache[cache_key] = (result, time.time())
        return result
    
    def _search_web_uncached(self, query):
        """Perform actual web search"""
        if not self.available:
            return "Web access is not available. Please install requests and beautifulsoup4."
        
        # Try Wikipedia first for factual information
        if self.wikipedia_available:
            try:
                # Use Wikipedia's search to find the best match
                search_results = wikipedia.search(query, results=3)
                if search_results:
                    try:
                        summary = wikipedia.summary(search_results[0], sentences=3)
                        return f"According to Wikipedia: {summary}"
                    except wikipedia.exceptions.DisambiguationError as e:
                        # Try the first disambiguation option
                        try:
                            summary = wikipedia.summary(e.options[0], sentences=3)
                            return f"According to Wikipedia: {summary}"
                        except:
                            pass
                    except wikipedia.exceptions.PageError:
                        pass
            except Exception as e:
                logger.debug(f"Wikipedia search failed: {e}")
        
        # Fallback to general web search
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            response = requests.get(search_url, headers=headers, timeout=10)
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to extract featured snippet or answer box
            answer_selectors = [
                '.hgKElc',  # Featured snippet
                '.Z0LcW',   # Answer box
                '.BNeawe.s3v9rd.AP7Wnd',  # Search result snippet
                '.BNeawe.vvjwJb.AP7Wnd'   # Alternative snippet
            ]
            
            for selector in answer_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) > 10:  # Minimum meaningful length
                        return f"According to web sources: {text}"
            
            return "I found some information about that topic, but couldn't extract a clear answer."
            
        except requests.RequestException as e:
            logger.error(f"Web search request error: {e}")
            return "I encountered a network error while searching for information."
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return "I encountered an error while searching for information."
    
    def open_website(self, site_name):
        """Enhanced website opening with more sites"""
        sites = {
            'google': 'https://www.google.com',
            'youtube': 'https://www.youtube.com',
            'facebook': 'https://www.facebook.com',
            'twitter': 'https://www.twitter.com',
            'x': 'https://www.x.com',
            'github': 'https://www.github.com',
            'wikipedia': 'https://www.wikipedia.org',
            'amazon': 'https://www.amazon.com',
            'netflix': 'https://www.netflix.com',
            'reddit': 'https://www.reddit.com',
            'stackoverflow': 'https://stackoverflow.com',
            'gmail': 'https://mail.google.com',
            'outlook': 'https://outlook.live.com',
            'linkedin': 'https://www.linkedin.com'
        }
        
        site_lower = site_name.lower().strip()
        
        if site_lower in sites:
            webbrowser.open(sites[site_lower])
            return f"Opening {site_name.capitalize()} for you, sir."
        elif site_lower.startswith('http'):
            webbrowser.open(site_lower)
            return f"Opening {site_name} for you, sir."
        else:
            # Try to construct a URL
            url = f"https://www.{site_lower}.com"
            webbrowser.open(url)
            return f"Attempting to open {site_name}, sir."

class EnhancedJarvisAssistant:
    """Enhanced JARVIS with improved speech, better UI, and smarter responses"""
    
    def __init__(self, root):
        self.root = root
        self.setup_window()
        
        # Initialize enhanced components
        self.tts = EnhancedTTS()
        self.speech_recognizer = EnhancedSpeechRecognizer()
        self.web_access = EnhancedWebAccess()
        self.command_processor = SmartCommandProcessor()
        self.init_database()
        
        # State variables
        self.conversation_history = []
        self.is_listening = False
        self.wake_word_listening = False
        self.system_status = "ONLINE"
        
        # Create enhanced GUI
        self.create_gui()
        
        # Message queue with priority
        self.message_queue = queue.PriorityQueue()
        self.process_message_queue()
        
        # Start with calibration and welcome
        self.initialize_system()
    
    def initialize_system(self):
        """Initialize system with proper setup"""
        # Test and calibrate microphone
        if self.speech_recognizer.available:
            success, message = self.speech_recognizer.test_microphone()
            if success:
                self.add_message("SYSTEM", f"Microphone test passed. {message}", priority=1)
                if self.speech_recognizer.calibrate():
                    self.add_message("SYSTEM", "Microphone calibrated successfully.", priority=1)
                else:
                    self.add_message("SYSTEM", "Microphone calibration failed.", priority=1)
            else:
                self.add_message("SYSTEM", f"Microphone test failed: {message}", priority=1)
        
        # Welcome message
        self.welcome_message()
    
    def setup_window(self):
        """Enhanced window setup with better styling"""
        self.root.title("J.A.R.V.I.S. - Enhanced AI Assistant")
        self.root.geometry("900x700")
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"900x700+{x}+{y}")
        
        # Configure styles
        self.configure_styles()
        
        # Make window resizable
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Set minimum size
        self.root.minsize(600, 500)
    
    def configure_styles(self):
        """Enhanced style configuration"""
        style = ttk.Style()
        
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        
        # Enhanced styles
        style.configure('TFrame', background=COLORS['bg_dark'])
        style.configure('TLabel', background=COLORS['bg_dark'], 
                       foreground=COLORS['text_primary'], font=FONTS['body'])
        style.configure('Title.TLabel', font=FONTS['title'], 
                       foreground=COLORS['accent'])
        style.configure('Status.TLabel', font=FONTS['small'], 
                       foreground=COLORS['text_secondary'])
        style.configure('SystemInfo.TLabel', font=FONTS['micro'], 
                       foreground=COLORS['system'])
        style.configure('TEntry', fieldbackground=COLORS['bg_light'],
                       foreground=COLORS['text_primary'], borderwidth=1)
        style.configure('TScrollbar', background=COLORS['bg_light'],
                       troughcolor=COLORS['bg_dark'], borderwidth=0)
        
        # Button styles
        style.configure('Accent.TButton', background=COLORS['accent'], 
                       foreground=COLORS['bg_dark'])
        style.configure('Danger.TButton', background=COLORS['error'])
        style.configure('Success.TButton', background=COLORS['success'])
    
    def init_database(self):
        """Enhanced database initialization with better schema"""
        try:
            os.makedirs("data", exist_ok=True)
            self.conn = sqlite3.connect("data/jarvis_enhanced.db", check_same_thread=False)
            self.cursor = self.conn.cursor()
            
            # Create enhanced schema
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    speaker TEXT,
                    message TEXT,
                    message_type TEXT DEFAULT 'text',
                    confidence REAL DEFAULT 1.0,
                    processing_time REAL DEFAULT 0.0
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    level TEXT,
                    component TEXT,
                    message TEXT
                )
            ''')
            
            self.conn.commit()
            logger.info("Enhanced database initialized")
        except Exception as e:
            logger.error(f"Database init error: {e}")
            self.conn = None
            self.cursor = None
    
    def create_gui(self):
        """Create enhanced GUI with modern design"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Enhanced header
        self.create_header(main_frame)
        
        # Status bar
        self.create_status_bar(main_frame)
        
        # Enhanced chat area
        self.create_chat_area(main_frame)
        
        # Enhanced input area
        self.create_input_area(main_frame)
    
    def create_header(self, parent):
        """Create enhanced header with system info"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header_frame.columnconfigure(1, weight=1)
        
        # Title section
        title_frame = ttk.Frame(header_frame)
        title_frame.grid(row=0, column=0, sticky="w")
        
        title = ttk.Label(title_frame, text="J.A.R.V.I.S.", style="Title.TLabel")
        title.pack(side=tk.LEFT)
        
        subtitle = ttk.Label(title_frame, text="Enhanced AI Assistant", 
                           font=FONTS['small'], foreground=COLORS['text_secondary'])
        subtitle.pack(side=tk.LEFT, padx=(10, 0))
        
        # Status section
        status_frame = ttk.Frame(header_frame)
        status_frame.grid(row=0, column=1, sticky="e")
        
        self.status_indicator = ttk.Label(status_frame, text="● ONLINE", 
                                        foreground=COLORS['success'], font=FONTS['small'])
        self.status_indicator.pack(side=tk.RIGHT)
    
    def create_status_bar(self, parent):
        """Create system status bar with component status"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        # Component status indicators
        components_frame = ttk.Frame(status_frame)
        components_frame.grid(row=0, column=0, sticky="w")
        
        # TTS Status
        tts_status = "●" if self.tts.available else "○"
        tts_color = COLORS['success'] if self.tts.available else COLORS['error']
        self.tts_status_label = ttk.Label(components_frame, 
                                        text=f"{tts_status} TTS", 
                                        foreground=tts_color, font=FONTS['micro'])
        self.tts_status_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Speech Recognition Status
        sr_status = "●" if self.speech_recognizer.available else "○"
        sr_color = COLORS['success'] if self.speech_recognizer.available else COLORS['error']
        self.sr_status_label = ttk.Label(components_frame, 
                                       text=f"{sr_status} Speech", 
                                       foreground=sr_color, font=FONTS['micro'])
        self.sr_status_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Web Access Status
        web_status = "●" if self.web_access.available else "○"
        web_color = COLORS['success'] if self.web_access.available else COLORS['error']
        self.web_status_label = ttk.Label(components_frame, 
                                        text=f"{web_status} Web", 
                                        foreground=web_color, font=FONTS['micro'])
        self.web_status_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # AI Status (if Ollama is available)
        if MODULES['ollama']['available']:
            ai_status = "●"
            ai_color = COLORS['success']
        else:
            ai_status = "○"
            ai_color = COLORS['error']
        
        self.ai_status_label = ttk.Label(components_frame, 
                                       text=f"{ai_status} Local AI", 
                                       foreground=ai_color, font=FONTS['micro'])
        self.ai_status_label.pack(side=tk.LEFT, padx=(0, 15))
    
    def create_chat_area(self, parent):
        """Create enhanced chat area with better formatting"""
        chat_frame = ttk.Frame(parent)
        chat_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 15))
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)
        
        # Chat area with enhanced styling
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, width=70, height=20,
            bg=COLORS['bg_medium'], fg=COLORS['text_primary'], 
            font=FONTS['monospace'],
            insertbackground=COLORS['accent'], 
            relief=tk.FLAT, 
            borderwidth=0,
            padx=20,
            pady=20,
            selectbackground=COLORS['bg_light']
        )
        self.chat_area.grid(row=0, column=0, sticky="nsew")
        self.chat_area.config(state=tk.DISABLED)
        
        # Configure enhanced text tags
        self.configure_chat_tags()
    
    def configure_chat_tags(self):
        """Configure enhanced text tags for better formatting"""
        # Timestamp tags
        self.chat_area.tag_config("timestamp", foreground=COLORS['text_secondary'], 
                                font=FONTS['micro'])
        
        # Speaker tags
        self.chat_area.tag_config("jarvis_sender", foreground=COLORS['accent'], 
                                font=(FONTS['monospace'][0], FONTS['monospace'][1], 'bold'))
        self.chat_area.tag_config("thinking_sender", foreground=COLORS['ai_thinking'], 
                                font=(FONTS['monospace'][0], FONTS['monospace'][1], 'italic'))
        self.chat_area.tag_config("user_sender", foreground=COLORS['success'], 
                                font=(FONTS['monospace'][0], FONTS['monospace'][1], 'bold'))
        self.chat_area.tag_config("voice_sender", foreground=COLORS['voice_active'], 
                                font=(FONTS['monospace'][0], FONTS['monospace'][1], 'bold'))
        self.chat_area.tag_config("system_sender", foreground=COLORS['warning'], 
                                font=(FONTS['monospace'][0], FONTS['monospace'][1], 'bold'))
        
        # Message content tags
        self.chat_area.tag_config("jarvis_message", foreground=COLORS['text_primary'])
        self.chat_area.tag_config("user_message", foreground=COLORS['text_primary'])
        self.chat_area.tag_config("system_message", foreground=COLORS['text_secondary'])
        self.chat_area.tag_config("error_message", foreground=COLORS['error'])
        
        # Special formatting
        self.chat_area.tag_config("highlight", background=COLORS['bg_light'], 
                                foreground=COLORS['accent'])
    
    def create_input_area(self, parent):
        """Create enhanced input area with voice controls"""
        input_frame = ttk.Frame(parent)
        input_frame.grid(row=3, column=0, sticky="ew")
        input_frame.columnconfigure(1, weight=1)
        
        # Voice status indicator
        self.voice_indicator = ttk.Label(input_frame, text="○", 
                                       foreground=COLORS['text_secondary'], 
                                       font=("Arial", 16))
        self.voice_indicator.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        # Enhanced input field
        self.text_input = ttk.Entry(input_frame, font=FONTS['body'])
        self.text_input.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.text_input.bind('<Return>', self.handle_text_input)
        self.text_input.bind('<Control-Return>', lambda e: self.handle_text_input(e, interrupt_speech=True))
        
        # Button group
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=0, column=2, sticky="e")
        
        # Send button
        self.send_btn = ttk.Button(button_frame, text="Send", 
                                 command=self.handle_text_input,
                                 style="Accent.TButton")
        self.send_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Voice button with enhanced functionality
        self.mic_btn = ttk.Button(button_frame, text="🎤", width=4,
                                command=self.toggle_listening)
        self.mic_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Stop speech button
        self.stop_btn = ttk.Button(button_frame, text="⏹", width=4,
                                 command=self.stop_all_audio,
                                 style="Danger.TButton")
        self.stop_btn.pack(side=tk.LEFT)
        
        # Keyboard shortcuts info
        shortcut_label = ttk.Label(input_frame, 
                                 text="Enter: Send | Ctrl+Enter: Send & Interrupt | Esc: Stop Audio",
                                 font=FONTS['micro'], foreground=COLORS['text_secondary'])
        shortcut_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))
        
        # Bind keyboard shortcuts
        self.root.bind('<Escape>', lambda e: self.stop_all_audio())
        self.text_input.focus()
    
    def toggle_listening(self):
        """Enhanced listening toggle with visual feedback"""
        if not self.speech_recognizer.available:
            self.add_message("SYSTEM", "Speech recognition is not available", priority=1)
            return
            
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """Enhanced listening with better feedback"""
        self.is_listening = True
        self.update_voice_indicator("listening")
        self.mic_btn.config(text="🔴")
        self.status_indicator.config(text="● LISTENING", foreground=COLORS['listening'])
        
        # Add system message
        self.add_message("SYSTEM", "Listening for your command...", priority=1)
        
        # Start listening in a separate thread
        threading.Thread(target=self.enhanced_listen_thread, daemon=True).start()
    
    def stop_listening(self):
        """Stop listening with proper cleanup"""
        self.is_listening = False
        self.update_voice_indicator("idle")
        self.mic_btn.config(text="🎤")
        self.status_indicator.config(text="● ONLINE", foreground=COLORS['success'])
        
        self.add_message("SYSTEM", "Stopped listening", priority=1)
    
    def stop_all_audio(self):
        """Stop all audio operations"""
        self.stop_listening()
        self.tts.stop_speaking()
        self.add_message("SYSTEM", "All audio operations stopped", priority=1)
    
    def update_voice_indicator(self, state):
        """Update voice status indicator"""
        indicators = {
            'idle': ("○", COLORS['text_secondary']),
            'listening': ("●", COLORS['listening']),
            'processing': ("◐", COLORS['ai_thinking']),
            'speaking': ("♪", COLORS['voice_active'])
        }
        
        if state in indicators:
            symbol, color = indicators[state]
            self.voice_indicator.config(text=symbol, foreground=color)
    
    def enhanced_listen_thread(self):
        """Enhanced listening thread with better error handling"""
        start_time = time.time()
        
        try:
            while self.is_listening:
                # Update processing indicator
                self.root.after(0, lambda: self.update_voice_indicator("processing"))
                
                # Listen for speech
                text = self.speech_recognizer.listen(timeout=10, phrase_limit=10)
                
                processing_time = time.time() - start_time
                
                if not self.is_listening:  # Check if listening was stopped
                    break
                
                if text is None:
                    # Timeout - continue listening
                    self.root.after(0, lambda: self.update_voice_indicator("listening"))
                    continue
                    
                if text == "":
                    # Speech detected but not understood
                    self.root.after(0, lambda: self.add_message("SYSTEM", 
                        "I heard something but couldn't understand it. Please try again.", priority=1))
                    self.root.after(0, lambda: self.update_voice_indicator("listening"))
                    continue
                
                # Process the recognized text
                self.root.after(0, lambda t=text, pt=processing_time: 
                              self.process_voice_input(t, pt))
                
                # Stop listening after successful recognition (single command mode)
                self.root.after(0, self.stop_listening)
                break
                
        except Exception as e:
            logger.error(f"Enhanced listen thread error: {e}")
            self.root.after(0, lambda: self.add_message("SYSTEM", 
                f"Speech recognition error: {str(e)}", priority=1))
            self.root.after(0, self.stop_listening)
    
    def process_voice_input(self, text, processing_time=0.0):
        """Process voice input with enhanced feedback"""
        self.add_message("YOU (Voice)", text, priority=2)
        self.save_conversation("YOU", text, "voice", processing_time=processing_time)
        
        # Show processing indicator
        self.update_voice_indicator("processing")
        
        # Process command
        self.process_command(text)
    
    def handle_text_input(self, event=None, interrupt_speech=False):
        """Enhanced text input handling"""
        text = self.text_input.get().strip()
        if not text:
            return
        
        self.text_input.delete(0, tk.END)
        
        # Interrupt speech if requested
        if interrupt_speech:
            self.tts.stop_speaking()
        
        self.add_message("YOU", text, priority=2)
        self.save_conversation("YOU", text, "text")
        self.process_command(text)
        
        # Return focus to input
        self.text_input.focus()
    
    def process_command(self, command):
        """Enhanced command processing with smart classification"""
        start_time = time.time()
        
        # Classify the command
        command_type, extracted_data = self.command_processor.classify_command(command)
        
        # Process based on command type
        if command_type == 'time':
            self.handle_time_command()
        elif command_type == 'date':
            self.handle_date_command()
        elif command_type == 'weather':
            self.handle_weather_command(command)
        elif command_type == 'search':
            query = self.command_processor.extract_search_query(command, extracted_data)
            self.handle_search_command(query)
        elif command_type == 'open_website':
            if extracted_data:
                site = extracted_data[0] if isinstance(extracted_data, tuple) else extracted_data
                self.handle_open_website(site)
        elif command_type == 'greeting':
            self.handle_greeting()
        elif command_type == 'thanks':
            self.handle_thanks()
        elif command_type == 'status':
            self.handle_status_query()
        elif command_type == 'clear':
            self.handle_clear_screen()
        else:
            # General query - use AI or provide helpful response
            self.handle_general_query(command)
        
        # Log processing time
        processing_time = time.time() - start_time
        logger.debug(f"Command processed in {processing_time:.2f}s")
    
    def handle_time_command(self):
        """Handle time-related commands"""
        current_time = datetime.now()
        time_str = current_time.strftime("%I:%M %p")
        date_str = current_time.strftime("%A, %B %d")
        
        response = f"The current time is {time_str} on {date_str}, sir."
        self.add_jarvis_response(response)
    
    def handle_date_command(self):
        """Handle date-related commands"""
        current_date = datetime.now()
        date_str = current_date.strftime("%A, %B %d, %Y")
        
        response = f"Today is {date_str}, sir."
        self.add_jarvis_response(response)
    
    def handle_weather_command(self, command):
        """Handle weather-related commands"""
        self.add_message("JARVIS", "Checking weather information...", priority=1)
        
        # Extract location if mentioned
        location_match = re.search(r'\bin\s+(\w+(?:\s+\w+)*)', command.lower())
        if location_match:
            location = location_match.group(1)
            query = f"weather in {location}"
        else:
            query = "current weather"
        
        result = self.web_access.search_web(query)
        self.add_jarvis_response(result)
    
    def handle_search_command(self, query):
        """Handle search commands with better feedback"""
        if not query:
            self.add_jarvis_response("I'm not sure what you'd like me to search for, sir.")
            return
        
        self.add_message("JARVIS", f"Searching for information about '{query}'...", priority=1)
        
        # Perform web search
        def search_thread():
            result = self.web_access.search_web(query)
            self.root.after(0, lambda: self.add_jarvis_response(result))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def handle_open_website(self, site):
        """Handle website opening commands"""
        if not site:
            self.add_jarvis_response("I'm not sure which website you'd like me to open, sir.")
            return
        
        result = self.web_access.open_website(site)
        self.add_jarvis_response(result)
    
    def handle_greeting(self):
        """Handle greeting commands with varied responses"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            time_greeting = "Good morning"
        elif 12 <= current_hour < 17:
            time_greeting = "Good afternoon"
        elif 17 <= current_hour < 21:
            time_greeting = "Good evening"
        else:
            time_greeting = "Good evening"
        
        greetings = [
            f"{time_greeting}, sir. How may I assist you today?",
            f"{time_greeting}. What can I do for you, sir?",
            f"Hello, sir. {time_greeting}. How may I be of service?",
            f"{time_greeting}, sir. I'm ready to help with whatever you need."
        ]
        
        self.add_jarvis_response(random.choice(greetings))
    
    def handle_thanks(self):
        """Handle thank you responses"""
        responses = [
            "You're most welcome, sir.",
            "Always a pleasure to assist, sir.",
            "Happy to help, sir. Is there anything else?",
            "At your service, sir.",
            "My pleasure, sir. What else can I do for you?"
        ]
        
        self.add_jarvis_response(random.choice(responses))
    
    def handle_status_query(self):
        """Handle status/how are you queries"""
        # Generate system status
        components = []
        if self.tts.available:
            components.append("voice synthesis online")
        if self.speech_recognizer.available:
            components.append("speech recognition active")
        if self.web_access.available:
            components.append("web access operational")
        
        if components:
            status_text = ", ".join(components[:-1])
            if len(components) > 1:
                status_text += f", and {components[-1]}"
            else:
                status_text = components[0]
        else:
            status_text = "basic systems operational"
        
        responses = [
            f"All systems are functioning optimally, sir. I have {status_text}.",
            f"Operating at full capacity, sir. Currently running with {status_text}.",
            f"Systems are running smoothly, sir. {status_text.capitalize()}.",
        ]
        
        self.add_jarvis_response(random.choice(responses))
    
    def handle_clear_screen(self):
        """Handle screen clearing commands"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state=tk.DISABLED)
        self.add_jarvis_response("Display cleared, sir.")
    
    def handle_general_query(self, query):
        """Handle general queries with intelligent responses"""
        # Check if Ollama is available for intelligent responses
        if MODULES['ollama']['available']:
            self.handle_ai_query(query)
        else:
            # Provide helpful fallback responses
            fallback_responses = [
                "I understand you're asking about that topic, sir. Perhaps try a web search for more detailed information?",
                "That's an interesting question, sir. I'd recommend searching the web for comprehensive information on that subject.",
                "I'd be happy to help you find information about that, sir. Shall I perform a web search?",
                "For detailed information on that topic, sir, I suggest we search the web together.",
            ]
            
            response = random.choice(fallback_responses)
            self.add_jarvis_response(response)
    
    def handle_ai_query(self, query):
        """Handle queries using local AI (Ollama)"""
        self.add_message("JARVIS", "Processing your query with AI...", priority=1, thinking=True)
        self.update_voice_indicator("processing")
        
        def ai_thread():
            try:
                # Create context for AI
                context = """You are JARVIS, an advanced AI assistant with a sophisticated British personality. 
                You are helpful, efficient, and polite. Always address the user as 'sir' or 'madam' as appropriate.
                Provide concise but comprehensive responses. You have access to various systems and can help with
                information queries, system operations, and general assistance."""
                
                # Add conversation context
                if self.conversation_history:
                    context += "\n\nRecent conversation context:\n"
                    for msg in self.conversation_history[-3:]:  # Last 3 messages for context
                        context += f"{msg['speaker']}: {msg['message']}\n"
                
                response = ollama.chat(
                    model='llama3',
                    messages=[
                        {'role': 'system', 'content': context},
                        {'role': 'user', 'content': query}
                    ]
                )
                
                ai_response = response['message']['content']
                
                # Update UI in main thread
                self.root.after(0, lambda: self.add_jarvis_response(ai_response))
                self.root.after(0, lambda: self.update_voice_indicator("idle"))
                
            except Exception as e:
                logger.error(f"AI query error: {e}")
                error_response = f"I encountered an error while processing your query, sir: {str(e)}"
                self.root.after(0, lambda: self.add_jarvis_response(error_response))
                self.root.after(0, lambda: self.update_voice_indicator("idle"))
        
        threading.Thread(target=ai_thread, daemon=True).start()
    
    def add_jarvis_response(self, response):
        """Add JARVIS response with enhanced TTS"""
        self.add_message("JARVIS", response, priority=2)
        self.save_conversation("JARVIS", response, "text")
        
        # Update voice indicator and speak
        self.update_voice_indicator("speaking")
        if self.tts.available:
            self.tts.speak(response)
            
            # Reset voice indicator after speaking
            def reset_indicator():
                time.sleep(1)  # Wait a bit to ensure speaking started
                while self.tts.is_speaking():
                    time.sleep(0.5)
                self.root.after(0, lambda: self.update_voice_indicator("idle"))
            
            threading.Thread(target=reset_indicator, daemon=True).start()
    
    def add_message(self, sender, message, priority=3, thinking=False):
        """Add message to display queue with priority"""
        timestamp = datetime.now()
        self.message_queue.put((priority, timestamp, sender, message, thinking))
    
    def process_message_queue(self):
        """Enhanced message queue processing with priority"""
        try:
            while True:
                priority, timestamp, sender, message, thinking = self.message_queue.get_nowait()
                
                self.chat_area.config(state=tk.NORMAL)
                
                # Format timestamp
                time_str = timestamp.strftime("%H:%M:%S")
                
                # Add timestamp
                self.chat_area.insert(tk.END, f"[{time_str}] ", "timestamp")
                
                # Add sender with appropriate styling
                sender_tag = self.get_sender_tag(sender, thinking)
                self.chat_area.insert(tk.END, f"{sender}: ", sender_tag)
                
                # Add message content
                message_tag = self.get_message_tag(sender)
                self.chat_area.insert(tk.END, f"{message}\n\n", message_tag)
                
                self.chat_area.config(state=tk.DISABLED)
                self.chat_area.see(tk.END)
                
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_message_queue)
    
    def get_sender_tag(self, sender, thinking=False):
        """Get appropriate tag for sender"""
        if thinking:
            return "thinking_sender"
        elif sender == "JARVIS":
            return "jarvis_sender"
        elif sender.startswith("YOU"):
            if "Voice" in sender:
                return "voice_sender"
            else:
                return "user_sender"
        else:
            return "system_sender"
    
    def get_message_tag(self, sender):
        """Get appropriate tag for message content"""
        if sender == "JARVIS":
            return "jarvis_message"
        elif sender.startswith("YOU"):
            return "user_message"
        elif sender == "SYSTEM":
            return "system_message"
        else:
            return "system_message"
    
    def save_conversation(self, speaker, message, message_type="text", confidence=1.0, processing_time=0.0):
        """Enhanced conversation saving with metadata"""
        if self.cursor:
            try:
                timestamp = datetime.now().isoformat()
                self.cursor.execute(
                    "INSERT INTO conversations (timestamp, speaker, message, message_type, confidence, processing_time) VALUES (?, ?, ?, ?, ?, ?)",
                    (timestamp, speaker, message, message_type, confidence, processing_time)
                )
                self.conn.commit()
            except Exception as e:
                logger.error(f"Database save error: {e}")
        
        # Keep in memory with enhanced structure
        self.conversation_history.append({
            "speaker": speaker, 
            "message": message, 
            "timestamp": datetime.now(),
            "type": message_type
        })
        
        # Maintain reasonable history size
        if len(self.conversation_history) > 50:
            self.conversation_history.pop(0)
    
    def welcome_message(self):
        """Enhanced welcome message with system status"""
        current_time = datetime.now()
        if 5 <= current_time.hour < 12:
            greeting = "Good morning"
        elif 12 <= current_time.hour < 17:
            greeting = "Good afternoon"
        elif 17 <= current_time.hour < 21:
            greeting = "Good evening"
        else:
            greeting = "Good evening"
        
        welcome_msg = f"{greeting}, sir. JARVIS Enhanced systems are now online.\n\n"
        
        # System capabilities report
        capabilities = []
        if self.tts.available:
            capabilities.append("✓ Advanced voice synthesis")
        else:
            capabilities.append("✗ Voice synthesis unavailable")
            
        if self.speech_recognizer.available:
            capabilities.append("✓ Enhanced speech recognition")
        else:
            capabilities.append("✗ Speech recognition unavailable")
            
        if self.web_access.available:
            capabilities.append("✓ Web access and search")
        else:
            capabilities.append("✗ Web access unavailable")
            
        if MODULES['ollama']['available']:
            capabilities.append("✓ Local AI intelligence")
        else:
            capabilities.append("✗ Local AI unavailable")
        
        welcome_msg += "System Status:\n" + "\n".join(capabilities) + "\n\n"
        welcome_msg += "I'm ready to assist you with information, web searches, system operations, and general inquiries. How may I help you today?"
        
        self.add_message("JARVIS", welcome_msg, priority=1)
        
        # Speak welcome message
        if self.tts.available:
            spoken_welcome = f"{greeting}, sir. JARVIS Enhanced systems are now online and ready to assist. How may I help you today?"
            self.tts.speak(spoken_welcome)
    
    def cleanup_and_exit(self):
        """Enhanced cleanup with proper resource management"""
        logger.info("Shutting down JARVIS Enhanced...")
        
        # Stop all operations
        self.is_listening = False
        self.wake_word_listening = False
        
        # Stop TTS
        if self.tts:
            self.tts.stop_speaking()
        
        # Close database connection
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        
        # Cleanup audio files
        if hasattr(self, 'tts') and self.tts:
            self.tts.audio_manager.cleanup_temp_files()
        
        # Log shutdown
        logger.info("JARVIS Enhanced shutdown complete")
        
        self.root.quit()

def main():
    """Enhanced main application entry point with better error handling"""
    try:
        print("=" * 60)
        print("Starting JARVIS Enhanced AI Assistant...")
        print("=" * 60)
        
        # System information
        print(f"Python version: {sys.version}")
        print(f"Operating system: {os.name}")
        
        # Check module availability
        print("\nModule Status:")
        for module, info in MODULES.items():
            status = "✓" if info['available'] else "✗"
            version = f" (v{info['version']})" if info['version'] else ""
            print(f"  {status} {module}{version}")
        
        # Installation suggestions for missing modules
        missing_modules = [module for module, info in MODULES.items() if not info['available']]
        if missing_modules:
            print("\nTo enable additional features, install these packages:")
            installation_commands = {
                'gtts': 'pip install gtts',
                'pygame': 'pip install pygame',
                'speech_recognition': 'pip install SpeechRecognition pyaudio',
                'requests': 'pip install requests',
                'bs4': 'pip install beautifulsoup4',
                'wikipedia': 'pip install wikipedia',
                'ollama': 'pip install ollama',
                'pydub': 'pip install pydub',
                'pyaudio': 'pip install pyaudio'
            }
            
            for module in missing_modules:
                if module in installation_commands:
                    print(f"  {installation_commands[module]}")
            
            if 'ollama' in missing_modules:
                print("\nFor Local AI features:")
                print("  1. Install Ollama from https://ollama.ai/")
                print("  2. Run: ollama pull llama3")
        
        print("\n" + "=" * 60)
        print("Initializing GUI...")
        
        # Start enhanced GUI
        root = tk.Tk()
        app = EnhancedJarvisAssistant(root)
        root.protocol("WM_DELETE_WINDOW", app.cleanup_and_exit)
        
        print("JARVIS Enhanced GUI started successfully!")
        print("Ready for operation.")
        print("=" * 60)
        
        root.mainloop()
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user.")
        logger.info("JARVIS shutdown requested by user")
    except Exception as e:
        import traceback
        error_msg = f"JARVIS Enhanced startup error: {e}\n\nFull traceback:\n{traceback.format_exc()}"
        print(error_msg)
        logger.error(error_msg)
        
        try:
            messagebox.showerror("JARVIS Enhanced Error", 
                               f"Failed to start JARVIS Enhanced:\n\n{str(e)}\n\nCheck jarvis.log for details.")
        except:
            pass
        
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()