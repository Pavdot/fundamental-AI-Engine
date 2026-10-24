import os 
import json
from pydantic import BaseModel, Field
from pydantic import ValidationError
from dotenv import load_dotenv  
from openai import OpenAI 

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

news = "Bitcoin fell 12% after a major cryptocurrency exchange suspended withdrawals."


class NewsAnalysis(BaseModel):
    asset: str = Field(..., description="The financial asset being analyzed")
    direction: float = Field(..., ge=-1, le=1, description="The direction of the price movement (-1 to 1)")
    importance: float = Field(..., ge=0, le=1, description="The importance of the news (0 to 1)")
    confidence: float = Field(..., ge=0, le=1, description="The confidence in the analysis (0 to 1)")
    horizon_hours: int = Field(..., gt=0, description="The time horizon for the analysis in hours")


def call_llm(prompt): 
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content
    return content     

def analyze_news(news):

    previous_error = ""
    prompt = f"""Analyze this financial news:
    {news}

    Return ONLY valid JSON with these fields:
    - asset
    - direction
    - importance
    - confidence
    - horizon_hours

    Rules:
    - direction must be between -1 and 1
    - importance must be between 0 and 1
    - confidence must be between 0 and 1
    - horizon_hours must be a positive integer"""

    for attempt in range(3):
        print(f"Tentative {attempt + 1}")

        
        if previous_error:
                prompt += f"""
                Your previous response was invalid because:
                {previous_error}

                Correct the error and return valid JSON.
                """
        
        content = call_llm(prompt)
        
        try:
            data = json.loads(content)
            result = NewsAnalysis(**data)
            return result

        except (json.JSONDecodeError, ValidationError) as error:
                previous_error = str(error)
                print(f"Tentative {attempt + 1}/3 échouée : {error}")

    raise RuntimeError("Analysis failed after 3 attempts")

analysis = analyze_news(news)
print(analysis)