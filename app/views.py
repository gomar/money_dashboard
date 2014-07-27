import os
from flask import render_template, Flask
from flask.ext.sqlalchemy import SQLAlchemy
import pandas as pd
from app import app, db


@app.route('/')
def index():
    data = pd.read_sql_table('transaction', db.engine)
    del data['id'], data['note']
    data['reconciled'] = data['reconciled'].astype(str)
    reconciled = data.reconciled
    reconciled[reconciled == 'True'] = '<i class="fa fa-check-square-o"></i>'
    reconciled[reconciled == 'False'] = '<i class="fa fa-square-o"></i>'
    data['reconciled'] = reconciled

    data = data.sort(['date'])
    data['balance'] = data['amount'].cumsum()
    
    data = data.to_html(classes=['table table-hover table-bordered'], index=False, escape=False)
    return render_template('index.html', data=data)
