"""
web_ui.py - Local web UI for SimpleLang: a code box + a run button + output.

Usage:
    python web_ui.py [port]

Then open http://localhost:<port> in a browser. No external dependencies
(stdlib only), matching the rest of the project.
"""

import html
import io
import json
import os
import re
import sys
import webbrowser
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from lexer import Lexer, LexError
from parser import Parser, ParseError
from interpreter import Interpreter, RuntimeErrorSL

GUIDE_PATH = Path(__file__).with_name("GUIDE.md")


def _inline_md(text):
    """Applies inline markdown (inline code, bold) to already-escaped text."""
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def markdown_to_html(source: str) -> str:
    """Tiny stdlib-only Markdown -> HTML renderer covering the subset used by
    GUIDE.md: headers, fenced code blocks, tables, unordered lists, horizontal
    rules, inline code, and bold."""
    lines = source.split("\n")
    out = []
    i, n = 0, len(lines)

    while i < n:
        stripped = lines[i].strip()

        if stripped.startswith("```"):
            i += 1
            code_lines = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
            continue

        if stripped in ("---", "***", "___"):
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")), 6)
            text = stripped[level:].strip()
            out.append(f"<h{level}>{_inline_md(text)}</h{level}>")
            i += 1
            continue

        if stripped.startswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = [[c.strip() for c in row.strip("|").split("|")] for row in table_lines]
            header, *rest = rows
            body_rows = [r for r in rest if not all(set(c) <= set("-: ") for c in r)]
            out.append("<table><thead><tr>")
            out.extend(f"<th>{_inline_md(c)}</th>" for c in header)
            out.append("</tr></thead><tbody>")
            for row in body_rows:
                out.append("<tr>" + "".join(f"<td>{_inline_md(c)}</td>" for c in row) + "</tr>")
            out.append("</tbody></table>")
            continue

        if stripped.startswith("- "):
            items = []
            while i < n and lines[i].strip().startswith("- "):
                items.append(lines[i].strip()[2:])
                i += 1
            out.append("<ul>" + "".join(f"<li>{_inline_md(item)}</li>" for item in items) + "</ul>")
            continue

        if stripped == "":
            i += 1
            continue

        para_lines = []
        while i < n and lines[i].strip() and not lines[i].strip().startswith(("```", "#", "|", "- ")) \
                and lines[i].strip() not in ("---", "***", "___"):
            para_lines.append(lines[i].strip())
            i += 1
        out.append(f"<p>{_inline_md(' '.join(para_lines))}</p>")

    return "\n".join(out)


def load_guide_html() -> str:
    try:
        return markdown_to_html(GUIDE_PATH.read_text(encoding="utf-8"))
    except OSError:
        return "<p>GUIDE.md not found.</p>"


GUIDE_HTML = load_guide_html()

