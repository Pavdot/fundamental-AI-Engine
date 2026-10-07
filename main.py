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


def analyze_news(news):
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this financial news

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
- horizon_hours must be a number"""
            }
        ]
    )
    content = response.choices[0].message.content

    try:
        data = json.loads(content)
        result = NewsAnalysis(**data)
        return result
    except json.JSONDecodeError as error:
        print("JSON error:", error)
        return None
    except ValidationError as error:
        print("Validation error:", error)
        return None

AAnalysis = analyze_news(news)
print(AAnalysis)