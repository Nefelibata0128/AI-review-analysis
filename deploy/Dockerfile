FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY proxy-server.py .
COPY orchestrator.py .
COPY mcp_server.py .
COPY lark_notifier.py .
COPY agents/ ./agents/
COPY report-dashboard.html .

# 暴露端口
EXPOSE 8080
EXPOSE 8081

# 启动主服务 (proxy + orchestrator)
CMD ["python", "proxy-server.py"]
