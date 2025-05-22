from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from perplexity_async.client import Client

app = FastAPI()

class ChatRequest(BaseModel):
    query: str = Field(..., description="The search query for Perplexity.")
    cookies: Dict[str, str] = Field(..., description="Cookies to be used for the Perplexity client session.")

class TestChatRequest(BaseModel):
    query: str = Field(..., description="The search query for Perplexity.")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        client = await Client(cookies=request.cookies)
        response = await client.search(query=request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-chat")
async def test_chat_endpoint(request: TestChatRequest):
    try:
        client = await Client(cookies={})
        response = await client.search(query=request.query, mode='auto')
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
