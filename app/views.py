import os, datetime
from flask import render_template, Flask, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import pandas as pd
import forms
from app import app, db, models


dict_key2expense = {'child': 'Childcare', 
                    'transport': 'Transport', 
                    'leisure': 'Culture & Leisure', 
                    'beauty': 'Beauty & Clothing', 
                    'bills': 'Bills', 
                    'other': 'Other', 
                    'day2day': 'Day to day', 
                    'healthcare': 'Healthcare'}
dict_key2income = {'salary': 'Salary', 
                   'other': 'Other income',
                   'repayment': 'Misc. repayment'}


def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text


@app.route('/')
def index():
    data = pd.read_sql_table('transaction', db.engine)

    pd.set_option('display.max_colwidth', 1000)

    data[' '] = ('<div class="btn-group btn-group-xs">'
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

    data['category'] = data['category'].map(lambda x: replace_all(x, dict_key2expense))
    data['category'] = data['category'].map(lambda x: replace_all(x, dict_key2income))

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
        form.category.choices = dict_key2expense.items()
    elif operationtype == 'credit':
        form.category.choices = dict_key2income.items()
    if form.validate_on_submit():
        if operationtype == 'debit':
            amount = -abs(float(form.amount.data))
        elif operationtype == 'credit':
            amount = abs(float(form.amount.data))
    	u = models.Transaction(date=form.date.data,
                               reconciled=False,
    		                   amount=amount,
    		                   description=form.description.data,
    		                   category=form.category.data,
    		                   note=form.note.data)
    	db.session.add(u)
    	db.session.commit()
    	return redirect('/')
    return render_template('add_transaction.html', 
                           form=form, operationtype=operationtype)


@app.route('/add_transaction')
def add_transaction_choice():
    return render_template('add_transaction_choice.html')


@app.route('/graphs', methods=['GET', 'POST'])
def display_graphs():
    data = pd.read_sql_table('transaction', db.engine)

    month = data['date'].map(lambda x: x.month)
    data = data[month == datetime.datetime.now().month]
    data['category'] = data['category'].map(lambda x: replace_all(x, dict_key2expense))
    data['category'] = data['category'].map(lambda x: replace_all(x, dict_key2income))

    debit = data[data['amount'] < 0][['category', 'amount']]
    debit = debit.groupby('category').sum().abs()
    debit = debit.sort('amount', ascending=False)
    donutexpenses = ''
    for cat in debit.index:
        donutexpenses += '{label: "%s", value: %d},' % (cat, debit.ix[cat])
    donutexpensessum = debit.sum()['amount']
    donutexpenses = donutexpenses[:-1]
    
    credit = data[data['amount'] >= 0][['category', 'amount']]
    credit = credit.groupby('category').sum().abs()
    credit = credit.sort('amount', ascending=False)
    donutincomes = ''
    for cat in credit.index:
        donutincomes += '{label: "%s", value: %d},' % (cat, credit.ix[cat])
    donutincomessum = credit.sum()['amount']
    donutincomes = donutincomes[:-1]

    form = forms.SelectDateRangeForm()
    if form.validate_on_submit():
        redirect('/')

    return render_template('graphs.html',
                           donutexpenses=donutexpenses,
                           donutexpensessum=donutexpensessum,
                           donutincomes=donutincomes,
                           donutincomessum=donutincomessum,
                           form=form)


