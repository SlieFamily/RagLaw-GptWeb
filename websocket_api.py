import json
from traceback import format_exc

import flask_sock
from flask import request as http_request
from utils import search_similar_documents, qa_interface
from app import sock

@sock.route("/api/v2/generate")
def ws_api_generate(ws):
    try:
        request = json.loads(ws.receive(timeout=5 * 60))
        assert request["type"] == "open_inference_session"
        ws.send(json.dumps({"ok": True}))
        while True:
            request = json.loads(ws.receive(timeout=5 * 60))
            inputs = request.get("inputs")
            print(f"ws.generate.step(), inputs={repr(inputs)}")

            docs = search_similar_documents(inputs, top_k=3)
            outputs = qa_interface(inputs, docs)
            print(f"ws.generate.step(), outputs={repr(outputs)}")
            ws.send(json.dumps({"ok": True, "outputs": outputs, "stop": True}))

    except flask_sock.ConnectionClosed:
        pass
    except Exception:
        print("ws.generate failed.")
        ws.send(json.dumps({"ok": False, "traceback": format_exc()}))
    finally:
        print(f"ws.generate.close()")
