"""
VaaniSeva — Local Activity Dashboard
=====================================
Run: python scripts/dashboard.py
Opens a browser at http://localhost:5050 showing all call/chat activity.
Press Ctrl+C to stop.
"""

import os, json, datetime, http.server, threading, webbrowser
import boto3
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv(override=True)

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
PORT = 5050


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError


def fetch_data():
    ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = ddb.Table("vaaniseva-calls")

    items = []
    resp = table.scan()
    items += resp["Items"]
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items += resp["Items"]

    # Filter out background job entries and empty sessions
    calls = []
    for item in items:
        cid = str(item.get("call_id", ""))
        if cid.startswith("job#"):
            continue
        hist_raw = item.get("conversation_history", "[]")
        try:
            hist = json.loads(hist_raw) if isinstance(hist_raw, str) else hist_raw
        except Exception:
            hist = []
        turns = len(hist) if isinstance(hist, list) else 0

        ts = int(item.get("timestamp", 0))
        dt = datetime.datetime.fromtimestamp(ts) if ts else None

        calls.append({
            "call_id":    cid,
            "from":       str(item.get("from_number", "Unknown")),
            "language":   str(item.get("language", "?")),
            "status":     str(item.get("status", "?")),
            "source":     str(item.get("source", "phone")),
            "queries":    int(str(item.get("queries_count", 0))),
            "turns":      turns,
            "timestamp":  ts,
            "datetime":   dt.strftime("%d %b %Y, %H:%M:%S") if dt else "Unknown",
            "history":    hist if isinstance(hist, list) else [],
            "voice":      str(item.get("voice_speaker", "")),
        })

    calls.sort(key=lambda x: x["timestamp"], reverse=True)
    return calls


