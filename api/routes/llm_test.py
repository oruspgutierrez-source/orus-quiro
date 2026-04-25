from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.services.gemini_client import generate_response

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str

@router.post("/health/llm")
async def test_llm(request: PromptRequest):
    try:
        response_text = await generate_response(request.prompt)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")
