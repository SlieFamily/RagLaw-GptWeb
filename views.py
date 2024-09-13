from flask import Flask, render_template


def render_index(app: Flask) -> str:

    with app.app_context():
        return render_template("index.html")