def build_html(calls):
    total        = len(calls)
    with_queries = sum(1 for c in calls if c["queries"] > 0)
    phone_calls  = sum(1 for c in calls if c["source"] == "phone")
    web_sessions = sum(1 for c in calls if c["source"] != "phone")
    langs        = {}
    for c in calls:
        langs[c["language"]] = langs.get(c["language"], 0) + 1
    lang_str = " &nbsp;|&nbsp; ".join(f"<b>{k.upper()}</b>: {v}" for k, v in sorted(langs.items(), key=lambda x: -x[1]))

    rows = ""
    for c in calls:
        lang_badge = {"hi": "#f97316", "en": "#3b82f6", "mr": "#8b5cf6", "ta": "#10b981"}.get(c["language"], "#6b7280")
        src_icon = "📞" if c["source"] == "phone" else "🌐"
        status_color = {"completed": "#10b981", "in-progress": "#f59e0b", "web-callback": "#3b82f6"}.get(c["status"], "#6b7280")

        # Build collapsible chat history
        history_html = ""
        for turn in c["history"]:
            q = str(turn.get("query", "")).replace("<", "&lt;").replace(">", "&gt;")
            a = str(turn.get("answer", "")).replace("<", "&lt;").replace(">", "&gt;")
            history_html += f"""
            <div class="turn">
              <div class="user-msg">🎤 {q}</div>
              <div class="bot-msg">🤖 {a}</div>
            </div>"""

        if history_html:
            detail_id = f"detail_{c['call_id'].replace('-','_').replace('#','_')}"
            expand_btn = f'<button class="expand-btn" onclick="toggle(\'{detail_id}\')">▶ {c["turns"]} turns</button>'
            history_block = f'<div id="{detail_id}" class="history-panel" style="display:none">{history_html}</div>'
        else:
            expand_btn = f'<span class="dim">{c["turns"]} turns</span>'
            history_block = ""

        rows += f"""
        <tr>
          <td class="mono dim">{c["datetime"]}</td>
          <td>{src_icon} <span class="mono small">{c["from"]}</span></td>
          <td><span class="badge" style="background:{lang_badge}">{c["language"].upper()}</span></td>
          <td><span style="color:{status_color}">●</span> {c["status"]}</td>
          <td class="center">{c["queries"]}</td>
          <td class="center">{expand_btn}{history_block}</td>
          <td class="mono dim small">{c["call_id"][:28]}</td>
        </tr>"""

    refreshed = datetime.datetime.now().strftime("%d %b %Y %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VaaniSeva Dashboard</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e2e8f0; min-height: 100vh; }}
  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 24px 32px; border-bottom: 1px solid #2d3748; }}
  .header h1 {{ font-size: 1.6rem; font-weight: 700; color: #f0a832; letter-spacing: -0.5px; }}
  .header .sub {{ color: #94a3b8; font-size: 0.85rem; margin-top: 4px; }}
  .stats {{ display: flex; gap: 16px; padding: 20px 32px; flex-wrap: wrap; }}
  .stat-card {{ background: #1e2433; border: 1px solid #2d3748; border-radius: 10px; padding: 16px 22px; min-width: 140px; }}
  .stat-card .val {{ font-size: 2rem; font-weight: 700; color: #f0a832; }}
  .stat-card .lbl {{ font-size: 0.78rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }}
  .lang-row {{ padding: 0 32px 16px; font-size: 0.85rem; color: #94a3b8; }}
  .table-wrap {{ padding: 0 32px 32px; overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
  th {{ background: #1e2433; color: #94a3b8; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; padding: 10px 14px; text-align: left; border-bottom: 1px solid #2d3748; }}
  td {{ padding: 10px 14px; border-bottom: 1px solid #1e2433; vertical-align: top; }}
  tr:hover td {{ background: #1a2234; }}
  .mono {{ font-family: 'SF Mono', 'Fira Code', monospace; }}
  .small {{ font-size: 0.78rem; }}
  .dim {{ color: #64748b; }}
  .center {{ text-align: center; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; color: white; }}
  .expand-btn {{ background: #2d3748; border: none; color: #94a3b8; padding: 3px 10px; border-radius: 4px; cursor: pointer; font-size: 0.78rem; }}
  .expand-btn:hover {{ background: #374151; color: #e2e8f0; }}
  .history-panel {{ margin-top: 8px; border-left: 2px solid #374151; padding-left: 12px; }}
  .turn {{ margin-bottom: 10px; }}
  .user-msg {{ background: #1e2d40; border-radius: 6px; padding: 6px 10px; margin-bottom: 4px; color: #93c5fd; font-size: 0.82rem; }}
  .bot-msg {{ background: #1c2b1e; border-radius: 6px; padding: 6px 10px; color: #86efac; font-size: 0.82rem; }}
  .refresh-bar {{ text-align: right; padding: 8px 32px; font-size: 0.75rem; color: #475569; }}
  a {{ color: #f0a832; text-decoration: none; }}
</style>
</head>
<body>
<div class="header">
  <h1>⚡ VaaniSeva — Activity Dashboard</h1>
  <div class="sub">Live view of all calls &amp; conversations · <a href="/" onclick="location.reload()">↻ Refresh</a></div>
</div>
<div class="refresh-bar">Last updated: {refreshed}</div>
<div class="stats">
  <div class="stat-card"><div class="val">{total}</div><div class="lbl">Total Sessions</div></div>
  <div class="stat-card"><div class="val">{with_queries}</div><div class="lbl">Real Convos</div></div>
  <div class="stat-card"><div class="val">{phone_calls}</div><div class="lbl">📞 Phone Calls</div></div>
  <div class="stat-card"><div class="val">{web_sessions}</div><div class="lbl">🌐 Web Sessions</div></div>
</div>
<div class="lang-row">Languages: {lang_str}</div>
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Time</th><th>Caller</th><th>Lang</th><th>Status</th><th>Queries</th><th>Conversation</th><th>Session ID</th>
      </tr>
    </thead>
    <tbody>
      {rows if rows else '<tr><td colspan="7" style="text-align:center;color:#64748b;padding:40px">No conversations yet</td></tr>'}
    </tbody>
  </table>
</div>
<script>
function toggle(id) {{
  var el = document.getElementById(id);
  var btn = el.previousElementSibling;
  if (el.style.display === 'none') {{
    el.style.display = 'block';
    btn.textContent = btn.textContent.replace('▶', '▼');
  }} else {{
    el.style.display = 'none';
    btn.textContent = btn.textContent.replace('▼', '▶');
  }}
}}
// Auto-refresh every 60 seconds
setTimeout(() => location.reload(), 60000);
</script>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"  Fetching data from DynamoDB...")
        try:
            calls = fetch_data()
            html  = build_html(calls)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            print(f"  Served dashboard: {len(calls)} sessions")
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode())
            print(f"  ERROR: {e}")

    def log_message(self, format, *args):
        pass  # suppress default access log noise


if __name__ == "__main__":
    server = http.server.HTTPServer(("localhost", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"\n  VaaniSeva Dashboard running at {url}")
    print(f"  Fetches live data from DynamoDB on every page load")
    print(f"  Press Ctrl+C to stop\n")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Dashboard stopped.")
