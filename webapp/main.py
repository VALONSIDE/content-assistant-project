# webapp/main.py (V2 - 支持流式响应)

import sys
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 导入新的 agent 函数
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.main_agent import run_agent_stream

app = FastAPI(title="内容创作助手")
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

class ChatRequest(BaseModel):
    prompt: str

# 【核心升级】使用 StreamingResponse
@app.post("/chat")
async def handle_chat_stream(chat_request: ChatRequest):
    user_prompt = chat_request.prompt
    
    async def event_stream():
        # run_agent_stream 是一个生成器 (generator)
        for chunk in run_agent_stream(user_prompt):
            yield chunk
            await asyncio.sleep(0.01) # 稍微暂停，让事件循环有机会处理其他事

    return StreamingResponse(event_stream(), media_type="text/plain")