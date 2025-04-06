FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
# 先安装numpy以确保兼容性
RUN pip install --no-cache-dir numpy==1.24.3
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py

# 暴露端口
EXPOSE 5001

# 启动命令
CMD ["python", "run.py"] 