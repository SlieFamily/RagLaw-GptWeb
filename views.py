import dataclasses
import json

from flask import Flask, render_template


def render_index(app: Flask) -> str:
    default_family = "default_family"
    default_model = "gpt-3.5"

    with app.app_context():
        return render_template("index.html")
