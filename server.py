"""
Flask Frontend Server.
Serves the static frontend files and proxies API requests to FastAPI backend.
This allows both Flask and FastAPI to work together:
  - Flask (port 5000) → serves HTML/CSS/JS + proxies /api/* to FastAPI
  - FastAPI (port 8000) → handles all API logic
"""

import os
import sys
from pathlib import Path
from flask import Flask, send_from_directory, request, Response
from flask_cors import CORS

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests")
    import requests

# Configuration
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FRONTEND_DIR = Path(__file__).parent / "frontend"

# Create Flask app
app = Flask(__name__, static_folder=str(FRONTEND_DIR))
CORS(app)


# ─── Static File Serving ───

@app.route('/')
def serve_index():
    """Serve the main HTML page."""
    return send_from_directory(str(FRONTEND_DIR), 'index.html')


@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files."""
    return send_from_directory(str(FRONTEND_DIR / 'css'), filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files."""
    return send_from_directory(str(FRONTEND_DIR / 'js'), filename)


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve asset files."""
    assets_dir = FRONTEND_DIR / 'assets'
    if assets_dir.exists():
        return send_from_directory(str(assets_dir), filename)
    return "Not found", 404


# ─── API Proxy ───

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_api(path):
    """
    Proxy all /api/* requests to the FastAPI backend.
    This allows the frontend to make API calls to the same origin.
    """
    target_url = f"{FASTAPI_URL}/api/{path}"

    try:
        # Forward the request
        headers = {
            key: value for key, value in request.headers
            if key.lower() not in ('host', 'content-length', 'transfer-encoding')
        }

        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            timeout=120  # 2 min timeout for LLM calls
        )

        # Build response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = {
            key: value for key, value in resp.headers.items()
            if key.lower() not in excluded_headers
        }

        return Response(
            resp.content,
            status=resp.status_code,
            headers=response_headers
        )

    except requests.exceptions.ConnectionError:
        return {
            "detail": "Cannot connect to FastAPI backend. Make sure it's running on " + FASTAPI_URL
        }, 502
    except requests.exceptions.Timeout:
        return {"detail": "Request to backend timed out"}, 504
    except Exception as e:
        return {"detail": f"Proxy error: {str(e)}"}, 500


# ─── Health Check ───

@app.route('/health')
def health():
    """Health check for Flask server."""
    # Also check FastAPI backend
    try:
        resp = requests.get(f"{FASTAPI_URL}/health", timeout=5)
        backend_status = "connected" if resp.status_code == 200 else "error"
    except Exception:
        backend_status = "disconnected"

    return {
        "flask": "healthy",
        "fastapi_backend": backend_status,
        "fastapi_url": FASTAPI_URL
    }


# ─── Main ───

if __name__ == '__main__':
    print("=" * 55)
    print("  🚀 AI Sales Playbook Assistant — Frontend Server")
    print("=" * 55)
    print(f"  Frontend:  http://localhost:{FLASK_PORT}")
    print(f"  Backend:   {FASTAPI_URL}")
    print(f"  API Docs:  {FASTAPI_URL}/docs")
    print("=" * 55)
    print()
    print("  Make sure the FastAPI backend is running first:")
    print(f"    cd backend && python main.py")
    print()

    app.run(
        host='0.0.0.0',
        port=FLASK_PORT,
        debug=True
    )
