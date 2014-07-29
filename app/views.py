import os
from flask import render_template, Flask
from flask.ext.sqlalchemy import SQLAlchemy
import pandas as pd
import forms
from app import app, db


@app.route('/')
def index():
    data = pd.read_sql_table('transaction', db.engine)
    del data['id'], data['note']

    data = data.sort(['date'])
    data['balance'] = data['amount'].cumsum()

    data = data.to_html(classes=['table table-hover table-bordered'], index=False, escape=False)
    return render_template('index.html', data=data)


@app.route('/add_transaction')
def add_transaction():
    form = forms.AddTransactionForm()
    return render_template('add_transaction.html', form=form)

