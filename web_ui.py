"""
web_ui.py - Local web UI for SimpleLang: a code box + a run button + output.

Usage:
    python web_ui.py [port]

Then open http://localhost:<port> in a browser. No external dependencies
(stdlib only), matching the rest of the project.
"""

import io
import json
import sys
import webbrowser
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from lexer import Lexer, LexError
from parser import Parser, ParseError
from interpreter import Interpreter, RuntimeErrorSL

DEFAULT_CODE = """let n = 10;
let result = 1;
let i = 1;

while (i <= n) {
    result = result * i;
    i = i + 1;
}

print("Factorial of", n, "is", result);
"""

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
  .hint {
    color: var(--muted);
    font-size: 12px;
    margin-left: auto;
  }
</style>
</head>
<body>
<header>
  <h1>SimpleLang Playground</h1>
  <span class="sub">write .sl code, run it, see the output</span>
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
        body = PAGE.replace("${DEFAULT_CODE_JSON}", json.dumps(DEFAULT_CODE)).encode("utf-8")
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
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(f"SimpleLang Playground running at {url}  (Ctrl+C to stop)")
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
