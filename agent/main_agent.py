# agent/main_agent.py (V5 - 支持流式汇报)

import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
import time

# --- 配置区 (无变化) ---
load_dotenv()
TOOL_API_BASE_URL = "https://content-agent.fly.dev"
client = OpenAI(...)
tools = [...] # 省略未变动的配置和工具定义

# --- 行动函数 (无变化) ---
def call_tool(tool_call):
    # ... (这部分代码保持不变) ...
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    endpoint_map = {
        "web_search": "/search",
        "analyze_seo_keywords": "/analyze",
        "publish_article": "/publish",
    }
    endpoint = endpoint_map.get(function_name)
    if not endpoint:
        return json.dumps({"error": f"未知的工具名称: {function_name}"})
    url = f"{TOOL_API_BASE_URL}{endpoint}"
    try:
        response = requests.post(url, json=arguments, headers={"Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()
        return json.dumps(response.json())
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": f"调用工具失败: {e}"})

# --- 【核心升级】大脑中枢，使用 yield 实现流式输出 ---
def run_agent_stream(user_prompt: str):
    """
    运行Agent，并以流式方式(yield)产出每一步的状态更新。
    """
    yield "状态：正在理解您的问题...\n"
    
    messages = [
        {"role": "system", "content": "你是一个全能的内容创作助手..."},
        {"role": "user", "content": user_prompt},
    ]

    # === 思考 (Reason) ===
    yield "状态：正在请求大模型进行决策...\n"
    response = client.chat.completions.create(
        model=os.getenv("QWEN_MODEL_NAME"),
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
            
            # 尝试解析工具返回的JSON，提取关键信息进行汇报
            try:
                tool_response_json = json.loads(tool_response_str)
                # 截取一部分结果展示，避免过长
                summary = str(tool_response_json)[:100] 
                yield f"状态：工具 {function_name} 返回结果 -> {summary}...\n"
            except json.JSONDecodeError:
                yield f"状态：工具 {function_name} 返回了非JSON格式的结果。\n"

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": tool_response_str,
            })
        
        # === 再思考 (Re-Reason) ===
        yield "状态：正在根据工具结果，请求大模型进行最终总结...\n"
        
        # 【重要】为了实现最终答案的滚动输出，这里也需要使用 stream=True
        final_response_stream = client.chat.completions.create(
            model=os.getenv("QWEN_MODEL_NAME"),
            messages=messages,
            stream=True # 开启流式输出
        )
        
        yield "答案：" # 这是一个特殊标记，告诉前端，后面开始是正式答案了
        for chunk in final_response_stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    else:
        # 如果不调用工具，直接流式输出答案
        yield "状态：无需使用工具，正在直接生成回答...\n"
        response_stream = client.chat.completions.create(
            model=os.getenv("QWEN_MODEL_NAME"),
            messages=messages,
            stream=True
        )
        yield "答案："
        for chunk in response_stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content