import os
from flask import render_template, Flask
from flask.ext.sqlalchemy import SQLAlchemy
import pandas as pd
from app import app, db


@app.route('/')
def index():
    data = pd.read_sql_table('transaction', db.engine)
    del data['id']
    data = data.to_html(classes=['table table-hover table-bordered'], index=False)
    return render_template('index.html', data=data)
