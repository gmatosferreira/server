#!/usr/bin/env python3
"""
Lightweight OliveTin-compatible Web Server
Loads actions from config.yaml and serves an interactive web UI.
"""

import os
import sys
import json
import time
import re
import subprocess
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"
INDEX_PATH = BASE_DIR / "index.html"

def preprocess_yaml(content: str) -> str:
    """Ensure unquoted hex colors like #ff0000 aren't discarded as comments."""
    lines = []
    for line in content.splitlines():
        m = re.match(r'^(\s*[\w\-]+:\s*)(#[0-9a-fA-F]{3,8}\b)(.*)$', line)
        if m:
            line = f'{m.group(1)}"{m.group(2)}"{m.group(3)}'
        lines.append(line)
    return '\n'.join(lines)

# Try importing pyyaml, fallback to minimal built-in parser if not installed
try:
    import yaml

    def load_yaml(content: str):
        return yaml.safe_load(preprocess_yaml(content))
except ImportError:
    def load_yaml(content: str):
        """Minimal fallback YAML parser for actions config."""
        content = preprocess_yaml(content)
        data = {"actions": []}
        current_action = None
        multiline_key = None
        multiline_lines = []

        def flush_multiline():
            nonlocal multiline_key, multiline_lines
            if current_action is not None and multiline_key and multiline_lines:
                current_action[multiline_key] = " && ".join(multiline_lines)
            multiline_key = None
            multiline_lines = []

        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("actions:"):
                continue

            # Detect if a known action key starts here
            known_key = False
            if ":" in line and not line.startswith("- "):
                candidate_key = line.split(":", 1)[0].strip()
                if candidate_key in ("title", "shell", "icon", "onclick", "description", "danger", "color", "group", "url", "link"):
                    known_key = True

            # Detect indented continuation of multiline block scalar (| or >)
            if multiline_key and not known_key and not line.startswith("- "):
                clean_chunk = line.rstrip("\\").rstrip("&").strip()
                if clean_chunk:
                    multiline_lines.append(clean_chunk)
                continue
            else:
                flush_multiline()

            if line.startswith("- "):
                if current_action:
                    data["actions"].append(current_action)
                current_action = {}
                line = line[2:].strip()

            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if val in ("|", ">", "|-", ">-"):
                    multiline_key = key
                    multiline_lines = []
                    continue
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                if current_action is not None and key in ("title", "shell", "icon", "onclick", "description", "danger", "color", "group", "url", "link"):
                    if key == "danger":
                        current_action[key] = val.lower() in ("true", "yes", "1")
                    else:
                        current_action[key] = val
                elif current_action is None:
                    if val.isdigit():
                        val = int(val)
                    data[key] = val

        flush_multiline()
        if current_action:
            data["actions"].append(current_action)
        return data


class ConfigManager:
    def __init__(self, path: Path):
        self.path = path
        self._cache = None
        self._last_mtime = 0

    def get_config(self):
        try:
            mtime = self.path.stat().st_mtime
            if self._cache is None or mtime != self._last_mtime:
                with open(self.path, "r", encoding="utf-8") as f:
                    config = load_yaml(f.read()) or {}
                self._cache = config
                self._last_mtime = mtime
            return self._cache
        except Exception as e:
            print(f"[!] Error loading config from {self.path}: {e}", file=sys.stderr)
            return self._cache or {"title": "OliveTin Server", "actions": []}


FAVICON_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="5" y="4" width="22" height="24" rx="7" fill="#64748b"/><path d="M5 9h22M5 23h22" stroke="#94a3b8" stroke-width="1.5"/><ellipse cx="16" cy="16" rx="6" ry="7.5" fill="#84cc16"/><circle cx="16" cy="16" r="2.2" fill="#ef4444"/></svg>"""

config_mgr = ConfigManager(CONFIG_PATH)


class OliveTinHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging format
        sys.stdout.write(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.serve_index()
        elif parsed.path in ("/favicon.ico", "/favicon.svg"):
            self.serve_favicon()
        elif parsed.path == "/api/config":
            self.serve_config_api()
        else:
            # Fallback to standard static file serving if needed
            super().do_GET()

    def serve_favicon(self):
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Content-Length", str(len(FAVICON_SVG)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(FAVICON_SVG)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/execute":
            self.handle_execute()
        elif parsed.path == "/shutdown":
            # Legacy fallback
            self.execute_command("poweroff")
        else:
            self.send_error(404, "Endpoint not found")

    def serve_index(self):
        if not INDEX_PATH.exists():
            self.send_error(404, "index.html not found")
            return
        try:
            with open(INDEX_PATH, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading index.html: {e}")

    def serve_config_api(self):
        config = config_mgr.get_config()
        # Sanitize actions for client (include id, title, icon, onclick, description)
        actions = []
        for idx, act in enumerate(config.get("actions", [])):
            color = str(act.get("color") or "").strip()
            # If user provided hex without leading # (e.g. ff0000 or 10b981), prepend #
            if re.match(r'^[0-9a-fA-F]{3,8}$', color):
                color = f"#{color}"
            # Only keep valid hex colors
            if not re.match(r'^#[0-9a-fA-F]{3,8}$', color):
                color = ""

            actions.append({
                "id": idx,
                "title": act.get("title", f"Action {idx + 1}"),
                "icon": act.get("icon", "terminal"),
                "onclick": act.get("onclick", "execution-dialog"),
                "description": act.get("description", ""),
                "color": color,
                "group": str(act.get("group") or "").strip(),
                "url": str(act.get("url") or act.get("link") or "").strip()
            })

        payload = {
            "title": config.get("title", "Server Control"),
            "actions": actions
        }
        data = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_execute(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON payload")
            return

        action_id = req.get("id")
        config = config_mgr.get_config()
        actions = config.get("actions", [])

        if action_id is None or not isinstance(action_id, int) or action_id < 0 or action_id >= len(actions):
            self.send_error(400, "Invalid action id")
            return

        action = actions[action_id]
        cmd = action.get("shell")
        if not cmd:
            self.send_error(400, "No shell command configured for this action")
            return

        result = self.execute_command(cmd)
        resp_data = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(resp_data)))
        self.end_headers()
        self.wfile.write(resp_data)

    def execute_command(self, cmd: str) -> dict:
        start_time = time.time()
        print(f"[>] Executing shell command: {cmd}")
        env = os.environ.copy()
        env.setdefault("TERM", "xterm-256color")
        env["FORCE_COLOR"] = "1"
        env["CLICOLOR_FORCE"] = "1"
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
                env=env
            )
            duration = round(time.time() - start_time, 2)
            return {
                "success": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "duration": duration,
                "command": cmd
            }
        except subprocess.TimeoutExpired as e:
            duration = round(time.time() - start_time, 2)
            return {
                "success": False,
                "exit_code": -1,
                "stdout": e.stdout or "",
                "stderr": f"Command timed out after 120 seconds",
                "duration": duration,
                "command": cmd
            }
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": duration,
                "command": cmd
            }


def main():
    config = config_mgr.get_config()
    port = int(config.get("port", 8888))
    listen_addr = config.get("listenAddress", "0.0.0.0")

    server_address = (listen_addr, port)
    httpd = ThreadingHTTPServer(server_address, OliveTinHandler)
    print(f"==================================================")
    print(f" OliveTin-lite Server running at http://{listen_addr}:{port}/")
    print(f" Config: {CONFIG_PATH}")
    print(f" Press Ctrl+C to stop.")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server...")
        httpd.shutdown()


if __name__ == "__main__":
    main()
