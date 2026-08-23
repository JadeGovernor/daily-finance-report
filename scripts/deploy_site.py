"""把最新一期报告发布到公网静态站（GitHub Pages）。

从 output/report.html 构建：
  index.html             = 最新一期（含顶部「历史往期」导航）
  archive.html           = 历史往期列表
  archive/YYYY-MM-DD.html = 每日快照（保留最近 90 天）
然后推送到公开网站仓库 daily-finance-report-site 的 main 分支。
"""
import html as html_mod
import os
import pathlib
import re
import shutil
import subprocess
import sys

SITE_REPO = "JadeGovernor/daily-finance-report-site"
BRANCH = "main"
SRC = pathlib.Path("output/report.html")
BUILD = pathlib.Path("/tmp/che-site")
KEEP_DAYS = 90

GATE_HASH = "f00d0e94577089bd5d28080bb3d42c62e74c4527887909b2370e222835db6603"  # SHA-256("CHEZHI")

GATE_STYLE = """
<style>
#che-gate{position:fixed;inset:0;z-index:99999;background:#f5f6f8;display:flex;align-items:center;justify-content:center;font-family:-apple-system,'PingFang SC',sans-serif}
#che-gate .box{background:#fff;border:1px solid #e0e0e0;border-radius:12px;padding:32px 28px;width:320px;box-shadow:0 8px 30px rgba(0,0,0,.08);text-align:center}
#che-gate h1{font-size:20px;margin:0 0 6px;color:#222}
#che-gate p{font-size:13px;color:#888;margin:0 0 16px}
#che-gate input{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #d0d0d0;border-radius:8px;font-size:15px;outline:none}
#che-gate input:focus{border-color:#1565c0}
#che-gate button{width:100%;margin-top:12px;padding:10px;border:0;border-radius:8px;background:#1565c0;color:#fff;font-size:15px;cursor:pointer}
#che-gate .err{color:#c62828;font-size:13px;margin-top:10px;min-height:18px}
</style>
"""

GATE_DIV = """
<div id="che-gate"><div class="box"><h1>🔒 CHE直早报</h1><p>请输入访问密码</p>
<form id="che-form" autocomplete="off"><input id="che-pass" type="password" placeholder="访问密码" />
<button type="submit">进入</button></form><div class="err" id="che-err"></div></div></div>
"""

GATE_SCRIPT = """
<script>
(function(){
  var HASH = "f00d0e94577089bd5d28080bb3d42c62e74c4527887909b2370e222835db6603";
  var gate = document.getElementById("che-gate");
  var form = document.getElementById("che-form");
  var input = document.getElementById("che-pass");
  var err = document.getElementById("che-err");
  function unlock(){ if (gate) gate.style.display = "none"; }
  if (sessionStorage.getItem("che_unlocked") === "1") { unlock(); return; }
  function hex(buf){ return Array.prototype.map.call(new Uint8Array(buf), function(b){ return b.toString(16).padStart(2,"0"); }).join(""); }
  form.addEventListener("submit", function(e){
    e.preventDefault();
    var v = (input.value || "").trim();
    if (!v) return;
    if (!window.crypto || !window.crypto.subtle) { err.textContent = "当前浏览器不支持加密校验，请更换浏览器"; return; }
    crypto.subtle.digest("SHA-256", new TextEncoder().encode(v)).then(function(buf){
      if (hex(buf) === HASH) { sessionStorage.setItem("che_unlocked", "1"); unlock(); }
      else { err.textContent = "密码错误，请重试"; input.value = ""; input.focus(); }
    });
  });
})();
</script>
"""

NAV = (
    '<div style="max-width:860px;margin:0 auto;padding:10px 16px 0;font-size:13px;'
    'font-family:-apple-system,\'PingFang SC\',sans-serif">'
    '<a href="archive.html" style="color:#1565c0;text-decoration:none">📅 历史往期</a></div>'
)


def _with_nav(content: str) -> str:
    return re.sub(r"(<body[^>]*>)", r"\1" + NAV, content, count=1)


def _with_gate(content: str) -> str:
    if "che-gate" in content:
        return content
    content = content.replace("<head>", "<head>" + GATE_STYLE, 1)
    content = re.sub(r"(<body[^>]*>)", r"\1" + GATE_DIV, content, count=1)
    content = content.replace("</body>", GATE_SCRIPT + "</body>", 1)
    return content


def _protect(content: str) -> str:
    return _with_gate(_with_nav(content))


def _report_date(content: str) -> str:
    m = re.search(r"CHE直早报\s*(\d{4}-\d{2}-\d{2})", content)
    if m:
        return m.group(1)
    import datetime
    return datetime.date.today().isoformat()


def build() -> pathlib.Path:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    (BUILD / "archive").mkdir(parents=True)
    content = SRC.read_text(encoding="utf-8")
    date_str = _report_date(content)
    (BUILD / "index.html").write_text(_protect(content), encoding="utf-8")
    (BUILD / "archive" / f"{date_str}.html").write_text(_protect(content), encoding="utf-8")

    archives = sorted((BUILD / "archive").glob("*.html"), reverse=True)
    rows = "\n".join(
        f'<li><a href="archive/{f.name}">{f.stem}</a></li>' for f in archives[:KEEP_DAYS]
    )
    index = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>CHE直早报 · 历史往期</title></head>
<body style="font-family:-apple-system,'PingFang SC',sans-serif;background:#fafafa;padding:24px">
<div style="max-width:640px;margin:0 auto;background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:20px">
<h1 style="font-size:20px;color:#333">📬 CHE直早报 · 历史往期</h1>
<p style="color:#666;font-size:13px">每日约 8:30 更新 · 数据来自公开网络，不构成投资建议</p>
<ol style="line-height:1.9">{rows}</ol>
<p style="margin-top:18px"><a href="index.html" style="color:#1565c0">← 返回最新一期</a></p>
</div></body></html>"""
    (BUILD / "archive.html").write_text(_protect(index), encoding="utf-8")
    return BUILD


def git_push(build: pathlib.Path) -> None:
    token = os.environ.get("SITE_DEPLOY_TOKEN", "")
    if not token:
        raise RuntimeError("缺少环境变量 SITE_DEPLOY_TOKEN")
    env = dict(os.environ)
    cmds = [
        ["git", "init", "-b", BRANCH],
        ["git", "config", "user.name", "JadeGovernor"],
        ["git", "config", "user.email", "jadegovernor@users.noreply.github.com"],
        ["git", "add", "-A"],
        ["git", "commit", "-m", "deploy: CHE直早报 更新", "--allow-empty"],
        ["git", "remote", "add", "origin",
         f"https://x-access-token:{token}@github.com/{SITE_REPO}.git"],
        ["git", "push", "-f", "origin", BRANCH],
    ]
    for cmd in cmds:
        subprocess.run(cmd, cwd=build, env=env, check=True, capture_output=True)


def main() -> int:
    if not SRC.exists():
        print("未找到 output/report.html，跳过发布")
        return 0
    build_dir = build()
    git_push(build_dir)
    print(f"已发布到 https://github.com/{SITE_REPO} （index + archive/{KEEP_DAYS} 天）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
