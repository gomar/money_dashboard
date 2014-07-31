import os
from flask import render_template, Flask, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import pandas as pd
import forms
from app import app, db, models


@app.route('/')
def index():
    data = pd.read_sql_table('transaction', db.engine)
    del data['id'], data['note']

    data = data.sort(['date'], ascending=False)
    data['balance'] = data['amount'][::-1].cumsum()[::-1]

    data = data.to_html(classes=['table table-hover table-bordered'], index=False, escape=False)
    return render_template('index.html', data=data)


@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    form = forms.AddTransactionForm()
    if form.validate_on_submit():
    	u = models.Transaction(date=form.date.data,
    		                   amount=form.amount.data,
    		                   description=form.description.data,
    		                   category=form.category.data,
    		                   note=form.note.data)
    	db.session.add(u)
    	db.session.commit()
    	return redirect('/')
    return render_template('add_transaction.html', form=form)

