#!/usr/bin/env bash
# CHE直早报 本地执行内核
# 职责：读参数文件 -> 校验 -> 跑 main.py(不推送) -> 记日志 -> 失败重试1次 -> 输出一行JSON摘要
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
PARAMS_FILE="$ROOT/scripts/run_params.json"
RUNS_DIR="$ROOT/runs"
LOG_FILE="$RUNS_DIR/runs.jsonl"
LOG_TMP="$RUNS_DIR/.last_run.log"
PY="$ROOT/.venv311/bin/python"

TRIGGER="${TRIGGER:-manual}"
mkdir -p "$RUNS_DIR"

# ---- 读取并校验参数（limit: 1-200 整数；date: YYYY-MM-DD 或空）----
read_params() {
  if [[ ! -f "$PARAMS_FILE" ]]; then
    echo '{"ok":false,"error":"参数文件不存在: scripts/run_params.json"}'
    return 2
  fi
  "$PY" - "$PARAMS_FILE" <<'PYEOF'
import json, re, sys
path = sys.argv[1]
try:
    d = json.load(open(path, encoding="utf-8"))
except Exception as exc:
    print(json.dumps({"ok": False, "error": f"参数文件解析失败: {exc}"}, ensure_ascii=False))
    sys.exit(2)
limit = d.get("limit", 50)
date = d.get("date") or None
try:
    limit = int(limit)
except (TypeError, ValueError):
    limit = -1
if not (1 <= limit <= 200):
    print(json.dumps({"ok": False, "error": f"limit 必须是 1-200 的整数，收到: {limit!r}"}, ensure_ascii=False))
    sys.exit(2)
if date is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(date)):
    print(json.dumps({"ok": False, "error": f"date 必须是 YYYY-MM-DD 格式，收到: {date!r}"}, ensure_ascii=False))
    sys.exit(2)
print(json.dumps({"ok": True, "limit": limit, "date": date}, ensure_ascii=False))
PYEOF
}

params="$(read_params)" || { echo "$params"; exit 2; }
LIMIT="$(echo "$params" | "$PY" -c "import json,sys; print(json.load(sys.stdin)['limit'])")"
DATE="$(echo "$params" | "$PY" -c "import json,sys; d=json.load(sys.stdin); print(d.get('date') or '')")"

ARGS=(main.py --no-push --limit "$LIMIT")
if [[ -n "$DATE" ]]; then
  ARGS+=(--date "$DATE")
fi

start=$(date +%s)
(cd "$ROOT" && "$PY" "${ARGS[@]}") >"$LOG_TMP" 2>&1
code=$?
if [[ $code -ne 0 ]]; then
  sleep 3
  echo "[auto-retry] 首次运行失败(exit=$code)，3 秒后自动重试..." >>"$LOG_TMP"
  (cd "$ROOT" && "$PY" "${ARGS[@]}") >>"$LOG_TMP" 2>&1
  code=$?
fi
end=$(date +%s)
elapsed=$((end - start))

# ---- 生成日志条目 + 摘要（JSON）----
entry="$("$PY" - "$TRIGGER" "$LIMIT" "$DATE" "$code" "$elapsed" "$LOG_TMP" "$ROOT" <<'PYEOF'
import json, os, sys, datetime
trigger, limit, date, code, elapsed, logtmp, root = sys.argv[1:]
code = int(code)
elapsed = int(elapsed)
tail = ""
if os.path.exists(logtmp):
    with open(logtmp, encoding="utf-8", errors="replace") as f:
        tail = "\n".join(f.read().splitlines()[-15:])
error = None
if code != 0:
    error = (tail[-2000:] if tail else "无日志输出")
report_files = []
out_dir = os.path.join(root, "output")
for name in ("report.html", "report.md"):
    if os.path.exists(os.path.join(out_dir, name)):
        report_files.append(name)
entry = {
    "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "trigger": trigger,
    "params": {"limit": int(limit), "date": date or None},
    "ok": code == 0,
    "exit": code,
    "elapsed_s": elapsed,
    "report_files": report_files,
    "error": error,
}
print(json.dumps(entry, ensure_ascii=False))
PYEOF
)"
echo "$entry" >>"$LOG_FILE"
echo "$entry"
