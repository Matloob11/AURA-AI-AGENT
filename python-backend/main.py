"""
AURA AI Backend Server
FastAPI + Socket.IO for real-time communication
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import socketio
from datetime import datetime
import logging
import asyncio

# Import Engines
from ai_engine import AIEngine
from voice_engine import VoiceEngine
from vision_engine import VisionEngine
from automation_engine import AutomationEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="AURA AI Backend",
    description="Advanced Desktop AI Assistant Backend",
    version="1.0.0"
)

# Initialize Socket.IO
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False
)

# Wrap Socket.IO with ASGI app
socket_app = socketio.ASGIApp(sio, app)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engines
ai_engine = AIEngine()
voice_engine = VoiceEngine()
vision_engine = VisionEngine()
automation_engine = AutomationEngine()
logger.info("AI Engine initialized")
logger.info("Voice Engine initialized")
logger.info("Vision Engine initialized")
logger.info("Automation Engine initialized")

# Pydantic Models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    timestamp: str = None

class AutomationRequest(BaseModel):
    action: str
    params: dict = {}

# ============================================
# REST API ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AURA AI Backend",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def get_status():
    """Get detailed server status"""
    ai_config = ai_engine.get_config()
    
    return {
        "status": "operational",
        "services": {
            "api": "online",
            "socket": "online",
            "ai_engine": "ready",
            "voice_engine": "ready" if voice_engine.get_status()["speech_recognition_available"] else "not_configured",
            "vision_engine": "ready" if vision_engine.get_status()["screen_capture_available"] else "not_configured",
            "automation_engine": "ready" if automation_engine.get_status()["pyautogui_available"] else "not_configured"
        },
        "voice_status": voice_engine.get_status(),
        "vision_status": vision_engine.get_status(),
        "automation_status": automation_engine.get_status(),
        "ai_config": {
            "model": ai_config.get("model", "local"),
            "temperature": ai_config.get("temperature", 0.7),
            "history_count": ai_config.get("history_count", 0),
            "api_key_configured": True
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Process chat message with AI"""
    try:
        logger.info(f"Chat request: {request.message}")
        
        # Emit processing event
        await sio.emit('event', {
            'message': f'Processing: {request.message}',
            'timestamp': datetime.now().isoformat()
        })
        
        # Get AI response
        response_text = await ai_engine.chat(request.message)
        
        # Emit AI response via Socket.IO
        await sio.emit('ai_response', {
            'message': response_text,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Chat response: {response_text[:50]}...")
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        error_msg = f"Chat error: {str(e)}"
        logger.error(error_msg)
        
        await sio.emit('event', {
            'message': error_msg,
            'timestamp': datetime.now().isoformat()
        })
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice/start")
async def start_voice():
    """Start voice recording and process with AI"""
    try:
        logger.info("Voice recording start requested")
        
        # Start listening
        result = voice_engine.start_listening()
        
        if not result["success"]:
            await sio.emit('event', {
                'message': f'Voice error: {result["error"]}',
                'timestamp': datetime.now().isoformat()
            })
            return result
        
        await sio.emit('event', {
            'message': 'Voice recording started. Speak now...',
            'timestamp': datetime.now().isoformat()
        })
        
        # Listen for voice input
        voice_result = voice_engine.listen_once()
        
        if voice_result["success"]:
            text = voice_result["text"]
            logger.info(f"Voice recognized: {text}")
            
            # Emit voice result
            await sio.emit('voice_result', {
                'text': text,
                'timestamp': datetime.now().isoformat()
            })
            
            # Process with AI
            ai_response = await ai_engine.chat(text)
            
            # Speak AI response
            voice_engine.speak(ai_response)
            
            # Emit AI response
            await sio.emit('ai_response', {
                'message': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                "status": "success",
                "text": text,
                "response": ai_response
            }
        else:
            await sio.emit('event', {
                'message': f'Voice error: {voice_result["error"]}',
                'timestamp': datetime.now().isoformat()
            })
            return voice_result
            
    except Exception as e:
        error_msg = f"Voice error: {str(e)}"
        logger.error(error_msg)
        await sio.emit('event', {
            'message': error_msg,
            'timestamp': datetime.now().isoformat()
        })
        return {"status": "error", "message": str(e)}

@app.post("/voice/stop")
async def stop_voice():
    """Stop voice recording"""
    try:
        result = voice_engine.stop_listening()
        
        await sio.emit('event', {
            'message': 'Voice recording stopped',
            'timestamp': datetime.now().isoformat()
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error stopping voice: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/wakeword/start")
async def start_wakeword():
    """Start wake word detection"""
    try:
        logger.info("Wake word detection start requested")
        
        async def wake_word_callback(data):
            """Callback when wake word is detected"""
            logger.info(f"Wake word detected: {data}")
            
            await sio.emit('event', {
                'message': f'Wake word detected: {data["wake_word"]}',
                'timestamp': datetime.now().isoformat()
            })
            
            # Listen for command after wake word
            voice_result = voice_engine.listen_once()
            
            if voice_result["success"]:
                text = voice_result["text"]
                
                await sio.emit('voice_result', {
                    'text': text,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Process with AI
                ai_response = await ai_engine.chat(text)
                voice_engine.speak(ai_response)
                
                await sio.emit('ai_response', {
                    'message': ai_response,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Start wake word detection
        result = voice_engine.start_wake_word_detection(
            callback=lambda data: asyncio.create_task(wake_word_callback(data))
        )
        
        if result["success"]:
            await sio.emit('event', {
                'message': f'Wake word detection started. Say "{voice_engine.wake_word}"',
                'timestamp': datetime.now().isoformat()
            })
        else:
            await sio.emit('event', {
                'message': f'Wake word error: {result["error"]}',
                'timestamp': datetime.now().isoformat()
            })
        
        return result
        
    except Exception as e:
        error_msg = f"Wake word error: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": str(e)}

@app.post("/wakeword/stop")
async def stop_wakeword():
    """Stop wake word detection"""
    try:
        result = voice_engine.stop_wake_word_detection()
        
        await sio.emit('event', {
            'message': 'Wake word detection stopped',
            'timestamp': datetime.now().isoformat()
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error stopping wake word: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/vision/analyze")
async def analyze_vision():
    """Analyze screen with AI vision"""
    try:
        logger.info("Vision analysis requested")
        
        await sio.emit('event', {
            'message': 'Analyzing screen...',
            'timestamp': datetime.now().isoformat()
        })
        
        # Analyze screen with AI
        result = vision_engine.analyze_screen_with_ai(
            "Analyze this screen. What is the user looking at? What can they do?"
        )
        
        if result["success"]:
            analysis = result["analysis"]
            
            # Emit result
            await sio.emit('vision_result', {
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            })
            
            # Optionally speak the analysis
            if voice_engine.get_status()["text_to_speech_available"]:
                voice_engine.speak(analysis)
            
            logger.info(f"Vision analysis complete: {analysis[:50]}...")
            
            return {
                "status": "success",
                "analysis": analysis
            }
        else:
            await sio.emit('event', {
                'message': f'Vision error: {result["error"]}',
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                "status": "error",
                "message": result["error"]
            }
            
    except Exception as e:
        error_msg = f"Vision analysis error: {str(e)}"
        logger.error(error_msg)
        await sio.emit('event', {
            'message': error_msg,
            'timestamp': datetime.now().isoformat()
        })
        return {"status": "error", "message": str(e)}

@app.post("/vision/ocr")
async def vision_ocr():
    """Extract text from screen using OCR"""
    try:
        logger.info("OCR requested")
        
        await sio.emit('event', {
            'message': 'Extracting text from screen...',
            'timestamp': datetime.now().isoformat()
        })
        
        result = vision_engine.extract_text_from_screen()
        
        if result["success"]:
            text = result["text"]
            
            await sio.emit('vision_result', {
                'ocr_text': text,
                'length': result["length"],
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"OCR extracted {result['length']} characters")
            
            return {
                "status": "success",
                "text": text,
                "length": result["length"]
            }
        else:
            await sio.emit('event', {
                'message': f'OCR error: {result["error"]}',
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                "status": "error",
                "message": result["error"]
            }
            
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/vision/webcam")
async def vision_webcam():
    """Capture and analyze webcam image"""
    try:
        logger.info("Webcam capture requested")
        
        await sio.emit('event', {
            'message': 'Capturing webcam...',
            'timestamp': datetime.now().isoformat()
        })
        
        # Capture webcam
        image = vision_engine.capture_webcam()
        
        if image is None:
            return {
                "status": "error",
                "message": "Failed to capture webcam. OpenCV required."
            }
        
        # Optionally analyze with AI
        result = vision_engine.analyze_image(
            image,
            "Describe what you see in this webcam image."
        )
        
        if result["success"]:
            await sio.emit('vision_result', {
                'webcam_analysis': result["analysis"],
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                "status": "success",
                "analysis": result["analysis"]
            }
        else:
            return {
                "status": "error",
                "message": result["error"]
            }
            
    except Exception as e:
        logger.error(f"Webcam error: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/vision/status")
async def get_vision_status():
    """Get vision engine status"""
    try:
        status = vision_engine.get_status()
        return {
            "status": "success",
            "vision_status": status
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/vision/find-text")
async def find_text_on_screen(request: ChatRequest):
    """Find specific text on screen"""
    try:
        search_text = request.message
        logger.info(f"Searching for text: {search_text}")
        
        result = vision_engine.find_text_on_screen(search_text)
        
        if result.get("found"):
            await sio.emit('vision_result', {
                'text_found': True,
                'location': {
                    'x': result['x'],
                    'y': result['y'],
                    'width': result['width'],
                    'height': result['height']
                },
                'timestamp': datetime.now().isoformat()
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Find text error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/vision/screenshot")
async def save_screenshot():
    """Save screenshot to file"""
    try:
        result = vision_engine.save_screenshot()
        
        if result["success"]:
            await sio.emit('event', {
                'message': f'Screenshot saved: {result["filename"]}',
                'timestamp': datetime.now().isoformat()
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return {"status": "error", "message": str(e)}

# ============================================
# AUTOMATION ENDPOINTS
# ============================================

@app.post("/automation/run")
async def run_automation(request: AutomationRequest):
    """Execute automation action"""
    try:
        action = request.action
        params = request.params
        
        logger.info(f"Automation requested: {action}")
        
        await sio.emit('event', {
            'message': f'Executing automation: {action}',
            'timestamp': datetime.now().isoformat()
        })
        
        # Execute action
        if action == "click":
            result = automation_engine.click(params["x"], params["y"], 
                                            params.get("button", "left"),
                                            params.get("clicks", 1))
        elif action == "type":
            result = automation_engine.type_text(params["text"], 
                                                params.get("interval", 0.05))
        elif action == "key":
            result = automation_engine.press_key(params["key"])
        elif action == "hotkey":
            result = automation_engine.hotkey(*params["keys"])
        elif action == "move":
            result = automation_engine.move_mouse(params["x"], params["y"],
                                                 params.get("duration", 0.5))
        elif action == "scroll":
            result = automation_engine.scroll(params["amount"])
        elif action == "open":
            result = automation_engine.open_application(params["app"])
        elif action == "command":
            result = automation_engine.run_command(params["command"],
                                                  params.get("timeout", 30))
        elif action == "macro":
            result = automation_engine.execute_macro(params["actions"])
        elif action == "minimize":
            result = automation_engine.minimize_all_windows()
        elif action == "copy":
            result = automation_engine.copy_to_clipboard(params["text"])
        elif action == "paste":
            result = automation_engine.paste_from_clipboard()
        elif action == "mousepos":
            result = automation_engine.get_mouse_position()
        elif action == "screensize":
            result = automation_engine.get_screen_size()
        else:
            result = {
                "success": False,
                "error": f"Unknown action: {action}"
            }
        
        # Emit result
        if result.get("success"):
            await sio.emit('automation_result', {
                'action': action,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
        else:
            await sio.emit('event', {
                'message': f'Automation error: {result.get("error")}',
                'timestamp': datetime.now().isoformat()
            })
        
        logger.info(f"Automation complete: {action}")
        
        return result
        
    except Exception as e:
        error_msg = f"Automation error: {str(e)}"
        logger.error(error_msg)
        await sio.emit('event', {
            'message': error_msg,
            'timestamp': datetime.now().isoformat()
        })
        return {"success": False, "error": str(e)}

@app.get("/automation/status")
async def get_automation_status():
    """Get automation engine status"""
    try:
        status = automation_engine.get_status()
        return {
            "status": "success",
            "automation_status": status
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/automation/click-text")
async def click_text_on_screen(request: ChatRequest):
    """Find text on screen and click it (Vision + Automation integration)"""
    try:
        search_text = request.message
        logger.info(f"Click text requested: {search_text}")
        
        # Find text using vision engine
        find_result = vision_engine.find_text_on_screen(search_text)
        
        if not find_result.get("found"):
            return {
                "success": False,
                "error": f"Text '{search_text}' not found on screen"
            }
        
        # Calculate center of text
        x = find_result["x"] + find_result["width"] // 2
        y = find_result["y"] + find_result["height"] // 2
        
        # Click at text location
        click_result = automation_engine.click(x, y)
        
        if click_result["success"]:
            await sio.emit('automation_result', {
                'action': 'click_text',
                'text': search_text,
                'location': {'x': x, 'y': y},
                'timestamp': datetime.now().isoformat()
            })
        
        return {
            "success": click_result["success"],
            "text": search_text,
            "location": {"x": x, "y": y},
            "message": f"Clicked on '{search_text}' at ({x}, {y})"
        }
        
    except Exception as e:
        logger.error(f"Click text error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/ai/clear-history")
async def clear_ai_history():
    """Clear AI conversation history"""
    try:
        ai_engine.clear_history()
        
        await sio.emit('event', {
            'message': 'Conversation history cleared',
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "message": "History cleared"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/ai/config")
async def get_ai_config():
    """Get AI engine configuration and provider status"""
    try:
        config = ai_engine.get_config()
        stats = ai_engine.get_provider_stats()
        
        return {
            "status": "success",
            "config": config,
            "provider_stats": stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/ai/analyze-intent")
async def analyze_intent(request: ChatRequest):
    """Analyze command intent"""
    try:
        result = await ai_engine.analyze_intent(request.message)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/voice/status")
async def get_voice_status():
    """Get voice engine status"""
    try:
        status = voice_engine.get_status()
        return {
            "status": "success",
            "voice_status": status
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/voice/speak")
async def speak_text(request: ChatRequest):
    """Speak text using TTS"""
    try:
        result = voice_engine.speak(request.message)
        
        await sio.emit('event', {
            'message': f'Speaking: {request.message[:50]}...',
            'timestamp': datetime.now().isoformat()
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error in speak: {e}")
        return {"status": "error", "message": str(e)}

# ============================================
# SERVER STARTUP
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("  AURA AI Backend Server")
    print("=" * 50)
    print(f"API Server: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print(f"Socket.IO: Connected via same port")
    print("=" * 50)
    print("Server starting...\n")
    
    # Run server with Socket.IO integration
    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

# ============================================
# SOCKET.IO EVENT HANDLERS
# ============================================

@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"[Socket.IO] Client connected: {sid}")
    await sio.emit('event', {
        'message': 'Connected to AURA AI Backend',
        'timestamp': datetime.now().isoformat()
    }, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"[Socket.IO] Client disconnected: {sid}")

@sio.event
async def ping(sid, data):
    """Handle ping from client"""
    await sio.emit('pong', {
        'timestamp': datetime.now().isoformat()
    }, room=sid)

@sio.event
async def message(sid, data):
    """Handle generic message from client"""
    print(f"[Socket.IO] Message from {sid}: {data}")
    await sio.emit('event', {
        'message': f'Received: {data}',
        'timestamp': datetime.now().isoformat()
    }, room=sid)
