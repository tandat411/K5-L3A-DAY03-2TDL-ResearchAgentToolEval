from __future__ import annotations

import argparse
import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
RUNS_DIR = ROOT / "runs"
TRANSCRIPTS_DIR = ROOT / "transcripts"
UI_FILE = ROOT / "ui" / "index.html"

load_lab_env(ROOT)

SESSIONS: dict[str, dict[str, Any]] = {}


def get_or_create_session(
    *,
    session_id: str | None,
    provider_name: str = "openrouter",
    model: str | None = None,
    version: str = "v0",
    history_window: int = 5,
    max_tool_rounds: int = 4,
) -> dict[str, Any]:
    if session_id and session_id in SESSIONS:
        session = SESSIONS[session_id]
        session["provider_name"] = provider_name
        session["model"] = model or session.get("model")
        session["version"] = version
        return session

    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    artifact_ver = build_artifact_version(version, system_prompt_path, tools_path)
    provider = make_provider(provider_name)
    selected_model = model or getattr(provider, "default_model", None)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), timestamp])
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_ver),
        "provider": provider_name,
        "model": selected_model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

    session = {
        "session_id": transcript_id,
        "provider_name": provider_name,
        "model": selected_model,
        "version": version,
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "history": [],
        "turn_index": 0,
        "transcript_path": transcript_path,
        "transcript": transcript,
    }
    SESSIONS[transcript_id] = session
    return session


def build_state_payload(version: str = "v0") -> dict[str, Any]:
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    system_prompt = system_prompt_path.read_text(encoding="utf-8") if system_prompt_path.exists() else ""
    declarations = load_tool_declarations(tools_path) if tools_path.exists() else []
    artifact_ver = build_artifact_version(version, system_prompt_path, tools_path)

    runs = []
    if RUNS_DIR.exists():
        for p in sorted(RUNS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                runs.append({
                    "file": p.name,
                    "run_id": data.get("run_id", p.stem),
                    "version": data.get("version", ""),
                    "suite": data.get("suite", ""),
                    "artifact_version": data.get("artifact_version", ""),
                    "provider": data.get("provider", ""),
                    "model": data.get("model", ""),
                    "summary": data.get("summary", {}),
                })
            except Exception:
                continue

    transcripts = []
    if TRANSCRIPTS_DIR.exists():
        for p in sorted(TRANSCRIPTS_DIR.glob("*.transcript.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                transcripts.append({
                    "file": p.name,
                    "transcript_id": data.get("transcript_id", p.stem),
                    "version": data.get("version", ""),
                    "provider": data.get("provider", ""),
                    "model": data.get("model", ""),
                    "turns_count": len(data.get("turns", [])),
                    "updated_at": data.get("updated_at", ""),
                })
            except Exception:
                continue

    return {
        **artifact_version_dict(artifact_ver),
        "system_prompt": system_prompt,
        "tools": declarations,
        "runs": runs,
        "transcripts": transcripts,
    }


class AgentUIHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_text: str) -> None:
        body = html_text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path in {"/", "/index.html"}:
            if not UI_FILE.exists():
                self._send_json({"error": "UI file missing"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_html(UI_FILE.read_text(encoding="utf-8"))
            return

        if parsed.path == "/api/state":
            version = (query.get("version") or ["v0"])[0]
            self._send_json(build_state_payload(version=version))
            return

        if parsed.path == "/api/run":
            fname = (query.get("file") or [""])[0]
            target = (RUNS_DIR / Path(fname).name).resolve()
            if not fname or not target.exists() or target.parent != RUNS_DIR.resolve():
                self._send_json({"error": "Run file not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json(json.loads(target.read_text(encoding="utf-8")))
            return

        if parsed.path == "/api/transcript":
            fname = (query.get("file") or [""])[0]
            target = (TRANSCRIPTS_DIR / Path(fname).name).resolve()
            if not fname or not target.exists() or target.parent != TRANSCRIPTS_DIR.resolve():
                self._send_json({"error": "Transcript not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json(json.loads(target.read_text(encoding="utf-8")))
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/session/new":
            session = get_or_create_session(
                session_id=None,
                provider_name=body.get("provider", "openrouter"),
                model=body.get("model") or None,
                version=body.get("version", "v0"),
            )
            self._send_json({
                "session_id": session["session_id"],
                "transcript_file": session["transcript_path"].name,
                "artifact_version": session["transcript"]["artifact_version"],
            })
            return

        if parsed.path == "/api/chat":
            user_text = str(body.get("message") or "").strip()
            if not user_text:
                self._send_json({"error": "Empty message"}, status=HTTPStatus.BAD_REQUEST)
                return

            provider_name = str(body.get("provider") or "openrouter")
            model_override = str(body.get("model") or "").strip() or None
            version = str(body.get("version") or "v0").strip() or "v0"
            session = get_or_create_session(
                session_id=body.get("session_id"),
                provider_name=provider_name,
                model=model_override,
                version=version,
            )

            system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
            tools_path = ARTIFACTS_DIR / "tools.yaml"
            system_prompt = system_prompt_path.read_text(encoding="utf-8")
            declarations = load_tool_declarations(tools_path)
            openai_tools = to_openai_tools(declarations)
            artifact_ver = build_artifact_version(version, system_prompt_path, tools_path)
            session["transcript"].update(artifact_version_dict(artifact_ver))

            session["turn_index"] += 1
            messages = [
                {"role": "system", "content": system_prompt},
                *trim_history(session["history"], session["history_window"]),
                {"role": "user", "content": user_text},
            ]

            turn_record: dict[str, Any] = {
                "turn_index": session["turn_index"],
                "started_at": now_iso(),
                "user": user_text,
                "status": "started",
                "assistant_text": None,
                "rounds": [],
                "tool_events": [],
            }

            try:
                provider = make_provider(provider_name)
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model_override,
                    max_tool_rounds=session["max_tool_rounds"],
                )
                turn_record.update(result)
                assistant_text = result["assistant_text"]
                session["history"].append({"role": "user", "content": user_text})
                session["history"].append({"role": "assistant", "content": assistant_text})
            except Exception as exc:
                turn_record.update({
                    "status": "provider_error",
                    "error": f"{type(exc).__name__}: {str(exc)}",
                    "assistant_text": f"Lỗi khi gọi provider: {type(exc).__name__}: {str(exc)}",
                })

            turn_record["ended_at"] = now_iso()
            session["transcript"]["turns"].append(turn_record)
            write_transcript(session["transcript_path"], session["transcript"])

            self._send_json({
                "session_id": session["session_id"],
                "transcript_file": session["transcript_path"].name,
                "artifact_version": session["transcript"]["artifact_version"],
                "turn": turn_record,
            })
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Agent Studio Web UI (starter_v0)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()

    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((args.host, args.port), AgentUIHandler)
    print(f"Research Agent UI running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()


if __name__ == "__main__":
    main()

