"""
the entry-point for flask, effectively 'main' for Hachit.

Loads all config, inputs, plugins

"""
import os

from flask import Flask, Blueprint

from api import bp
from config import Config

app = Flask('hachit')
Config.load(env=os.environ)     # load all the things
Config.set_flask(app)           # prep flask

app.register_blueprint(bp)      # setup our route

if __name__ == '__main__':
    Config.getLogger().info("Starting Hachit\n")
    app.run(debug=True)
