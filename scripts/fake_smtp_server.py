"""本地假 SMTP 服务器：捕获邮件到文件，用于验证发送链路（无需真实邮箱）。

用法：
    python scripts/fake_smtp_server.py [端口] [输出文件]
然后设置环境变量运行 main.py 推送：
    SMTP_HOST=127.0.0.1 SMTP_PORT=1025 SMTP_TLS=none SMTP_USER=test@test.com \
    SMTP_PASS=x MAIL_TO=me@test.com python main.py
"""
import socket
import sys
import threading
from pathlib import Path


class FakeSMTPServer:
    def __init__(self, host="127.0.0.1", port=1025, out_file="captured_email.eml"):
        self.out_file = Path(out_file)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((host, port))
        self.sock.listen(5)
        print(f"[fake-smtp] listening on {host}:{port} -> {self.out_file}", flush=True)

    def _send(self, conn, line):
        conn.sendall((line + "\r\n").encode("utf-8"))

    def handle(self, conn):
        conn.settimeout(30)
        self._send(conn, "220 fake-smtp ready")
        buf = b""
        in_data = False
        try:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buf += data
                lines = buf.split(b"\r\n")
                buf = lines.pop()
                for line in lines:
                    text = line.decode("utf-8", "replace").strip()
                    upper = text.upper()
                    if in_data:
                        if upper == ".":
                            in_data = False
                            self.out_file.write_bytes(prev_data)
                            print(f"[fake-smtp] saved {len(prev_data)} bytes -> {self.out_file}", flush=True)
                            self._send(conn, "250 OK")
                        else:
                            prev_data += (text + "\n").encode("utf-8")
                        continue
                    if upper.startswith("EHLO") or upper.startswith("HELO"):
                        self._send(conn, "250-fake-smtp\r\n250 AUTH PLAIN LOGIN")
                    elif upper.startswith("AUTH"):
                        self._send(conn, "235 2.7.0 Authentication successful")
                    elif upper.startswith("MAIL") or upper.startswith("RCPT"):
                        self._send(conn, "250 OK")
                    elif upper == "DATA":
                        in_data = True
                        prev_data = b""
                        self._send(conn, "354 End data with <CR><LF>.<CR><LF>")
                    elif upper == "QUIT":
                        self._send(conn, "221 Bye")
                        break
                    elif upper == "RSET" or upper == "NOOP":
                        self._send(conn, "250 OK")
        except Exception as exc:  # 客户端断开等，忽略
            print(f"[fake-smtp] connection closed: {exc}", flush=True)
        finally:
            conn.close()

    def serve_forever(self):
        while True:
            conn, _ = self.sock.accept()
            threading.Thread(target=self.handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 1025
    out = sys.argv[2] if len(sys.argv) > 2 else "captured_email.eml"
    FakeSMTPServer(port=port, out_file=out).serve_forever()
