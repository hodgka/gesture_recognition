from flask import Flask
from config import Config
from flask_pymongo import PyMongo
import json 
import os
from bson.objectid import ObjectId
import shutil
from app.utils import AutoSwitch

class JSONEncoder(json.JSONEncoder):
    ''' extend json-encoder class'''

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


app = Flask(__name__)
app.config.from_object(Config)
mongo = PyMongo(app, app.config["MONGO_URI"])
app.json_encoder = JSONEncoder

switch = AutoSwitch(30)
disk_free_mb = int(shutil.disk_usage('.').free / 1024 / 1024)

from app import routes, models

