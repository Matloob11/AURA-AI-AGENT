"""
AI Engine for AURA
Universal Multi-Provider AI Integration with automatic fallback
Supports: OpenAI, Hugging Face, Cohere, Gemini, Deepseek
"""

import os
from dotenv import load_dotenv
from datetime import datetime
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import local AI fallback
try:
    from local_ai import LocalAI
    LOCAL_AI_AVAILABLE = True
except:
    LOCAL_AI_AVAILABLE = False


class AIEngine:
    """Universal AI Engine with multi-provider support and automatic fallback"""
    
    def __init__(self):
        """Initialize AI Engine with all available providers"""
        
        # Load API keys from environment
        self.api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'huggingface': os.getenv('HF_API_KEY'),
            'cohere': os.getenv('COHERE_API_KEY'),
            'gemini': os.getenv('GEMINI_API_KEY'),
            'deepseek': os.getenv('DEEPSEEK_API_KEY')
        }
        
        # Initialize provider clients
        self.providers = {}
        self._initialize_providers()
        
        # Determine available providers
        self.available_providers = [name for name, client in self.providers.items() if client is not None]
        
        # Initialize local AI as fallback
        self.local_ai = LocalAI() if LOCAL_AI_AVAILABLE else None
        
        if not self.available_providers:
            if self.local_ai:
                logger.warning("No AI API keys configured. Using LOCAL AI mode.")
                self.available_providers = ['local']
            else:
                logger.warning("No AI API keys configured. Please set at least one API key in .env file.")
        else:
            logger.info(f"Available AI providers: {', '.join(self.available_providers)}")
        
        # Track which provider was used for last request
        self.last_provider_used = None
        self.provider_stats = {name: {'calls': 0, 'errors': 0, 'total_time': 0} for name in self.api_keys.keys()}
        
        # Conversation history
        self.conversation_history = []
        self.max_history = 20  # Keep last 20 messages
        
        # System prompt
        self.system_prompt = """You are AURA, an advanced AI desktop assistant.

Your capabilities:
- Voice command processing
- Screen analysis and vision
- System automation and control
- File operations
- Web searches and information retrieval
- Task automation

Personality:
- Concise and efficient
- Helpful and proactive
- Professional yet friendly
- Action-oriented

Guidelines:
- Keep responses brief (2-3 sentences max unless asked for details)
- Suggest actions when appropriate
- Confirm before executing system commands
- Be clear about your limitations"""

        # Model configuration from environment
        self.model = os.getenv('AI_MODEL', 'gpt-4')
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', '500'))
        
        logger.info(f"AI Engine configured: model={self.model}, temp={self.temperature}")
    
    def _initialize_providers(self):
        """Initialize all available AI provider clients"""
        
        # Deepseek (PRIORITY - FREE & FAST)
        if self.api_keys['deepseek']:
            try:
                from openai import OpenAI
                # Deepseek uses OpenAI-compatible API
                self.providers['deepseek'] = OpenAI(
                    api_key=self.api_keys['deepseek'],
                    base_url="https://api.deepseek.com"
                )
                logger.info("✓ Deepseek client initialized (PRIMARY)")
            except Exception as e:
                logger.warning(f"✗ Deepseek initialization failed: {e}")
                self.providers['deepseek'] = None
        else:
            self.providers['deepseek'] = None
        
        # OpenAI
        if self.api_keys['openai']:
            try:
                from openai import OpenAI
                self.providers['openai'] = OpenAI(api_key=self.api_keys['openai'])
                logger.info("✓ OpenAI client initialized")
            except Exception as e:
                logger.warning(f"✗ OpenAI initialization failed: {e}")
                self.providers['openai'] = None
        else:
            self.providers['openai'] = None
        
        # Hugging Face
        if self.api_keys['huggingface']:
            try:
                import requests
                # Test the API key
                headers = {"Authorization": f"Bearer {self.api_keys['huggingface']}"}
                self.providers['huggingface'] = {'headers': headers, 'session': requests.Session()}
                logger.info("✓ Hugging Face client initialized")
            except Exception as e:
                logger.warning(f"✗ Hugging Face initialization failed: {e}")
                self.providers['huggingface'] = None
        else:
            self.providers['huggingface'] = None
        
        # Cohere
        if self.api_keys['cohere']:
            try:
                import cohere
                self.providers['cohere'] = cohere.Client(self.api_keys['cohere'])
                logger.info("✓ Cohere client initialized")
            except Exception as e:
                logger.warning(f"✗ Cohere initialization failed: {e}")
                self.providers['cohere'] = None
        else:
            self.providers['cohere'] = None
        
        # Google Gemini
        if self.api_keys['gemini']:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_keys['gemini'])
                self.providers['gemini'] = genai
                logger.info("✓ Gemini client initialized")
            except Exception as e:
                logger.warning(f"✗ Gemini initialization failed: {e}")
                self.providers['gemini'] = None
        else:
            self.providers['gemini'] = None

    async def chat(self, user_message: str) -> str:
        """
        Universal chat method with automatic provider fallback
        
        Args:
            user_message: User's input message
            
        Returns:
            AI response string
        """
        # Use local AI if no providers available
        if not self.available_providers or self.available_providers == ['local']:
            if self.local_ai:
                logger.info("Using LOCAL AI (no API keys)")
                response = self.local_ai.chat(user_message)
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            return "AI Engine not configured. Please set at least one API key (OPENAI_API_KEY, HF_API_KEY, COHERE_API_KEY, GEMINI_API_KEY, or DEEPSEEK_API_KEY) in .env file."
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Try each provider in order until one succeeds
        for provider_name in self.available_providers:
            try:
                start_time = time.time()
                logger.info(f"Attempting to use {provider_name.upper()} for chat...")
                
                # Call the appropriate provider
                if provider_name == 'openai':
                    response = await self._chat_openai(user_message)
                elif provider_name == 'huggingface':
                    response = await self._chat_huggingface(user_message)
                elif provider_name == 'cohere':
                    response = await self._chat_cohere(user_message)
                elif provider_name == 'gemini':
                    response = await self._chat_gemini(user_message)
                elif provider_name == 'deepseek':
                    response = await self._chat_deepseek(user_message)
                else:
                    continue
                
                # Success! Track stats
                elapsed_time = time.time() - start_time
                self.provider_stats[provider_name]['calls'] += 1
                self.provider_stats[provider_name]['total_time'] += elapsed_time
                self.last_provider_used = provider_name
                
                # Add AI response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                
                logger.info(f"✓ {provider_name.upper()} responded successfully in {elapsed_time:.2f}s")
                return response
                
            except Exception as e:
                # Log error and try next provider
                self.provider_stats[provider_name]['errors'] += 1
                logger.warning(f"✗ {provider_name.upper()} failed: {str(e)}")
                continue
        
        # All providers failed - use local AI as last resort
        if self.local_ai:
            logger.warning("All API providers failed. Falling back to LOCAL AI.")
            response = self.local_ai.chat(user_message)
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        error_msg = "All AI providers failed. Please check your API keys and network connection."
        logger.error(error_msg)
        
        # Remove the user message from history since we couldn't respond
        if self.conversation_history and self.conversation_history[-1]["role"] == "user":
            self.conversation_history.pop()
        
        return error_msg
    
    async def _chat_openai(self, user_message: str) -> str:
        """Chat using OpenAI API"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history[-self.max_history:]
        ]
        
        response = self.providers['openai'].chat.completions.create(
            model=self.model if self.model.startswith('gpt') else 'gpt-4',
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    async def _chat_huggingface(self, user_message: str) -> str:
        """Chat using Hugging Face Inference API"""
        import requests
        
        # Use a good conversational model
        model = "mistralai/Mistral-7B-Instruct-v0.2"
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        
        # Format conversation for HF
        conversation_text = self.system_prompt + "\n\n"
        for msg in self.conversation_history[-self.max_history:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_text += f"{role}: {msg['content']}\n"
        conversation_text += "Assistant:"
        
        payload = {
            "inputs": conversation_text,
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "return_full_text": False
            }
        }
        
        response = requests.post(
            api_url,
            headers=self.providers['huggingface']['headers'],
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0].get('generated_text', '').strip()
        return str(result)
    
    async def _chat_cohere(self, user_message: str) -> str:
        """Chat using Cohere API"""
        # Format conversation history for Cohere
        chat_history = []
        for msg in self.conversation_history[-self.max_history:-1]:  # Exclude the last user message
            chat_history.append({
                "role": "USER" if msg["role"] == "user" else "CHATBOT",
                "message": msg["content"]
            })
        
        response = self.providers['cohere'].chat(
            message=user_message,
            chat_history=chat_history,
            preamble=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.text
    
    async def _chat_gemini(self, user_message: str) -> str:
        """Chat using Google Gemini API"""
        # Create model (using Gemini 1.5 Flash - free and fast)
        model = self.providers['gemini'].GenerativeModel('models/gemini-1.5-flash')
        
        # Start chat with history
        chat_history = []
        for msg in self.conversation_history[-self.max_history:-1]:  # Exclude the last user message
            chat_history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]]
            })
        
        chat = model.start_chat(history=chat_history)
        
        # Send message
        response = chat.send_message(
            user_message,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            }
        )
        
        return response.text
    
    async def _chat_deepseek(self, user_message: str) -> str:
        """Chat using Deepseek API (OpenAI-compatible)"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history[-self.max_history:]
        ]
        
        response = self.providers['deepseek'].chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_history_count(self) -> int:
        """Get number of messages in history"""
        return len(self.conversation_history)

    def get_last_messages(self, count: int = 5) -> list:
        """Get last N messages from history"""
        return self.conversation_history[-count:]

    async def analyze_intent(self, command: str) -> dict:
        """
        Analyze user command to extract intent using available AI provider
        
        Args:
            command: User command string
            
        Returns:
            Dictionary with intent analysis
        """
        try:
            if not self.available_providers:
                return {"error": "AI Engine not configured"}
            
            intent_prompt = """Analyze this command and extract:
1. action: main action (open, close, search, analyze, etc.)
2. target: what to act on (app name, file, screen, etc.)
3. parameters: additional details

Respond in JSON format only."""
            
            # Save current system prompt and temporarily replace it
            original_prompt = self.system_prompt
            original_history = self.conversation_history.copy()
            
            self.system_prompt = intent_prompt
            self.conversation_history = []
            
            # Use the universal chat method
            intent = await self.chat(command)
            
            # Restore original prompt and history
            self.system_prompt = original_prompt
            self.conversation_history = original_history
            
            return {
                "success": True,
                "intent": intent,
                "original_command": command,
                "provider_used": self.last_provider_used
            }
            
        except Exception as e:
            logger.error(f"Intent analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_provider_stats(self) -> dict:
        """Get statistics for all providers"""
        stats = {}
        for provider, data in self.provider_stats.items():
            if data['calls'] > 0:
                avg_time = data['total_time'] / data['calls']
                stats[provider] = {
                    'calls': data['calls'],
                    'errors': data['errors'],
                    'avg_response_time': round(avg_time, 2),
                    'success_rate': round((data['calls'] - data['errors']) / data['calls'] * 100, 1)
                }
        return stats

    def set_model(self, model: str):
        """Change AI model"""
        self.model = model
        logger.info(f"AI model changed to: {model}")

    def set_temperature(self, temperature: float):
        """Change temperature setting"""
        self.temperature = max(0.0, min(2.0, temperature))
        logger.info(f"Temperature set to: {self.temperature}")

    def get_config(self) -> dict:
        """Get current configuration and provider status"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "history_count": len(self.conversation_history),
            "max_history": self.max_history,
            "available_providers": self.available_providers,
            "last_provider_used": self.last_provider_used,
            "provider_stats": self.provider_stats,
            "api_keys_configured": {
                provider: bool(key) for provider, key in self.api_keys.items()
            }
        }

    def update_system_prompt(self, new_prompt: str):
        """Update system prompt"""
        self.system_prompt = new_prompt
        logger.info("System prompt updated")
