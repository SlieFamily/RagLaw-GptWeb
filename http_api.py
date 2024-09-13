from traceback import format_exc
from flask import jsonify, request

from app import app

@app.post("/api/v1/generate")
def http_api_generate():
    try:
        inputs = request.values.get("inputs")
        outputs = "当前用户未授权..."
        print(f"generate(), outputs={repr(outputs)}")

        return jsonify(ok=True, outputs=outputs)
    except Exception:
        return jsonify(ok=False, traceback=format_exc())
