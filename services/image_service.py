import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.base_url = "https://image.pollinations.ai/prompt"
    
    def generate_image(self, prompt: str, width: int = 800, height: int = 200) -> str:
        """Generate image using Pollinations AI (free alternative to Nano Banana)"""
        try:
            # Clean and encode prompt
            clean_prompt = prompt.replace(" ", "%20").replace(",", "%2C")
            image_url = f"{self.base_url}/{clean_prompt}?width={width}&height={height}&seed=42"
            
            # Test if URL is accessible
            response = requests.head(image_url, timeout=5)
            if response.status_code == 200:
                return image_url
            else:
                return self._fallback_image(prompt, width, height)
                
        except Exception as e:
            logger.warning(f"Image generation failed: {e}")
            return self._fallback_image(prompt, width, height)
    
    def _fallback_image(self, prompt: str, width: int, height: int) -> str:
        """Fallback to placeholder image"""
        text = prompt.replace(" ", "+")[:50]
        return f"https://via.placeholder.com/{width}x{height}/4A90E2/FFFFFF?text={text}"