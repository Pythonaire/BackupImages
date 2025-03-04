#!/usr/bin/env python3
from flask import Flask

def init_app(basedir):
    app = Flask(__name__, instance_relative_config=False, root_path=basedir)
    with app.app_context():
        import application.routes  # Import routes
    return app