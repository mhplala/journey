from typing import List, Dict, Any
import aiohttp
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

class DeepSeekService:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_base = os.getenv("DEEPSEEK_API_BASE")
        if not self.api_key or not self.api_base:
            raise ValueError("DeepSeek API configuration missing")

    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response using the DeepSeek API
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"DeepSeek API error: {error_data.get('error', 'Unknown error')}"
                        )
                    
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except aiohttp.ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with DeepSeek API: {str(e)}"
            )
