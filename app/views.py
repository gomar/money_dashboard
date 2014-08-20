import os, datetime, calendar, time, dateutil
from flask import render_template, Flask, redirect
from flask.ext.sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
import forms
from app import app, db, models, utils


list_category = ['Vehicle', 
                 'Household Bills & Utilities', 
                 'Home & Garden',
                 'Day to Day',
                 'Leisure & Holidays',
                 'Clothing & Grooming', 
                 'Healthcare',
                 'Childcare & Education',
                 'Salary',
                 'Tax']

list_currency = [('euro', u'Euro'), ('gbp', u'British pound'), ('usd', u'US dollar')]


def update_waiting_scheduled_transactions():
    if os.path.exists(app.config['DB_FNAME']):
        return models.ScheduledTransaction.query\
                    .filter(models.ScheduledTransaction.next_occurence
                            <= datetime.datetime.now()).count()
    else:
        return 0

def in_account(path):
    path = path.split('/')
    path.remove('')
    return (path[0] == 'account') and (len(path) > 1)

app.jinja_env.filters['in_account'] = in_account


global context
context = {'now': datetime.datetime.now(),
           'waiting_scheduled_transactions': update_waiting_scheduled_transactions()}

@app.route('/')
def intro():
    return render_template('intro.html')


@app.route('/accounts')
def home():
    accounts = pd.read_sql_table('account', db.engine)
    return render_template('accounts.html', 
                           accounts=accounts.T.to_dict(),
                           **context)


@app.route('/add_account', methods=['GET', 'POST'])
def add_account():
    form = forms.AddAccount()
    form.currency.choices = list_currency

    if form.validate_on_submit():
        # creating database entry
        u = models.Account(name=form.name.data,
                           currency=form.currency.data)
        # adding to database
        db.session.add(u)
        db.session.commit()
        return redirect('/accounts')

    return render_template('add_account.html',
                           form=form,
                           **context)


@app.route('/delete_account/<int:account_id>')
def delete_account(account_id):
    account = models.Account.query.get(account_id)
    db.session.delete(account)
    db.session.commit()
    return redirect('/accounts')


@app.route('/account/<int:account_id>/transactions')
def transactions(account_id):
    account = models.Account.query.get(account_id)
    data = pd.read_sql_table('transaction', db.engine)
    data = data[data['account'] == account.name]

    pd.set_option('display.max_colwidth', 1000)

    data[' '] = '<div class="btn-toolbar pull-right" role="toolbar">'
    data[' '] += np.where(data['note'] != '', 
                          ('<div class="btn-group btn-group-xs">'
                           '<a href="/info_transaction/' + data['id'].astype(str) + 
                           '"class="btn btn-info transactioninfo" role="button"><i class="fa fa-info"></i></a>'
                           '</div>'),
                          '')
    data[' '] += '<div class="btn-group btn-group-xs">'
    data[' '] += ('<a href="/edit_transaction/' + data['id'].astype(str) + 
                  '" class="btn btn-default" role="button"><i class="fa fa-edit"></i></a>')
    data[' '] += ('<a href="/delete_transaction/' + data['id'].astype(str) + 
                  '" class="btn btn-danger confirmdelete" role="button"><i class="fa fa-trash-o"></i></a>'
                  '</div>')
    data[' '] += '</div>'

    # sorting based on descending date
    data = data.sort(['date'], ascending=False)
    # adding the total amount
    currency = '(<i class="fa fa-%s"></i>)' % account.currency

    data['balance  %s' % currency] = data['amount'][::-1].cumsum()[::-1]

    # replacing amount by in and out for easier reading
    data['in %s' % currency] = data[data['amount'] >= 0]['amount']
    data['out %s' % currency] = data[data['amount'] < 0]['amount']

    # displaying the pandas data as an html table
    data = data[[' ', 'date', 'description', 'category', 
                 'in %s' % currency, 
                 'out %s' % currency, 
                 'balance  %s' % currency]]

    data = data.to_html(classes=['table table-hover table-bordered table-striped table-condensed'], 
                        index=False, escape=False, na_rep='')
    return render_template('transactions.html', data=data, **context)


@app.route('/info_transaction/<int:transaction_id>')
def info_transaction(transaction_id):
    data = pd.read_sql_table('transaction', db.engine)
    note = data[data['id'] == transaction_id]['note']
    return render_template('info_transaction.html', 
                           note=note.iloc[0],
                           **context)


