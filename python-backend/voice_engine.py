"""
Voice Engine for AURA
Speech Recognition + Text-to-Speech
"""

import os
import threading
import logging
from typing import Optional, Callable
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class VoiceEngine:
    """Voice Engine for speech recognition and text-to-speech"""
    
    def __init__(self):
        """Initialize Voice Engine"""
        self.is_listening = False
        self.wake_word_active = False
        self.wake_word = os.getenv('WAKE_WORD', 'aura').lower()
        self.listen_thread = None
        self.wake_word_thread = None
        
        # Initialize speech recognition
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            self.sr_available = True
            logger.info("Speech recognition initialized successfully")
            
        except Exception as e:
            logger.warning(f"Speech recognition not available: {e}")
            self.sr_available = False
            self.recognizer = None
            self.microphone = None
        
        # Initialize text-to-speech
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS
            self.tts_engine.setProperty('rate', int(os.getenv('TTS_RATE', '180')))
            self.tts_engine.setProperty('volume', float(os.getenv('TTS_VOLUME', '0.9')))
            
            self.tts_available = True
            logger.info("Text-to-speech initialized successfully")
            
        except Exception as e:
            logger.warning(f"Text-to-speech not available: {e}")
            self.tts_available = False
            self.tts_engine = None

    def start_listening(self) -> dict:
        """Start listening for voice input"""
        try:
            if not self.sr_available:
                return {
                    "success": False,
                    "error": "Speech recognition not available. Install: pip install SpeechRecognition pyaudio"
                }
            
            if self.is_listening:
                return {
                    "success": False,
                    "error": "Already listening"
                }
            
            self.is_listening = True
            logger.info("Voice listening started")
            
            return {
                "success": True,
                "message": "Listening started"
            }
            
        except Exception as e:
            logger.error(f"Error starting listening: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def stop_listening(self) -> dict:
        """Stop listening for voice input"""
        try:
            self.is_listening = False
            logger.info("Voice listening stopped")
            
            return {
                "success": True,
                "message": "Listening stopped"
            }
            
        except Exception as e:
            logger.error(f"Error stopping listening: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 10) -> dict:
        """Listen for a single voice command"""
        try:
            if not self.sr_available:
                return {
                    "success": False,
                    "error": "Speech recognition not available"
                }
            
            import speech_recognition as sr
            
            with self.microphone as source:
                logger.info("Listening for voice input...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            # Recognize speech using Google Speech Recognition
            logger.info("Recognizing speech...")
            text = self.recognizer.recognize_google(audio)
            
            logger.info(f"Recognized: {text}")
            
            return {
                "success": True,
                "text": text,
                "confidence": 1.0
            }
            
        except sr.WaitTimeoutError:
            logger.warning("Timeout - no speech detected")
            return {
                "success": False,
                "error": "Timeout - no speech detected"
            }
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return {
                "success": False,
                "error": "Could not understand audio"
            }
        except sr.RequestError as e:
            logger.error(f"Recognition service error: {e}")
            return {
                "success": False,
                "error": f"Recognition service error: {e}"
            }
        except Exception as e:
            logger.error(f"Error during speech recognition: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def start_wake_word_detection(self, callback: Optional[Callable] = None) -> dict:
        """Start wake word detection in background thread"""
        try:
            if not self.sr_available:
                return {
                    "success": False,
                    "error": "Speech recognition not available"
                }
            
            if self.wake_word_active:
                return {
                    "success": False,
                    "error": "Wake word detection already active"
                }
            
            self.wake_word_active = True
            
            def wake_word_loop():
                """Background loop for wake word detection"""
                import speech_recognition as sr
                
                logger.info(f"Wake word detection started. Listening for '{self.wake_word}'...")
                
                while self.wake_word_active:
                    try:
                        with self.microphone as source:
                            audio = self.recognizer.listen(
                                source,
                                timeout=2,
                                phrase_time_limit=3
                            )
                        
                        text = self.recognizer.recognize_google(audio).lower()
                        logger.debug(f"Heard: {text}")
                        
                        if self.wake_word in text:
                            logger.info(f"Wake word '{self.wake_word}' detected!")
                            
                            if callback:
                                callback({
                                    "detected": True,
                                    "text": text,
                                    "wake_word": self.wake_word
                                })
                            
                            # Optional: speak confirmation
                            self.speak("Yes?")
                            
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except Exception as e:
                        logger.debug(f"Wake word detection error: {e}")
                        continue
                
                logger.info("Wake word detection stopped")
            
            # Start background thread
            self.wake_word_thread = threading.Thread(
                target=wake_word_loop,
                daemon=True
            )
            self.wake_word_thread.start()
            
            return {
                "success": True,
                "message": f"Wake word detection started for '{self.wake_word}'"
            }
            
        except Exception as e:
            logger.error(f"Error starting wake word detection: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def stop_wake_word_detection(self) -> dict:
        """Stop wake word detection"""
        try:
            self.wake_word_active = False
            logger.info("Wake word detection stopped")
            
            return {
                "success": True,
                "message": "Wake word detection stopped"
            }
            
        except Exception as e:
            logger.error(f"Error stopping wake word detection: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def speak(self, text: str) -> dict:
        """Text-to-speech output"""
        try:
            if not self.tts_available:
                logger.warning(f"TTS not available. Would speak: {text}")
                return {
                    "success": False,
                    "error": "Text-to-speech not available. Install: pip install pyttsx3"
                }
            
            def speak_thread():
                """Background thread for TTS"""
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except Exception as e:
                    logger.error(f"TTS error: {e}")
            
            # Run TTS in background thread
            thread = threading.Thread(target=speak_thread, daemon=True)
            thread.start()
            
            logger.info(f"Speaking: {text[:50]}...")
            
            return {
                "success": True,
                "message": "Speaking text"
            }
            
        except Exception as e:
            logger.error(f"Error in speak: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def process_audio(self, audio_data: bytes) -> dict:
        """Process raw audio data (for future streaming support)"""
        try:
            # Placeholder for audio processing
            logger.info("Processing audio data...")
            
            return {
                "success": True,
                "message": "Audio processing not yet implemented"
            }
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_status(self) -> dict:
        """Get voice engine status"""
        return {
            "speech_recognition_available": self.sr_available,
            "text_to_speech_available": self.tts_available,
            "is_listening": self.is_listening,
            "wake_word_active": self.wake_word_active,
            "wake_word": self.wake_word
        }

    def set_wake_word(self, wake_word: str):
        """Change wake word"""
        self.wake_word = wake_word.lower()
        logger.info(f"Wake word changed to: {self.wake_word}")

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_listening()
            self.stop_wake_word_detection()
            
            if self.tts_engine:
                self.tts_engine.stop()
            
            logger.info("Voice engine cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
