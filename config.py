import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "no"
    #MONGO_URI = "mongodb://localhost:27017/myDatabase
    MONGO_URI = os.environ.get("DATABASE_URL") or \
            "mongodb://localhost/app.db"
            #'mongodb://' + os.path.join(basedir, 'app.db')


    camera = 0
    record_path = '/u/home/hodgkinsona/Documents/gesture_recognition/record'
    if not os.path.exists(record_path):
        os.makedirs(record_path)