# plugins/seo_analyzer.py (V2 - 三合一增强版)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re
import requests
import os
import json

# --- 初始化与配置 ---
app = FastAPI(
    title="Multi-Tool Content Agent Plugin",
    description="一个为内容创作助手提供多种能力的API服务。",
    version="2.0.0",
)

# 从环境变量中获取 Serper API Key
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# --- 数据模型定义 ---

# SEO 分析工具的模型
class SeoAnalysisRequest(BaseModel):
    text: str
    keywords: list[str]

class SeoAnalysisResponse(BaseModel):
    word_count: int
    keyword_density: dict[str, float]

# 网页搜索工具的模型
class WebSearchRequest(BaseModel):
    query: str

class WebSearchResponse(BaseModel):
    search_results: list[dict]

# 模拟发布工具的模型
class PublishRequest(BaseModel):
    title: str
    content: str

class PublishResponse(BaseModel):
    status: str
    mock_url: str

# --- API 端点实现 ---

# 端点 1: SEO 分析 (已完成)
@app.post("/analyze", response_model=SeoAnalysisResponse, tags=["Analysis"])
def analyze_seo_keywords(request: SeoAnalysisRequest):
    # ... (这部分代码保持不变) ...
    text_lower = request.text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    word_count = len(words)
    density = {}
    if word_count > 0:
        for keyword in request.keywords:
            keyword_lower = keyword.lower()
            count = words.count(keyword_lower)
            density[keyword] = round((count / word_count) * 100, 4)
    return SeoAnalysisResponse(word_count=word_count, keyword_density=density)

# 端点 2: 【新增】网页搜索
@app.post("/search", response_model=WebSearchResponse, tags=["Search"])
def web_search(request: WebSearchRequest):
    """
    根据查询词，调用 Serper API 进行实时网页搜索。
    """
    if not SERPER_API_KEY:
        raise HTTPException(status_code=500, detail="SERPER_API_KEY 未配置")
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": request.query})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        results = response.json()
        
        # 我们只提取前3个结果的关键信息，避免信息过载
        simplified_results = []
        for item in results.get("organic", [])[:3]:
            simplified_results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
            })
        
        return WebSearchResponse(search_results=simplified_results)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"调用搜索API失败: {e}")

# 端点 3: 【新增】模拟发布
@app.post("/publish", response_model=PublishResponse, tags=["Publish"])
def mock_publish(request: PublishRequest):
    """
    模拟将文章发布到一个博客平台。
    """
    print("--- [模拟发布] ---")
    print(f"标题: {request.title}")
    print(f"内容: {request.content[:100]}...")
    print("--- [发布成功] ---")
    
    # 返回一个虚构的成功信息和URL
    return PublishResponse(
        status="success",
        mock_url=f"https://my-fake-blog.com/posts/{request.title.replace(' ', '-').lower()}"
    )

# 根路径
@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "Multi-Tool Content Agent Plugin is running!"}