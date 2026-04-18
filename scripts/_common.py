from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


def print_json(data: Dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False))


def build_parser(description: str) -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=description)


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _extract_last_json_payload(stdout: str):
    """Extract the last valid JSON object from stdout.

    Tries multiple strategies:
    1. Parse lines in reverse order
    2. Find JSON objects starting with '{'
    3. Parse entire text as JSON
    """
    text = (stdout or "").strip()
    if not text:
        return None

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in reversed(lines):
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _end = decoder.raw_decode(text[i:])
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    return None


import shlex


def add_shell_vars(vars_dict: Dict[str, Any]) -> Dict[str, str]:
    """Add shell-quoted versions of variables with _sh suffix.

    Args:
        vars_dict: Dictionary of variables to quote

    Returns:
        Dictionary with original vars plus _sh quoted versions
    """
    import sys

    out = dict(vars_dict)
    for k, v in vars_dict.items():
        value = str(v)
        # On Windows, use simpler quoting to avoid over-escaping
        if sys.platform == "win32":
            # Only quote if the value contains spaces or special characters
            if " " in value or any(c in value for c in "&|<>^"):
                out[f"{k}_sh"] = f'"{value}"'
            else:
                out[f"{k}_sh"] = value
        else:
            out[f"{k}_sh"] = shlex.quote(value)
    return out


def rpc_call(
    rpc_url: str, method: str, params: Optional[list] = None, timeout: int = 60
) -> Any:
    """Make a JSON-RPC call with requests fallback to curl.

    Args:
        rpc_url: RPC endpoint URL
        method: JSON-RPC method name
        params: Optional list of parameters
        timeout: Request timeout in seconds

    Returns:
        RPC result data

    Raises:
        RuntimeError: If RPC call fails
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": [] if params is None else params,
        "id": 1,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "curl/8.5.0",
    }

    try:
        response = requests.post(
            rpc_url.rstrip("/"),
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        if "error" in data and data["error"]:
            raise RuntimeError(f"RPC error for {method}: {data['error']}")
        return data.get("result", data)
    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        if status != 403:
            raise

    cmd = [
        "curl",
        "-sS",
        "-X",
        "POST",
        rpc_url.rstrip("/"),
        "-H",
        "Content-Type: application/json",
        "-d",
        json.dumps(payload, separators=(",", ":")),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(
            f"curl fallback failed ({proc.returncode}): {proc.stderr.strip()}"
        )

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from RPC: {proc.stdout}") from e

    if "error" in data and data["error"]:
        raise RuntimeError(f"RPC error for {method}: {data['error']}")

    return data.get("result", data)


def best_effort_decode_hex(value: str | None) -> Dict[str, Any]:
    if not value:
        return {"hex": value or "", "utf8": None}
    if not isinstance(value, str) or not value.startswith("0x"):
        return {"hex": value, "utf8": None}
    try:
        raw = bytes.fromhex(value[2:])
    except ValueError:
        return {"hex": value, "utf8": None}
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = None
    return {"hex": value, "utf8": text}


def _resolve_backend_template_symbol(template: str):
    """Resolve symbolic backend template placeholders.

    If template is an environment variable name (e.g., GLH_SUBMIT_DEPLOY_BACKEND_CMD),
    resolve it from environment or caller's scope.
    """
    s = (template or "").strip()
    if not s:
        return template

    # already looks like a real shell command/template
    if any(ch in s for ch in " \t\r\n/.'\"$`|&;<>"):
        return template

    # resolve symbolic placeholders like GLH_SUBMIT_DEPLOY_BACKEND_CMD
    if re.fullmatch(r"[A-Z][A-Z0-9_]*", s):
        env_val = os.environ.get(s)
        if isinstance(env_val, str) and env_val.strip():
            return env_val

        frame = inspect.currentframe()
        if frame is None:
            return template
        try:
            f = frame.f_back
            while f:
                for scope in (f.f_locals, f.f_globals):
                    val = scope.get(s)
                    if isinstance(val, str) and val.strip():
                        return val
                f = f.f_back
        finally:
            del frame

    return template


def run_backend_template(
    backend: Any,
    fmt_vars: Optional[Dict[str, Any]] = None,
    *,
    allow_nonzero_with_tx_hash: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Run a backend command template with variable substitution.

    Args:
        backend: Backend config dict or template string
        fmt_vars: Variables for template formatting
        allow_nonzero_with_tx_hash: Allow non-zero exit if tx_hash present
        **kwargs: Additional variables for template

    Returns:
        Dictionary containing backend response

    Raises:
        RuntimeError: If backend command fails
        TypeError: If backend type is invalid
    """
    backend_name = None
    template = None
    merged_vars = {}

    if isinstance(fmt_vars, dict):
        merged_vars.update(fmt_vars)
    merged_vars.update(kwargs)

    if isinstance(backend, dict):
        backend_name = (
            backend.get("name")
            or backend.get("backend")
            or backend.get("id")
            or backend.get("label")
        )
        template = (
            backend.get("template") or backend.get("command") or backend.get("cmd")
        )
        if template is None:
            raise RuntimeError(
                f"Backend config dict has no template/command/cmd key: {backend!r}"
            )
    elif isinstance(backend, str):
        template = backend
    else:
        raise TypeError(
            "run_backend_template backend must be dict or str, "
            f"got: {type(backend).__name__}"
        )

    if not isinstance(template, str):
        raise TypeError(
            "run_backend_template resolved template must be str, "
            f"got: {type(template).__name__}"
        )

    template = _resolve_backend_template_symbol(template)

    try:
        merged_vars = add_shell_vars(merged_vars)
        cmd = template.format(**merged_vars)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to format backend template. template={template!r}, vars={merged_vars!r}"
        ) from exc

    # On Windows, cmd.exe doesn't handle single quotes like bash does
    # Replace single quotes around paths with double quotes for Windows compatibility
    import re
    import sys

    if sys.platform == "win32":
        # Pattern to match single-quoted paths (not containing spaces or special chars inside)
        # This matches 'C:\path\to\file.py' but not '[true]'
        cmd = re.sub(r"'([A-Za-z]:[/\\][^']*?\.(?:py|mjs|js|exe))'", r'"\1"', cmd)

    proc = subprocess.run(
        cmd,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
    )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    payload = _extract_last_json_payload(stdout)

    salvaged_nonzero = (
        proc.returncode != 0
        and allow_nonzero_with_tx_hash
        and isinstance(payload, dict)
        and bool(payload.get("tx_hash"))
    )

    if proc.returncode != 0 and not salvaged_nonzero:
        prefix = f"[{backend_name}] " if backend_name else ""
        raise RuntimeError(
            f"{prefix}Backend command failed ({proc.returncode}): {cmd}\n"
            f"STDERR: {stderr.strip()}\n"
            f"STDOUT: {stdout.strip()}"
        )

    if not isinstance(payload, dict):
        prefix = f"[{backend_name}] " if backend_name else ""
        raise RuntimeError(
            f"{prefix}Backend command returned no JSON payload: {cmd}\n"
            f"STDERR: {stderr.strip()}\n"
            f"STDOUT: {stdout.strip()}"
        )

    if not payload.get("_stderr"):
        payload["_stderr"] = stderr.strip()
    if not payload.get("_command"):
        payload["_command"] = cmd
    if backend_name and not payload.get("_backend_name"):
        payload["_backend_name"] = backend_name

    payload["_backend_returncode"] = proc.returncode
    payload["_backend_nonzero_salvaged"] = salvaged_nonzero

    return payload
