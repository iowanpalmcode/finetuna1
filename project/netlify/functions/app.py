"""
Netlify Function entrypoint that adapts an API-Gateway-style proxy event
into a WSGI call against the existing Flask app (ui_server.app), so the app
can be deployed as-is without a separate serverless framework.

Note: Netlify Functions are stateless/ephemeral - each invocation may run in
a fresh container, so the in-memory `agents` dict in ui_server.py is not
guaranteed to persist across requests here. For anything that depends on
agent state surviving between calls, deploy to Render instead (render.yaml).
"""

import base64
import sys
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode

# project root is two levels up from netlify/functions/app.py
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ui_server import app  # noqa: E402


def handler(event, context):
    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    headers = event.get("headers") or {}
    query = event.get("queryStringParameters") or {}
    raw_body = event.get("body") or ""

    if event.get("isBase64Encoded"):
        body_bytes = base64.b64decode(raw_body)
    else:
        body_bytes = raw_body.encode("utf-8")

    content_type = headers.get("content-type", headers.get("Content-Type", ""))

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": urlencode(query),
        "CONTENT_LENGTH": str(len(body_bytes)),
        "CONTENT_TYPE": content_type,
        "SERVER_NAME": "netlify",
        "SERVER_PORT": "443",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "https",
        "wsgi.input": BytesIO(body_bytes),
        "wsgi.errors": sys.stderr,
        "wsgi.multithread": False,
        "wsgi.multiprocess": True,
        "wsgi.run_once": False,
    }

    for key, value in headers.items():
        header_key = "HTTP_" + key.upper().replace("-", "_")
        environ.setdefault(header_key, value)

    response_state = {}

    def start_response(status, response_headers, exc_info=None):
        response_state["status"] = int(status.split(" ", 1)[0])
        response_state["headers"] = dict(response_headers)

    body_chunks = app(environ, start_response)
    response_body = b"".join(body_chunks)

    return {
        "statusCode": response_state.get("status", 200),
        "headers": response_state.get("headers", {}),
        "body": response_body.decode("utf-8", errors="replace"),
    }
