# agent/main_agent.py (V6 - 记忆功能版)

import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
import time

# --- 配置区 ---
load_dotenv()
TOOL_API_BASE_URL = "https://content-agent.fly.dev"

# 初始化阿里云千问大模型的客户端
api_base_url = os.getenv("QWEN_API_BASE_URL")
api_key = os.getenv("DASHSCOPE_API_KEY")
model_name = os.getenv("QWEN_MODEL_NAME")

if not all([api_base_url, api_key, model_name]):
    raise ValueError("请确保 .env 文件中已正确配置 QWEN_API_BASE_URL, DASHSCOPE_API_KEY, 和 QWEN_MODEL_NAME")

client = OpenAI(
    api_key=api_key,
    base_url=api_base_url,
)

# 向大模型描述我们拥有的所有工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "当需要获取实时信息、近期事件或模型知识库以外的深度资料时，使用此工具进行网页搜索。",
            "parameters": {
                "type": "object", "properties": {"query": {"type": "string", "description": "需要搜索的关键词或问题。"}}, "required": ["query"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_seo_keywords",
            "description": "分析一段给定的文本，计算总词数和指定关键词列表的词频密度。",
            "parameters": {
                "type": "object", "properties": {"text": {"type": "string", "description": "需要被分析的完整文章内容。"}, "keywords": {"type": "array", "items": {"type": "string"}}}, "required": ["text", "keywords"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "publish_article",
            "description": "当用户明确表示要'发布'时，调用此工具将文章发布。",
            "parameters": {
                "type": "object", "properties": {"title": {"type": "string", "description": "文章的标题。"}, "content": {"type": "string", "description": "文章的完整内容。"}}, "required": ["title", "content"],
            },
        }
    },
]

# --- 行动函数 ---
def call_tool(tool_call):
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    endpoint_map = { "web_search": "/search", "analyze_seo_keywords": "/analyze", "publish_article": "/publish" }
    endpoint = endpoint_map.get(function_name)
    if not endpoint:
        return json.dumps({"error": f"未知的工具名称: {function_name}"})
    url = f"{TOOL_API_BASE_URL}{endpoint}"
    print(f"  ⚡️ 正在调用云端工具: {url} with args {arguments}")
    try:
        response = requests.post(url, json=arguments, headers={"Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        print(f"  ❌ 工具调用失败: {e}")
        return json.dumps({"error": f"调用工具失败: {e}"})

# --- 大脑中枢 ---
async def process_agent_request(messages: list):
    """
    接收完整的消息历史，并以异步生成器的方式流式返回处理过程。
    """
    yield "状态：正在请求大模型进行决策...\n"
    
    # === 思考 (Reason) ===
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = response.choices[0].message
    messages.append(response_message)

    # === 行动 (Act) ===
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            yield f"状态：模型决定调用工具 -> {function_name}...\n"
            tool_response_str = call_tool(tool_call)
            try:
                tool_response_json = json.loads(tool_response_str)
                summary = str(tool_response_json)[:100]
                yield f"状态：工具 {function_name} 返回结果 -> {summary}...\n"
            except json.JSONDecodeError:
                yield f"状态：工具 {function_name} 返回了非JSON格式的结果。\n"
            messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": tool_response_str})
        
        # === 再思考 (Re-Reason) ===
        yield "状态：正在根据工具结果，请求大模型进行最终总结...\n"
        final_response_stream = client.chat.completions.create(
            model=model_name, messages=messages, stream=True
        )
        yield "答案："
        for chunk in final_response_stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    else:
        yield "状态：无需使用工具，正在直接生成回答...\n"
        response_stream = client.chat.completions.create(
            model=model_name, messages=messages, stream=True
        )
        yield "答案："
        for chunk in response_stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content