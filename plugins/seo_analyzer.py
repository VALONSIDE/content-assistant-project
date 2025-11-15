# plugins/seo_analyzer.py

# 导入我们需要的库
from fastapi import FastAPI
from pydantic import BaseModel
import re

# 1. 初始化FastAPI应用
# 我们给它起个标题和版本号，这会显示在自动生成的API文档中
app = FastAPI(
    title="SEO Analyzer Plugin",
    description="一个简单的工具，用于分析文本中关键词的密度。",
    version="1.0.0",
)

# 2. 定义输入数据的格式
# 使用Pydantic的BaseModel可以确保输入的数据类型正确
class SeoAnalysisRequest(BaseModel):
    text: str
    keywords: list[str]
    # 添加一个示例，方便在API文档中查看
    class Config:
        schema_extra = {
            "example": {
                "text": "Python is a great programming language. I love programming in Python because Python is versatile.",
                "keywords": ["python", "programming"]
            }
        }

# 3. 定义输出数据的格式
class SeoAnalysisResponse(BaseModel):
    word_count: int
    keyword_density: dict[str, float]


# 4. 创建API端点 (Endpoint)
# @app.post("/analyze") 告诉FastAPI:
# - 这是一个处理POST请求的函数
# - 它的访问路径是 /analyze
@app.post("/analyze", response_model=SeoAnalysisResponse, tags=["Analysis"])
def analyze_seo_keywords(request: SeoAnalysisRequest):
    """
    分析文本，计算总词数和每个关键词的词频密度。
    - **text**: 需要被分析的文章全文。
    - **keywords**: 一个包含关键词字符串的列表。
    """
    text_lower = request.text.lower()
    # 使用正则表达式来分词，效果比简单的 split() 更好
    words = re.findall(r'\b\w+\b', text_lower)
    word_count = len(words)

    density = {}
    if word_count > 0:
        for keyword in request.keywords:
            keyword_lower = keyword.lower()
            # 计算关键词在词语列表中出现的次数
            count = words.count(keyword_lower)
            # 计算密度百分比，并保留4位小数
            density[keyword] = round((count / word_count) * 100, 4)

    return SeoAnalysisResponse(word_count=word_count, keyword_density=density)

# 5. 添加一个根路径，用于快速检查服务是否存活
@app.get("/", tags=["Health Check"])
def read_root():
    """
    一个简单的健康检查端点。
    """
    return {"status": "ok", "message": "SEO Analyzer Plugin is running!"}