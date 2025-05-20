import os
import json
import aiohttp
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIIntegration:
    """Utility class for AI model integration."""
    
    def __init__(self):
        # Get API key and URL from environment variables
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent")
        
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables")
    
    async def generate_content(self, prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Call the Gemini API with the given prompt."""
        if not self.api_key:
            return {"status": "error", "message": "GEMINI_API_KEY not found in environment variables"}
            
        url = f"{self.api_url}?key={self.api_key}"
        
        # Add system instructions to ensure the AI stays on topic
        system_instruction = "You are an AI assistant helping with software development tasks. Stay focused on the specific task or question provided. Respond in JSON format when requested."
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"{system_instruction}\n\n{prompt}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Extract the generated text from the response
                        candidates = result.get("candidates", [])
                        if candidates and len(candidates) > 0:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts and len(parts) > 0:
                                generated_text = parts[0].get("text", "")
                                return {"status": "success", "content": generated_text}
                        
                        # If we couldn't extract the text properly
                        return {"status": "error", "message": "Failed to extract content from API response", "details": result}
                    else:
                        error_text = await response.text()
                        return {"status": "error", "message": f"API error: {response.status}", "details": error_text}
        except Exception as e:
            return {"status": "error", "message": f"Exception: {str(e)}"}
    
    @staticmethod
    def extract_json_from_text(text: str) -> Dict[str, Any]:
        """Extract JSON from text response."""
        try:
            # Find the JSON part in the response (it might be surrounded by markdown or other text)
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = text[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"raw_text": text}
        except json.JSONDecodeError:
            return {"raw_text": text}