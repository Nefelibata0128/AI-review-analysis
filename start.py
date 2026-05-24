"""Start server, print port, handle requests"""
import os, sys, json, time, socket

# Find free port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 0))
PORT = s.getsockname()[1]
s.close()

# Load .env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("ps", os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy-server.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

import http.server, socketserver
class TS(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

# Write port to file for discovery
port_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".server_port")
with open(port_file, "w") as f:
    f.write(str(PORT))

print(f"Server: http://localhost:{PORT}", flush=True)
srv = TS(("0.0.0.0", PORT), mod.ProxyHandler)
srv.serve_forever()