@app.route('/delete_transaction/<int:transaction_id>')
def delete_transaction(transaction_id):
    transaction = models.Transaction.query.get(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    account_id = models.Account.query\
            .filter(models.Account.name == transaction.account).all()[0].id
    return redirect('/account/%d/transactions' % account_id)


@app.route('/account/<int:account_id>/add_transaction/<operationtype>', methods=['GET', 'POST'])
def add_transaction(account_id, operationtype):
    account = models.Account.query.get(account_id)
    form = forms.AddTransactionForm()

    # adding an extra category depending on type of operation
    if operationtype == 'debit':
        additional_category = 'Misc. Expense'
    elif operationtype == 'credit':
        additional_category = 'Misc. Income'
    categories = list_category + [additional_category]
    categories.sort()
    form.category.choices = zip(categories, categories)

    if form.validate_on_submit():
        if operationtype == 'debit':
            amount = -abs(float(form.amount.data))
        elif operationtype == 'credit':
            amount = abs(float(form.amount.data))
        # creating database entry
        u = models.Transaction(date=form.date.data,
                               account=account.name,
                               amount=amount,
                               description=form.description.data,
                               category=form.category.data,
                               note=form.note.data)
        # adding to database
        db.session.add(u)
        db.session.commit()
        return redirect('/account/%d/transactions' % account_id)
    return render_template('add_transaction.html', 
                           form=form, operationtype=operationtype,
                           currency=account.currency,
                           **context)


@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    form = forms.AddTransactionForm()
    categories = list_category + ['Misc. Expense', 'Misc. Income']
    categories.sort()
    form.category.choices = zip(categories, categories)
    # getting the transaction element
    transaction = models.Transaction.query.get(transaction_id)
    account = models.Account.query.filter(models.Account.name == transaction.account).all()[0]
    if form.validate_on_submit():
        # update the rssfeed column
        transaction.date = form.date.data
        transaction.amount = form.amount.data
        transaction.description = form.description.data
        transaction.category = form.category.data
        transaction.note = form.note.data
        db.session.commit()
        account_id = models.Account.query\
            .filter(models.Account.name == transaction.account).all()[0].id
        return redirect('/account/%d/transactions' % account_id)
    else:
        form.date.data = transaction.date
        form.amount.data = '%.2f' % transaction.amount
        form.description.data = transaction.description
        form.category.data = transaction.category
        form.note.data = transaction.note
    return render_template('edit_transaction.html', 
                           operationtype='transaction',
                           form=form, currency=account.currency,
                           **context)


@app.route('/graphs', methods=['GET', 'POST'])
def display_graphs():
    data = pd.read_sql_table('transaction', db.engine)

    def compute(data, start_day, end_day):
        data = data[(data['date'] >= start_day) & (data['date'] <= end_day)]

        def _donut_data(data):
            data = data.groupby('category').sum().abs()
            data = data.sort('amount', ascending=False)
            donut_data = ''
            for cat in data.index:
                donut_data += '{label: "%s", value: %f},' % (cat, data.ix[cat])
            donut_sum = data.sum()['amount']
            donut_data = donut_data[:-1]
            return donut_data, donut_sum

        donutexpenses, donutexpensessum = _donut_data(data=data[data['amount'] < 0][['category', 'amount']])
        donutincomes, donutincomessum = _donut_data(data=data[data['amount'] >= 0][['category', 'amount']])
        return donutexpenses, donutexpensessum, donutincomes, donutincomessum

    form = forms.SelectDateRangeForm()

    if form.validate_on_submit():
        start_day = datetime.datetime.strptime(form.start.data, '%d/%m/%Y')
        end_day = datetime.datetime.strptime(form.end.data, '%d/%m/%Y')
    else:
        now = datetime.datetime.now()
        start_day, end_day = calendar.monthrange(year=now.year, month=now.month)
        start_day = datetime.date(now.year, now.month, 1)
        end_day = datetime.date(now.year, now.month, end_day)
        form.start.data = start_day.strftime('%d/%m/%Y')
        form.end.data = end_day.strftime('%d/%m/%Y')
        
    donutexpenses, donutexpensessum, donutincomes, donutincomessum = compute(data=data, start_day=start_day, end_day=end_day)
    return render_template('graphs.html',
                           donutexpenses=donutexpenses,
                           donutexpensessum=donutexpensessum,
                           donutincomes=donutincomes,
                           donutincomessum=donutincomessum,
                           form=form,
                           **context)



@app.route('/account/<int:account_id>/scheduled_transactions')
def scheduled_transactions(account_id):
    account = models.Account.query.get(account_id)
    df = pd.read_sql_table('scheduled_transaction', db.engine)
    df = df[df['account'] == account.name]
    pd.to_datetime(df['next_occurence'])
    df = df.sort('next_occurence')
    df = pd.DataFrame(df.values, columns=df.columns)
    df_dict = df.T.to_dict()
    scheduled_transactions = [df_dict[i] for i in range(len(df_dict))]
    return render_template('/account/%d/scheduled_transactions' % account_id, 
                           scheduled_transactions=scheduled_transactions,
                           currency=account.currency,
                           **context)


@app.route('/delete_scheduled_transaction/<int:transaction_id>')
def delete_scheduled_transaction(transaction_id):
    transaction = models.ScheduledTransaction.query.get(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()
    return redirect('/scheduled_transactions')


@app.route('/account/<int:account_id>/add_scheduled_transaction/<operationtype>', methods=['GET', 'POST'])
def add_scheduled_transaction(account_id, operationtype):
    account = models.Account.query.get(account_id)
    form = forms.AddTransactionForm()
    form.date.label = 'next occurence'

    # adding an extra category depending on type of operation
    if operationtype == 'debit':
        additional_category = 'Misc. Expense'
    elif operationtype == 'credit':
        additional_category = 'Misc. Income'
    categories = list_category + [additional_category]
    categories.sort()
    form.category.choices = zip(categories, categories)

    if form.validate_on_submit():
        if operationtype == 'debit':
            amount = -abs(float(form.amount.data))
        elif operationtype == 'credit':
            amount = abs(float(form.amount.data))
        # creating database entry
        u = models.ScheduledTransaction(next_occurence=form.date.data,
                                        amount=amount,
                                        account=account.name,
                                        description=form.description.data,
                                        category=form.category.data,
                                        note=form.note.data)
        # adding to database
        db.session.add(u)
        db.session.commit()
        context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()

        return redirect('/scheduled_transactions')
    return render_template('add_transaction.html', 
                           form=form, 
                           operationtype='scheduled ' + operationtype,
                           **context)


@app.route('/create_scheduled_transaction/<int:transaction_id>')
def create_scheduled_transaction(transaction_id):
    s_transaction = models.ScheduledTransaction.query.get(transaction_id)
    u = models.Transaction(date=s_transaction.next_occurence,
                           amount=s_transaction.amount,
                           description=s_transaction.description,
                           category=s_transaction.category,
                           note=s_transaction.note)
    # adding new transaction to database
    db.session.add(u)
    s_transaction.next_occurence = s_transaction.next_occurence + dateutil.relativedelta.relativedelta(months=1)
    db.session.commit()
    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()
    return redirect('/scheduled_transactions')


@app.route('/skip_scheduled_transaction/<int:transaction_id>')
def skip_scheduled_transaction(transaction_id):
    s_transaction = models.ScheduledTransaction.query.get(transaction_id)
    s_transaction.next_occurence = s_transaction.next_occurence + dateutil.relativedelta.relativedelta(months=1)
    db.session.commit()
    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()
    return redirect('/scheduled_transactions')


@app.route('/info_scheduled_transaction/<int:transaction_id>')
def info_scheduled_transaction(transaction_id):
    data = pd.read_sql_table('scheduled_transaction', db.engine)
    note = data[data['id'] == transaction_id]['note']
    return render_template('info_transaction.html', 
                           note=note.iloc[0],
                           **context)


@app.route('/edit_scheduled_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_scheduled_transaction(transaction_id):
    form = forms.AddTransactionForm()
    form.date.label = 'next occurence'
    categories = list_category + ['Misc. Expense', 'Misc. Income']
    categories.sort()
    form.category.choices = zip(categories, categories)
    # getting the transaction element
    transaction = models.ScheduledTransaction.query.get(transaction_id)
    if form.validate_on_submit():
        # update the rssfeed column
        transaction.next_occurence = form.date.data
        transaction.amount = form.amount.data
        transaction.description = form.description.data
        transaction.category = form.category.data
        transaction.note = form.note.data
        db.session.commit()
        context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()
        return redirect('/scheduled_transactions')
    else:
        form.date.data = transaction.next_occurence
        form.amount.data = '%.2f' % transaction.amount
        form.description.data = transaction.description
        form.category.data = transaction.category
        form.note.data = transaction.note
    return render_template('edit_transaction.html',
                           operationtype='scheduled transaction',
                           form=form,
                           **context)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', **context), 404
