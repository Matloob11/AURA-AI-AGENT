"""
Vision Engine for AURA
Screen Capture + OCR + Vision AI Analysis
"""

import os
import base64
import io
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv
from PIL import Image
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class VisionEngine:
    """Vision Engine for screen capture, OCR, and AI vision analysis"""
    
    def __init__(self):
        """Initialize Vision Engine"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        # Initialize screen capture
        try:
            import mss
            self.mss = mss.mss()
            self.screen_capture_available = True
            logger.info("Screen capture (mss) initialized successfully")
        except Exception as e:
            logger.warning(f"mss not available, trying PIL: {e}")
            try:
                from PIL import ImageGrab
                self.ImageGrab = ImageGrab
                self.mss = None
                self.screen_capture_available = True
                logger.info("Screen capture (PIL) initialized successfully")
            except Exception as e2:
                logger.warning(f"Screen capture not available: {e2}")
                self.screen_capture_available = False
                self.mss = None
                self.ImageGrab = None
        
        # Initialize OCR
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.ocr_available = True
            logger.info("OCR (pytesseract) initialized successfully")
        except Exception as e:
            logger.warning(f"OCR not available: {e}")
            self.ocr_available = False
            self.pytesseract = None
        
        # Initialize OpenCV (optional)
        try:
            import cv2
            self.cv2 = cv2
            self.opencv_available = True
            logger.info("OpenCV initialized successfully")
        except Exception as e:
            logger.warning(f"OpenCV not available: {e}")
            self.opencv_available = False
            self.cv2 = None
        
        # Initialize OpenAI client for vision
        if self.api_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.api_key)
                self.vision_ai_available = True
                logger.info("OpenAI Vision API initialized successfully")
            except Exception as e:
                logger.warning(f"OpenAI Vision not available: {e}")
                self.vision_ai_available = False
                self.openai_client = None
        else:
            self.vision_ai_available = False
            self.openai_client = None

    def capture_screen(self) -> Optional[Image.Image]:
        """Capture entire screen"""
        try:
            if not self.screen_capture_available:
                logger.error("Screen capture not available")
                return None
            
            if self.mss:
                # Use mss for faster capture
                monitor = self.mss.monitors[1]  # Primary monitor
                screenshot = self.mss.grab(monitor)
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                logger.info("Screen captured using mss")
                return img
            elif self.ImageGrab:
                # Fallback to PIL
                img = self.ImageGrab.grab()
                logger.info("Screen captured using PIL")
                return img
            else:
                logger.error("No screen capture method available")
                return None
                
        except Exception as e:
            logger.error(f"Screen capture error: {e}")
            return None

    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[Image.Image]:
        """Capture specific screen region"""
        try:
            if not self.screen_capture_available:
                logger.error("Screen capture not available")
                return None
            
            if self.mss:
                monitor = {
                    "top": y,
                    "left": x,
                    "width": width,
                    "height": height
                }
                screenshot = self.mss.grab(monitor)
                img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
                logger.info(f"Region captured: ({x}, {y}, {width}, {height})")
                return img
            elif self.ImageGrab:
                img = self.ImageGrab.grab(bbox=(x, y, x + width, y + height))
                logger.info(f"Region captured: ({x}, {y}, {width}, {height})")
                return img
            else:
                return None
                
        except Exception as e:
            logger.error(f"Region capture error: {e}")
            return None

    def capture_webcam(self) -> Optional[Image.Image]:
        """Capture image from webcam"""
        try:
            if not self.opencv_available:
                logger.error("OpenCV not available for webcam capture")
                return None
            
            # Open webcam
            cap = self.cv2.VideoCapture(0)
            
            if not cap.isOpened():
                logger.error("Could not open webcam")
                return None
            
            # Capture frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.error("Failed to capture webcam frame")
                return None
            
            # Convert BGR to RGB
            frame_rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            logger.info("Webcam image captured")
            return img
            
        except Exception as e:
            logger.error(f"Webcam capture error: {e}")
            return None

    def extract_text_from_image(self, image: Image.Image) -> dict:
        """Extract text from image using OCR"""
        try:
            if not self.ocr_available:
                return {
                    "success": False,
                    "error": "OCR not available. Install: pip install pytesseract"
                }
            
            # Perform OCR
            text = self.pytesseract.image_to_string(image)
            
            logger.info(f"OCR extracted {len(text)} characters")
            
            return {
                "success": True,
                "text": text.strip() if text.strip() else "No text detected",
                "length": len(text.strip())
            }
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def extract_text_from_screen(self) -> dict:
        """Extract text from current screen"""
        try:
            screenshot = self.capture_screen()
            
            if screenshot is None:
                return {
                    "success": False,
                    "error": "Failed to capture screen"
                }
            
            return self.extract_text_from_image(screenshot)
            
        except Exception as e:
            logger.error(f"Screen OCR error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def analyze_image(self, image: Image.Image, prompt: str = "Describe what you see in this image.") -> dict:
        """Analyze image using OpenAI Vision API"""
        try:
            if not self.vision_ai_available:
                return {
                    "success": False,
                    "error": "OpenAI Vision API not available. Check OPENAI_API_KEY"
                }
            
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            logger.info("Sending image to OpenAI Vision API...")
            
            # Call OpenAI Vision API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # Updated model name
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            analysis = response.choices[0].message.content
            
            logger.info(f"Vision analysis complete: {analysis[:50]}...")
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def analyze_screen_with_ai(self, prompt: str = "Analyze this screen. What is the user looking at?") -> dict:
        """Analyze current screen using AI vision"""
        try:
            screenshot = self.capture_screen()
            
            if screenshot is None:
                return {
                    "success": False,
                    "error": "Failed to capture screen"
                }
            
            return self.analyze_image(screenshot, prompt)
            
        except Exception as e:
            logger.error(f"Screen analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def find_text_on_screen(self, search_text: str) -> dict:
        """Find specific text on screen and return coordinates"""
        try:
            if not self.ocr_available:
                return {
                    "found": False,
                    "error": "OCR not available"
                }
            
            screenshot = self.capture_screen()
            
            if screenshot is None:
                return {
                    "found": False,
                    "error": "Failed to capture screen"
                }
            
            # Get text with bounding boxes
            data = self.pytesseract.image_to_data(screenshot, output_type=self.pytesseract.Output.DICT)
            
            for i, text in enumerate(data['text']):
                if search_text.lower() in text.lower():
                    logger.info(f"Text '{search_text}' found at ({data['left'][i]}, {data['top'][i]})")
                    return {
                        "found": True,
                        "x": data['left'][i],
                        "y": data['top'][i],
                        "width": data['width'][i],
                        "height": data['height'][i],
                        "text": text
                    }
            
            logger.info(f"Text '{search_text}' not found on screen")
            return {"found": False}
            
        except Exception as e:
            logger.error(f"Text search error: {e}")
            return {
                "found": False,
                "error": str(e)
            }

    def save_screenshot(self, filename: str = "screenshot.png") -> dict:
        """Save screenshot to file"""
        try:
            screenshot = self.capture_screen()
            
            if screenshot is None:
                return {
                    "success": False,
                    "error": "Failed to capture screen"
                }
            
            screenshot.save(filename)
            logger.info(f"Screenshot saved: {filename}")
            
            return {
                "success": True,
                "filename": filename,
                "message": f"Screenshot saved: {filename}"
            }
            
        except Exception as e:
            logger.error(f"Save screenshot error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_status(self) -> dict:
        """Get vision engine status"""
        return {
            "screen_capture_available": self.screen_capture_available,
            "ocr_available": self.ocr_available,
            "opencv_available": self.opencv_available,
            "vision_ai_available": self.vision_ai_available,
            "capture_method": "mss" if self.mss else "PIL" if self.ImageGrab else "none"
        }

    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.mss:
                self.mss.close()
            logger.info("Vision engine cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
