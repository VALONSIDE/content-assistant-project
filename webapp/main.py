# webapp/main.py (V3 - 记忆功能版)

import sys
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 【重要】我们将直接调用 Agent 的核心处理逻辑
from agent.main_agent import process_agent_request

app = FastAPI(title="内容创作助手")
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")

# 允许所有来源的跨域请求（开发阶段使用，生产环境请根据需要调整）
origins = [
    "*"  # 允许所有来源，对于这个项目是安全的。未来可以替换为您的Netlify网址。
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 允许所有方法 (GET, POST, etc.)
    allow_headers=["*"], # 允许所有请求头
)

# 【新增】一个简单的、存在于内存中的“记忆库” (Python 字典)
# Key: session_id, Value: message_history_list
chat_sessions = {}

# 1. 根路径 (无变化)
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 2. 更新请求模型，加入 session_id
class ChatRequest(BaseModel):
    prompt: str
    session_id: str

# 3. 【核心升级】聊天接口，现在会处理会话历史
@app.post("/chat")
async def handle_chat_stream(chat_request: ChatRequest):
    session_id = chat_request.session_id
    user_prompt = chat_request.prompt
    
    if session_id not in chat_sessions:
        # 【关键修复】我们在这里添加了关于如何总结工具结果的明确指令
        system_prompt = (
            "你是一个全能的内容创作助手。按步骤思考，根据用户的请求，自主决定是否需要、以及如何使用你拥有的工具来完成任务。"
            "你必须记住用户在对话中提到的信息。"
            "【重要规则】当工具执行完毕后，你必须只使用工具返回的结果，为用户生成一个简洁、最终的确认回复。"
            "绝对不要暴露任何关于'工具调用'、'状态'或内部流程的细节，你的回答应该像一个真正的人类助手一样自然。"
        )
        chat_sessions[session_id] = [
            {"role": "system", "content": system_prompt}
        ]
    
    chat_sessions[session_id].append({"role": "user", "content": user_prompt})

    async def event_stream():
        # ... (后续的 event_stream 逻辑完全保持不变) ...
        ai_full_response = ""
        async for chunk in process_agent_request(chat_sessions[session_id]):
            if not (isinstance(chunk, dict) and chunk.get("type") == "status"):
                 ai_full_response += chunk
            yield chunk
        if ai_full_response:
            chat_sessions[session_id].append({"role": "assistant", "content": ai_full_response})

    return StreamingResponse(event_stream(), media_type="text/plain")