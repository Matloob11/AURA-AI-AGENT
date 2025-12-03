"""
Automation Engine for AURA
Mouse, Keyboard, and System Control
"""

import os
import time
import subprocess
import platform
import logging
from typing import List, Dict, Optional
from threading import Lock

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutomationEngine:
    """Automation Engine for system control and automation"""
    
    def __init__(self):
        """Initialize Automation Engine"""
        self.system = platform.system()
        self.lock = Lock()  # Thread safety
        
        # Initialize PyAutoGUI
        try:
            import pyautogui
            self.pyautogui = pyautogui
            
            # Safety settings
            self.pyautogui.FAILSAFE = True  # Move mouse to corner to abort
            self.pyautogui.PAUSE = 0.1  # Pause between actions
            
            self.pyautogui_available = True
            logger.info("PyAutoGUI initialized successfully")
            
        except Exception as e:
            logger.warning(f"PyAutoGUI not available: {e}")
            self.pyautogui_available = False
            self.pyautogui = None
        
        # Initialize keyboard control
        try:
            import keyboard
            self.keyboard = keyboard
            self.keyboard_available = True
            logger.info("Keyboard control initialized successfully")
            
        except Exception as e:
            logger.warning(f"Keyboard control not available: {e}")
            self.keyboard_available = False
            self.keyboard = None
        
        # Initialize clipboard
        try:
            import pyperclip
            self.pyperclip = pyperclip
            self.clipboard_available = True
            logger.info("Clipboard control initialized successfully")
            
        except Exception as e:
            logger.warning(f"Clipboard not available: {e}")
            self.clipboard_available = False
            self.pyperclip = None
        
        logger.info(f"Automation Engine initialized on {self.system}")

    def click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> dict:
        """Click at coordinates"""
        try:
            if not self.pyautogui_available:
                return {
                    "success": False,
                    "error": "PyAutoGUI not available. Install: pip install pyautogui"
                }
            
            with self.lock:
                self.pyautogui.click(x, y, clicks=clicks, button=button)
            
            logger.info(f"Clicked at ({x}, {y}) with {button} button")
            
            return {
                "success": True,
                "action": f"Clicked at ({x}, {y})",
                "button": button,
                "clicks": clicks
            }
            
        except Exception as e:
            logger.error(f"Click error: {e}")
            return {"success": False, "error": str(e)}

    def type_text(self, text: str, interval: float = 0.05) -> dict:
        """Type text"""
        try:
            if not self.pyautogui_available:
                return {
                    "success": False,
                    "error": "PyAutoGUI not available"
                }
            
            with self.lock:
                self.pyautogui.write(text, interval=interval)
            
            logger.info(f"Typed text: {text[:50]}...")
            
            return {
                "success": True,
                "action": f"Typed {len(text)} characters",
                "text": text[:50] + "..." if len(text) > 50 else text
            }
            
        except Exception as e:
            logger.error(f"Type error: {e}")
            return {"success": False, "error": str(e)}

    def press_key(self, key: str) -> dict:
        """Press a key"""
        try:
            if not self.pyautogui_available:
                return {
                    "success": False,
                    "error": "PyAutoGUI not available"
                }
            
            with self.lock:
                self.pyautogui.press(key)
            
            logger.info(f"Pressed key: {key}")
            
            return {
                "success": True,
                "action": f"Pressed: {key}"
            }
            
        except Exception as e:
            logger.error(f"Key press error: {e}")
            return {"success": False, "error": str(e)}

    def hotkey(self, *keys) -> dict:
        """Press hotkey combination"""
        try:
            if not self.pyautogui_available:
                return {
                    "success": False,
                    "error": "PyAutoGUI not available"
                }
            
            with self.lock:
                self.pyautogui.hotkey(*keys)
            
            hotkey_str = '+'.join(keys)
            logger.info(f"Pressed hotkey: {hotkey_str}")
            
            return {
                "success": True,
                "action": f"Hotkey: {hotkey_str}"
            }
            
        except Exception as e:
            logger.error(f"Hotkey error: {e}")
            return {"success": False, "error": str(e)}

    def move_mouse(self, x: int, y: int, duration: float = 0.5) -> dict:
        """Move mouse to coordinates"""
        try:
            if not self.pyautogui_available:
                return {
                    "success": False,
                    "error": "PyAutoGUI not available"
                }
            
            with self.lock:
                self.pyautogui.moveTo(x, y, duration=duration)
            
            logger.info(f"Moved mouse to ({x}, {y})")
            
            return {
                "success": True,
                "action": f"Moved to ({x}, {y})"
            }
            
        except Exception as e:
            logger.error(f"Mouse move error: {e}")
            return {"success": False, "error": str(e)}

    def scroll(self, amount: int) -> dict:
        """Scroll up (positive) or down (negative)"""
        try:
            if not self.pyautogui_available:
                return {
                    "success": False,
                    "error": "PyAutoGUI not available"
                }
            
            with self.lock:
                self.pyautogui.scroll(amount)
            
            direction = "up" if amount > 0 else "down"
            logger.info(f"Scrolled {direction} by {abs(amount)}")
            
            return {
                "success": True,
                "action": f"Scrolled {direction}",
                "amount": amount
            }
            
        except Exception as e:
            logger.error(f"Scroll error: {e}")
            return {"success": False, "error": str(e)}

    def open_application(self, app_name: str) -> dict:
        """Open application"""
        try:
            logger.info(f"Opening application: {app_name}")
            
            if self.system == "Windows":
                os.startfile(app_name)
            elif self.system == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", app_name])
            else:  # Linux
                subprocess.Popen([app_name])
            
            return {
                "success": True,
                "action": f"Opened: {app_name}"
            }
            
        except Exception as e:
            logger.error(f"Open application error: {e}")
            return {"success": False, "error": str(e)}

    def run_command(self, command: str, timeout: int = 30) -> dict:
        """Execute system command"""
        try:
            logger.info(f"Running command: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            logger.info(f"Command completed with return code: {result.returncode}")
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timeout: {command}")
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Command error: {e}")
            return {"success": False, "error": str(e)}

    def get_mouse_position(self) -> dict:
        """Get current mouse position"""
        try:
            if not self.pyautogui_available:
                return {
                    "success": False,
                    "error": "PyAutoGUI not available"
                }
            
            x, y = self.pyautogui.position()
            
            return {
                "success": True,
                "x": x,
                "y": y
            }
            
        except Exception as e:
            logger.error(f"Get mouse position error: {e}")
            return {"success": False, "error": str(e)}

    def get_screen_size(self) -> dict:
        """Get screen dimensions"""
        try:
            if not self.pyautogui_available:
                return {
                    "success": False,
                    "error": "PyAutoGUI not available"
                }
            
            width, height = self.pyautogui.size()
            
            return {
                "success": True,
                "width": width,
                "height": height
            }
            
        except Exception as e:
            logger.error(f"Get screen size error: {e}")
            return {"success": False, "error": str(e)}

    def execute_macro(self, actions: List[Dict]) -> dict:
        """Execute a sequence of actions"""
        try:
            logger.info(f"Executing macro with {len(actions)} actions")
            
            results = []
            
            for i, action in enumerate(actions):
                action_type = action.get("type")
                logger.info(f"Macro step {i+1}/{len(actions)}: {action_type}")
                
                if action_type == "click":
                    result = self.click(action["x"], action["y"])
                elif action_type == "type":
                    result = self.type_text(action["text"])
                elif action_type == "key":
                    result = self.press_key(action["key"])
                elif action_type == "hotkey":
                    result = self.hotkey(*action["keys"])
                elif action_type == "move":
                    result = self.move_mouse(action["x"], action["y"])
                elif action_type == "scroll":
                    result = self.scroll(action["amount"])
                elif action_type == "wait":
                    duration = action.get("duration", 1)
                    time.sleep(duration)
                    result = {"success": True, "action": f"Waited {duration}s"}
                else:
                    result = {"success": False, "error": f"Unknown action: {action_type}"}
                
                results.append(result)
                
                if not result.get("success"):
                    logger.warning(f"Macro stopped at step {i+1} due to error")
                    break
            
            logger.info("Macro execution complete")
            
            return {
                "success": True,
                "results": results,
                "completed": len(results),
                "total": len(actions)
            }
            
        except Exception as e:
            logger.error(f"Macro execution error: {e}")
            return {"success": False, "error": str(e)}

    def minimize_all_windows(self) -> dict:
        """Minimize all windows"""
        try:
            logger.info("Minimizing all windows")
            
            if self.system == "Windows":
                self.hotkey('win', 'd')
            elif self.system == "Darwin":
                self.hotkey('command', 'option', 'h', 'm')
            else:
                return {
                    "success": False,
                    "error": "Minimize all not supported on this platform"
                }
            
            return {
                "success": True,
                "action": "Minimized all windows"
            }
            
        except Exception as e:
            logger.error(f"Minimize error: {e}")
            return {"success": False, "error": str(e)}

    def copy_to_clipboard(self, text: str) -> dict:
        """Copy text to clipboard"""
        try:
            if not self.clipboard_available:
                return {
                    "success": False,
                    "error": "Clipboard not available. Install: pip install pyperclip"
                }
            
            self.pyperclip.copy(text)
            logger.info(f"Copied to clipboard: {text[:50]}...")
            
            return {
                "success": True,
                "action": "Copied to clipboard"
            }
            
        except Exception as e:
            logger.error(f"Clipboard error: {e}")
            return {"success": False, "error": str(e)}

    def paste_from_clipboard(self) -> dict:
        """Get text from clipboard"""
        try:
            if not self.clipboard_available:
                return {
                    "success": False,
                    "error": "Clipboard not available"
                }
            
            text = self.pyperclip.paste()
            logger.info(f"Pasted from clipboard: {text[:50]}...")
            
            return {
                "success": True,
                "text": text
            }
            
        except Exception as e:
            logger.error(f"Clipboard error: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> dict:
        """Get automation engine status"""
        return {
            "pyautogui_available": self.pyautogui_available,
            "keyboard_available": self.keyboard_available,
            "clipboard_available": self.clipboard_available,
            "system": self.system,
            "failsafe_enabled": self.pyautogui.FAILSAFE if self.pyautogui_available else None
        }

    def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Automation engine cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
