# Dockerfile

# 使用官方的 Python 3.10 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有项目文件
COPY . .

# 暴露端口 (Fly.io 内部会处理端口映射)
EXPOSE 8080

# 启动命令
CMD ["uvicorn", "plugins.seo_analyzer:app", "--host", "0.0.0.0", "--port", "8080"]