DEFAULT_CODE = """# Enter your code. Refer to GUIDE for syntax"""

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SimpleLang Playground</title>
<style>
  :root {
    --bg: #1e1e2e;
    --panel: #26263a;
    --border: #3a3a52;
    --text: #e4e4f0;
    --muted: #9090aa;
    --accent: #7c5cff;
    --accent-hover: #9070ff;
    --error: #ff6b6b;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
  header {
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
  }
  header h1 {
    font-size: 16px;
    margin: 0;
    font-weight: 600;
  }
  header .sub {
    color: var(--muted);
    font-size: 12px;
  }
  main {
    flex: 1;
    display: flex;
    min-height: 0;
  }
  .pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .pane + .pane {
    border-left: 1px solid var(--border);
  }
  .pane-header {
    padding: 8px 14px;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  textarea {
    flex: 1;
    resize: none;
    border: none;
    outline: none;
    background: var(--panel);
    color: var(--text);
    font-family: "SF Mono", Consolas, "Cascadia Code", monospace;
    font-size: 14px;
    line-height: 1.5;
    padding: 14px;
    tab-size: 4;
  }
  #output {
    flex: 1;
    margin: 0;
    padding: 14px;
    overflow: auto;
    font-family: "SF Mono", Consolas, "Cascadia Code", monospace;
    font-size: 14px;
    line-height: 1.5;
    background: var(--panel);
    white-space: pre-wrap;
    word-break: break-word;
  }
  #output.error { color: var(--error); }
  #output.empty { color: var(--muted); }
  button {
    background: var(--accent);
    color: white;
    border: none;
    padding: 7px 16px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
  }
  button:hover { background: var(--accent-hover); }
  button:active { transform: translateY(1px); }
  .ghost-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text);
  }
  .ghost-btn:hover { background: transparent; border-color: var(--accent); color: var(--accent); }
  .hint {
    color: var(--muted);
    font-size: 12px;
    margin-left: auto;
  }
  .guide-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }
  .guide-overlay.hidden { display: none; }
  .guide-panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    width: min(820px, 92vw);
    height: 86vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  .guide-panel-header {
    padding: 12px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
  }
  .guide-content {
    padding: 8px 26px 28px;
    overflow-y: auto;
    line-height: 1.65;
  }
  .guide-content h1, .guide-content h2, .guide-content h3 {
    color: var(--text);
    margin: 26px 0 10px;
  }
  .guide-content h1 { font-size: 22px; }
  .guide-content h2 { font-size: 18px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
  .guide-content h3 { font-size: 15px; color: var(--muted); }
  .guide-content p, .guide-content li { font-size: 14px; }
  .guide-content code {
    font-family: "SF Mono", Consolas, "Cascadia Code", monospace;
    background: var(--bg);
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 13px;
  }
  .guide-content pre {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 14px;
    overflow-x: auto;
  }
  .guide-content pre code { background: none; padding: 0; }
  .guide-content table { border-collapse: collapse; width: 100%; margin: 12px 0; }
  .guide-content th, .guide-content td {
    border: 1px solid var(--border);
    padding: 6px 10px;
    font-size: 13px;
    text-align: left;
  }
  .guide-content hr { border: none; border-top: 1px solid var(--border); margin: 22px 0; }
  .guide-content ul { padding-left: 22px; }
</style>
</head>
<body>
<header>
  <h1>SimpleLang Playground</h1>
  <span class="sub">write .sl code, run it, see the output</span>
  <button id="guideBtn" class="ghost-btn">Guide</button>
  <span class="hint">Ctrl / Cmd + Enter to run</span>
</header>
<main>
  <div class="pane">
    <div class="pane-header">
      <span>Code</span>
      <button id="run">Run ▶</button>
    </div>
    <textarea id="code" spellcheck="false"></textarea>
  </div>
  <div class="pane">
    <div class="pane-header"><span>Output</span></div>
    <pre id="output" class="empty">Output will appear here.</pre>
  </div>
</main>
<div id="guideOverlay" class="guide-overlay hidden">
  <div class="guide-panel">
    <div class="guide-panel-header">
      <span>Language Guide</span>
      <button id="closeGuide" class="ghost-btn">Close ✕</button>
    </div>
    <div class="guide-content">${GUIDE_HTML}</div>
  </div>
</div>
<script>
const codeEl = document.getElementById('code');
const outEl = document.getElementById('output');
const runBtn = document.getElementById('run');

codeEl.value = ${DEFAULT_CODE_JSON};

async function run() {
  outEl.classList.remove('error', 'empty');
  outEl.textContent = 'Running...';
  try {
    const res = await fetch('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: codeEl.value }),
    });
    const data = await res.json();
    if (data.error) {
      outEl.classList.add('error');
      outEl.textContent = data.output || '(error, no message)';
    } else {
      outEl.classList.remove('error');
      const text = data.output;
      if (!text) {
        outEl.classList.add('empty');
        outEl.textContent = '(no output)';
      } else {
        outEl.textContent = text;
      }
    }
  } catch (e) {
    outEl.classList.add('error');
    outEl.textContent = 'Request failed: ' + e;
  }
}

runBtn.addEventListener('click', run);
codeEl.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    run();
  }
});

const guideBtn = document.getElementById('guideBtn');
const guideOverlay = document.getElementById('guideOverlay');
const closeGuideBtn = document.getElementById('closeGuide');

guideBtn.addEventListener('click', () => guideOverlay.classList.remove('hidden'));
closeGuideBtn.addEventListener('click', () => guideOverlay.classList.add('hidden'));
guideOverlay.addEventListener('click', (e) => {
  if (e.target === guideOverlay) guideOverlay.classList.add('hidden');
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') guideOverlay.classList.add('hidden');
});
</script>
</body>
</html>
"""


def run_source(source: str):
    """Run SimpleLang source, returning (output_text, is_error)."""
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            tokens = Lexer(source).tokenize()
            program = Parser(tokens).parse()
            Interpreter().run(program)
        return buf.getvalue(), False
    except LexError as e:
        return buf.getvalue() + f"[Lexer error] {e}", True
    except ParseError as e:
        return buf.getvalue() + f"[Parser error] {e}", True
    except RuntimeErrorSL as e:
        return buf.getvalue() + f"[Runtime error] {e}", True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # keep stdout quiet

    def do_GET(self):
        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return
        body = (
            PAGE.replace("${DEFAULT_CODE_JSON}", json.dumps(DEFAULT_CODE))
            .replace("${GUIDE_HTML}", GUIDE_HTML)
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/run":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw or b"{}")
            code = payload.get("code", "")
        except json.JSONDecodeError:
            code = ""
        output, is_error = run_source(code)
        resp = json.dumps({"output": output, "error": is_error}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)


def main():
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 5000))
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(f"SimpleLang Playground running at {url}  (Ctrl+C to stop)")
    if host == "127.0.0.1":
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
