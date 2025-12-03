"""
Local AI Engine - Works without API keys
Enhanced rule-based responses with better intelligence
"""

import random
from datetime import datetime
import re

class LocalAI:
    """Enhanced local AI that works without API keys"""
    
    def __init__(self):
        self.conversation_history = []
    
    def chat(self, message: str) -> str:
        """Generate intelligent response based on message"""
        message_lower = message.lower()
        
        # Greeting detection
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'aura', 'namaste']):
            return random.choice([
                "Hello! I'm AURA, your AI assistant. How can I help you?",
                "Hi there! AURA at your service.",
                "Namaste! What can I do for you today?",
                "Hey! Ready to assist you."
            ])
        
        # Time detection
        if any(word in message_lower for word in ['time', 'clock', 'kitna baja']):
            return f"The current time is {datetime.now().strftime('%I:%M %p')}"
        
        # Date detection
        if any(word in message_lower for word in ['date', 'today', 'day', 'tarikh']):
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
        
        # Math detection
        if any(op in message_lower for op in ['+', '-', '*', '/', 'plus', 'minus']):
            try:
                numbers = re.findall(r'\d+', message)
                if len(numbers) >= 2:
                    a, b = int(numbers[0]), int(numbers[1])
                    if '+' in message or 'plus' in message_lower:
                        return f"{a} + {b} = {a + b}"
                    elif '-' in message or 'minus' in message_lower:
                        return f"{a} - {b} = {a - b}"
            except:
                pass
        
        # Joke detection
        if any(word in message_lower for word in ['joke', 'funny', 'mazak']):
            return "Why don't programmers like nature? It has too many bugs! 😄"
        
        # Help detection
        if any(word in message_lower for word in ['help', 'capabilities']):
            return "I can help with voice commands, automation, screen analysis, and more!"
        
        # Default response
        return f"I understand. How can I assist you with: '{message}'?"
