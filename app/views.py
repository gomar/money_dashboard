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
    data['balance  (<i class="fa fa-gbp"></i>)'] = data['amount'][::-1].cumsum()[::-1]

    # replacing amount by in and out for easier reading
    data['in (<i class="fa fa-gbp"></i>)'] = data[data['amount'] >= 0]['amount']
    data['out (<i class="fa fa-gbp"></i>)'] = data[data['amount'] < 0]['amount']

    # displaying the pandas data as an html table
    data = data[[' ', 'date', 'description', 'category', 
                 'in (<i class="fa fa-gbp"></i>)', 
                 'out (<i class="fa fa-gbp"></i>)', 
                 'balance  (<i class="fa fa-gbp"></i>)']]

    data = data.to_html(classes=['table table-hover table-bordered'], 
                        index=False, escape=False, na_rep='')
    return render_template('index.html', data=data)


@app.route('/info_transaction/<int:transaction_id>')
def info_transaction(transaction_id):
    data = pd.read_sql_table('transaction', db.engine)
    note = data[data['id'] == transaction_id]['note']
    if len(note) != 0:
        if note.iloc[0] == '':
            note = 'No note'
        else:
            note = note.iloc[0]
        return render_template('info_transaction.html', 
                               note=note)
    else:
        return render_template('info_transaction.html', 
                               note='No note')


@app.route('/delete_transaction/<int:transaction_id>')
def delete_transaction(transaction_id):
    transaction = models.Transaction.query.get(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect('/')


@app.route('/add_transaction/<operationtype>', methods=['GET', 'POST'])
def add_expense(operationtype):
    form = forms.AddTransactionForm()
    if operationtype == 'debit':
        form.category.choices = [('child', 'Childcare'), 
                                 ('transport', 'Transport'), 
                                 ('leisure', 'Entertainment & Leisure'), 
                                 ('beauty', 'Beauty & Clothing'), 
                                 ('bills', 'Bills'), 
                                 ('other', 'Other'), 
                                 ('day2day', 'Day to day expenses'), 
                                 ('healthcare', 'Healthcare')]
    elif operationtype == 'credit':
        form.category.choices = [('salary', 'Salary'), 
                                 ('other', 'Other income'),
                                 ('repayment', 'Miscellaneous repayment')]
    if form.validate_on_submit():
    	u = models.Transaction(date=form.date.data,
    		                   amount=form.amount.data,
    		                   description=form.description.data,
    		                   category=form.category.data,
    		                   note=form.note.data)
    	db.session.add(u)
    	db.session.commit()
    	return redirect('/')
    return render_template('add_transaction.html', 
                           form=form, operationtype=operationtype)


@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction_choice():
    return render_template('add_transaction_choice.html')

