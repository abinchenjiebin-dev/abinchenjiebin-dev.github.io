"""越南语学堂 - 网页版本地运行 / 自测脚本（只需要 Python 3.8+，不用装任何库）

在 VS Code 里：打开本文件 → 点右上角 ▶「运行 Python 文件」即可。
或在终端里（本文件所在文件夹）：
    python run.py          启动并自动打开浏览器
    python run.py --test   自测
"""
import http.server
import os
import re
import socket
import socketserver
import sys
import threading
import time
import urllib.request
import webbrowser

# Windows 中文系统的终端默认是 GBK 编码，打印越南语会报错，这里统一改成 UTF-8
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

ROOT = os.path.dirname(os.path.abspath(__file__))  # 不管从哪里运行，都以本文件所在文件夹为准
ROUTES = ["/", "/learn", "/levels", "/practice", "/pronounce", "/review", "/mistakes", "/search", "/quiz/meaning", "/compounds", "/sentences", "/topic/greetings", "/cards/food", "/settings", "/videos", "/video/BV1LE411d7WE", "/level/u2-w1", "/dialogues", "/dialogue/market", "/shadow/food", "/word/xe%20m%C3%A1y"]
EXPECT_IN_BUNDLE = ["Xin chào.", "Cái này bao nhiêu tiền?", "máy bay", "Tôi không hiểu.", "vi-VN"]


class Handler(http.server.SimpleHTTPRequestHandler):
    # Windows 注册表里 .js 有时被登记成 text/plain，浏览器会拒绝执行，这里写死正确类型
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".json": "application/json",
        ".css": "text/css",
        ".html": "text/html; charset=utf-8",
        ".ttf": "font/ttf",
        ".png": "image/png",
        ".ico": "image/x-icon",
    }

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def translate_path(self, path):
        full = super().translate_path(path)
        if not os.path.exists(full):  # /phrases 等地址交给 App 自己处理
            return os.path.join(ROOT, "index.html")
        return full

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def free_port(start=8000):
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("找不到可用端口")


def serve(port):
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def get(port, path):
    return urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=10).read().decode("utf-8")


def check(name, passed):
    print(("[通过] " if passed else "[失败] ") + name)
    return passed


def self_test():
    print(f"Python {sys.version.split()[0]}，目录：{ROOT}\n")
    ok = check("找到 index.html", os.path.exists(os.path.join(ROOT, "index.html")))
    if not ok:
        print("\n请确认 run.py 和 index.html、_expo 文件夹放在同一个文件夹里（先完整解压 zip）。")
        return 1
    port = free_port(8100)
    httpd = serve(port)
    for r in ROUTES:
        try:
            ok &= check(f"页面 {r} 可以打开", 'id="root"' in get(port, r))
        except Exception as e:  # noqa: BLE001
            ok &= check(f"页面 {r} 可以打开（{e}）", False)
    html = get(port, "/")
    m = re.search(r"(_expo/static/js/web/[^\"']+\.js)", html)
    ok &= check("找到程序文件", bool(m))
    if m:
        bundle = get(port, "/" + m.group(1))
        bundle = re.sub(r"\\u([0-9a-fA-F]{4})", lambda x: chr(int(x.group(1), 16)), bundle)
        bundle = re.sub(r"\\x([0-9a-fA-F]{2})", lambda x: chr(int(x.group(1), 16)), bundle)
        for text in EXPECT_IN_BUNDLE:
            ok &= check(f"内容包含「{text}」", text in bundle)
    httpd.shutdown()
    print("\n全部通过！" if ok else "\n有检查没通过，请把上面的输出截图发给我。")
    return 0 if ok else 1


def main():
    if "--test" in sys.argv:
        sys.exit(self_test())
    if not os.path.exists(os.path.join(ROOT, "index.html")):
        print("找不到 index.html：请先把 zip 完整解压，再运行解压后文件夹里的 run.py。")
        sys.exit(1)
    port = free_port(8000)
    serve(port)
    url = f"http://127.0.0.1:{port}/"
    print("=" * 50)
    print(f"越南语学堂已启动： {url}")
    print("浏览器没有自动打开的话，手动复制上面的地址打开。")
    print("推荐用 Edge 浏览器（自带越南语发音）。")
    print("关闭：在这个终端按 Ctrl+C（或点 VS Code 终端的垃圾桶图标）")
    print("=" * 50)
    webbrowser.open(url)
    try:
        while True:  # Windows 上用 sleep 循环，Ctrl+C 才能正常退出
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("已退出")


if __name__ == "__main__":
    main()
