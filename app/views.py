import os
from flask import render_template, Flask, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import pandas as pd
import forms
from app import app, db, models


@app.route('/')
def index():
    data = pd.read_sql_table('transaction', db.engine)

    pd.set_option('display.max_colwidth', 1000)

    data[' '] = ('<div class="btn-group btn-group-xs">'
                      '<a href="#" class="btn btn-default" role="button"><i class="fa fa-edit"></i></a>'
                      '<a href="/info_transaction/' + data['id'].astype(str) + 
                            '"class="btn btn-default transactioninfo" role="button"><i class="fa fa-info"></i></a>'
                      '<a href="/delete_transaction/' + data['id'].astype(str) + 
                            '" class="btn btn-danger confirmdelete" role="button"><i class="fa fa-trash-o"></i></a>'
                      '</div>')

    # sorting based on descending date
    data = data.sort(['date'], ascending=False)
    # adding the total amount
    data['balance'] = data['amount'][::-1].cumsum()[::-1]

    # replacing amount by in and out for easier reading
    data['in'] = data[data['amount'] >= 0]['amount']
    data['out'] = data[data['amount'] < 0]['amount']

    # displaying the pandas data as an html table
    data = data[[' ', 'date', 'description', 'category', 'in', 'out', 'balance']]

    data = data.to_html(classes=['table table-hover table-bordered'], 
                        index=False, escape=False, na_rep='')
    return render_template('index.html', data=data)


@app.route('/info_transaction/<int:transaction_id>')
def info_transaction(transaction_id):
    data = pd.read_sql_table('transaction', db.engine)
    note=data[data['id'] == transaction_id]['note']
    if len(note):
        return render_template('info_transaction.html', 
                           note=data[data['id'] == transaction_id]['note'])
    else:
        return render_template('info_transaction.html', 
                           note='No note')


@app.route('/delete_transaction/<int:transaction_id>')
def delete_transaction(transaction_id):
    transaction = models.Transaction.query.get(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect('/')


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

