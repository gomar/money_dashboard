import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('app.config')
db = SQLAlchemy(app)

from app import views, models

if not os.path.isdir(app.config['DB_FOLDER']):
	os.makedirs(app.config['DB_FOLDER'])
db.create_all()
