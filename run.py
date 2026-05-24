"""启动脚本 — 加载 .env 并启动 proxy server"""
import os, sys
# Load .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, os.path.dirname(__file__))
import importlib.util
spec = importlib.util.spec_from_file_location("ps", os.path.join(os.path.dirname(__file__), "proxy-server.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Force flush stdout
import sys
print(f"AI评论分析平台 v3.0", flush=True)
print(f"服务地址: http://localhost:{mod.PORT}", flush=True)
print(f"按 Ctrl+C 停止", flush=True)

class TS(mod.socketserver.ThreadingMixIn, mod.http.server.HTTPServer):
    daemon_threads = True
srv = TS(("0.0.0.0", mod.PORT), mod.ProxyHandler)
srv.serve_forever()
