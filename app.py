from flask import Flask
from flask_cors import CORS
from flask_sock import Sock

import views

print("Loading models")
# models = utils.load_models()

print("Starting Flask app")
app = Flask(__name__)
CORS(app)
app.config["SOCK_SERVER_OPTIONS"] = {"ping_interval": 25}
sock = Sock(app)

print("Pre-rendering index page")
index_html = views.render_index(app)


@app.route("/")
def main_page():
    return index_html


# import http_api
import websocket_api
