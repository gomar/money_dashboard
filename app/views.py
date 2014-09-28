import os, datetime, calendar, time, dateutil
from dateutil.relativedelta import relativedelta
from flask import render_template, Flask, redirect, flash, abort
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import pandas as pd
import numpy as np
import forms
from app import app, db, models, utils
from itertools import count
from sqlalchemy import desc


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

dict_category2icon = {'Vehicle': 'fa-car', 
'Household Bills & Utilities': 'fa-dollar', 
'Home & Garden': 'fa-home',
'Day to Day': 'fa-shopping-cart',
'Leisure & Holidays': 'fa-glass',
'Clothing & Grooming': 'fa-heart-o', 
'Healthcare': 'fa-medkit',
'Childcare & Education': 'fa-child',
'Salary': 'fa-plus',
'Tax': 'fa-gavel',
'Misc. Income': 'fa-question-circle',
'Misc. Expense': 'fa-question-circle', 
'Transfer': 'fa-exchange'}

list_currency = [('euro', u'Euro (<i class="fa fa-euro"></i>)'), 
                 ('gbp', u'British pound (<i class="fa fa-gbp"></i>)')]

list_operation_type = ['credit card', 'online payment', 'cheque', 'other']


def update_waiting_scheduled_transactions(account_name=None):
    if (os.path.exists(app.config['DB_FNAME'])) and (account_name is not None):
        return models.ScheduledTransaction.query\
                    .filter(models.ScheduledTransaction.account
                            == account_name)\
                    .filter(models.ScheduledTransaction.next_occurence
                            <= datetime.datetime.now())\
                    .filter(or_(models.ScheduledTransaction.ends
                            > datetime.datetime.now(),
                            models.ScheduledTransaction.ends == None)).count()
    else:
        return 0

def is_in(url, target):
    url = url.split('/')
    if '' in url:
        url.remove('')
    target = target.split('/')
    if '' in target:
        target.remove('')
    return len(set(target) & set(url)) == len(target)

def account_name(url):
    url = url.split('/')
    url.remove('')
    idx_account = url.index('account')
    account = models.Account.query.get(int(url[idx_account + 1]))
    return account.name

def get_balance():
    accounts = pd.read_sql_table('account', db.engine)
    transactions = pd.read_sql_table('transaction', db.engine, columns=['account', 'amount'])
    scheduled_transactions = pd.read_sql_table('scheduled_transaction', 
                                               db.engine) 

    transactions = transactions.rename(columns={'account': 'name'})
    transactions = transactions.groupby('name', as_index=False).sum()
    accounts['amount'] = accounts['reconciled_balance']
    for name in transactions.name:
        accounts.ix[accounts['name'] == name, 'amount'] += \
            transactions.ix[transactions.name == name, 'amount'].iloc[-1]
    # taking scheduled transactions into account
    accounts['end_of_month_amount'] = accounts['amount']
    for idx, operation in scheduled_transactions.iterrows():
        i = 0
        today = datetime.datetime.now()
        last_day_of_month = today + relativedelta(day=1, months=+1, days=-1)
        while operation.next_occurence \
            + relativedelta(**{operation.every_type: i * operation.every_nb}) \
            <= last_day_of_month:
            i += 1
        accounts.ix[accounts['name'] == operation.account, 'end_of_month_amount'] += \
            operation.amount * i
    return accounts

def category_id(category):
    categories = list_category + ['Misc. Expense', 'Misc. Income']
    return categories.index(category)

def category_name(category_id):
    categories = list_category + ['Misc. Expense', 'Misc. Income']
    return categories[category_id]

app.jinja_env.filters['is_in'] = is_in
app.jinja_env.filters['account_name'] = account_name

global context
context = {'now': datetime.datetime.now(),
           'waiting_scheduled_transactions': update_waiting_scheduled_transactions()}


@app.route('/')
def intro():
    for table in ['transaction', 'account', 'scheduled_transaction', 'transfer']:
        pd.read_sql_table(table, db.engine).to_excel(os.path.join(app.config['DB_FOLDER'], 
                                                                '%s.xls' % table))
    return render_template('intro.html')


@app.route('/accounts')
def home():
    data = get_balance()

    pd.set_option('display.max_colwidth', 2000)

    data['action'] = ('<div class="btn-group">'
                      '    <a class="btn btn-xs dropdown-toggle" data-toggle="dropdown" style="color: #2C3E50;" rel="tooltip" data-toggle="tooltip" data-placement="top" title="actions">'
                      '         <i class="fa fa-cog"></i>'
                      '    </a>'
                      '<ul class="dropdown-menu" role="menu">')
    data['action'] += ('<li>'
                       '<a href="/delete_account/' + data['id'].astype(str) + 
                       '" class="confirmdelete"><i class="fa fa-trash-o fa-fw"></i> Delete </a></li>')
    data['action'] += '</ul></div'

    # sorting based on currency and name
    data = data.sort(['currency', 'name'])

    # adding currency to amount
    data['amount'] = '<span class="pull-right">' + data['amount'].astype(str) + ' <i class="fa fa-' + data['currency'] + '"></i></span>' 

    # displaying the pandas data as an html table
    data = data[['id', 'action', 'name', 'amount']]

    data['name'] = ('<i class="fa fa-square" style="color: #E74C3C;"></i> &nbsp;&nbsp;' +
                    data['name'] + '&nbsp;&nbsp;<a href=/account/' + data['id'].astype(str) + '/transactions ' +
                    'class="btn btn-xs" style="color: #2C3E50;" rel="tooltip" data-toggle="tooltip" data-placement="top" title="select account">'
                    '    <i class="fa fa-chevron-right"></i>'
                    '</a></div>')

    del data['id']

    data = data.rename(columns={'amount': '<span class="pull-right">amount</span>'})

    data = data.to_html(classes=['table table-hover table-bordered table-striped'], 
                        index=False, escape=False, na_rep='')
    return render_template('accounts.html', 
                           data=data,
                           **context)


@app.route('/add_account', methods=['GET', 'POST'])
def add_account():
    form = forms.AddAccount()
    form.currency.choices = list_currency

    if form.validate_on_submit():
        # creating database entry
        u = models.Account(name=form.name.data,
                           currency=form.currency.data,
                           reconciled_balance=form.initial_balance.data)
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

    # deleting all transactions
    transactions = models.Transaction.query.filter(models.Transaction.account == account.name).all()
    for transaction in transactions:
        db.session.delete(transaction)

    # deleting all scheduled transactions
    scheduled_transactions = models.ScheduledTransaction.query.filter(models.ScheduledTransaction.account == account.name).all()
    for s_transaction in scheduled_transactions:
        db.session.delete(s_transaction)

    db.session.delete(account)
    db.session.commit()
    return redirect('/accounts')


@app.route('/account/<int:account_id>/transactions')
def transactions(account_id):
    account = models.Account.query.get(account_id)
    data = pd.read_sql_table('transaction', db.engine)
    data = data[data['account'] == account.name]

    pd.set_option('display.max_colwidth', 2000)

    data['category'] = data['category'].map(lambda x: '<i class="fa %s" rel="tooltip" data-toggle="tooltip" data-placement="top" title="%s"></i>' % (dict_category2icon[x], x))

    data['action'] = ('<div class="btn-group">'
                 '    <a class="btn btn-xs dropdown-toggle" data-toggle="dropdown" style="color: #2C3E50;" rel="tooltip" data-toggle="tooltip" data-placement="top" title="actions">'
                       '         <i class="fa fa-cog"></i>'
                       '    </a>'
                 '<ul class="dropdown-menu" role="menu">')
    data['action'] += np.where(data['note'] != '', 
                          ('<li>'
                           '<a href="/info_transaction/' + data['id'].astype(str) + 
                           '" class="transactioninfo"><i class="fa fa-info fa-fw"></i> Information</a>'
                           '</li>'),
                          '')
    data['action'] += ('<li>'
                  '<a href="/edit_transaction/account/%s/' % account_id + data['id'].astype(str) + 
                  '"><i class="fa fa-edit fa-fw"></i> Edit</a></li>')
    data['action'] += ('<li>'
                  '<a href="/delete_transaction/account/%s/' % account_id + data['id'].astype(str) + 
                  '" class="confirmdelete"><i class="fa fa-trash-o fa-fw"></i> Delete </a></li>')
    data['action'] += '</ul></div>'

    # sorting based on descending date
    data = data.sort(['date'], ascending=False)

    # adding the total amount
    currency = '(<i class="fa fa-%s"></i>)' % account.currency
    data['balance  %s' % currency] = data['amount'][::-1].cumsum()[::-1] + float(account.reconciled_balance)

    # replacing amount by in and out for easier reading
    data['amount %s' % currency] = np.nan
    data['amount %s' % currency].loc[data['amount'] >= 0] = "<p class='text-success'> <i class='fa fa-chevron-up'></i> " + data[data['amount'] >= 0]['amount'].astype(str) + "</p>" 
    data['amount %s' % currency].loc[data['amount'] < 0] = "<p class='text-danger'> <i class='fa fa-chevron-down'></i> " + data[data['amount'] < 0]['amount'].astype(str) + "</p>" 

    # displaying the pandas data as an html table
    data = data[['action', 'date', 'description', 'category', 
                 'amount %s' % currency, 
                 'balance  %s' % currency]]

    data = data.to_html(classes=['table table-hover table-bordered table-striped table-condensed'], 
                        index=False, escape=False, na_rep='')
    accounts = get_balance()
    cur_balance = accounts.ix[accounts.name == account.name, 'amount'].values[0]
    eom_balance = accounts.ix[accounts.name == account.name, 'end_of_month_amount'].values[0]

    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions(account_name=account.name)

    return render_template('transactions.html', data=data, 
                           several_accounts=(models.Account.query.count() > 1),
                           currency=account.currency,
                           cur_balance=cur_balance, eom_balance=eom_balance,
                           account_id=account_id, **context)


@app.route('/info_transaction/<int:transaction_id>')
def info_transaction(transaction_id):
    note = models.Transaction.query.get(transaction_id).note
    return render_template('info_transaction.html', 
                           note=note,
                           **context)


@app.route('/delete_transaction/account/<int:account_id>/<int:transaction_id>')
def delete_transaction(account_id, transaction_id):
    transaction = models.Transaction.query.get(transaction_id)
    if len(transaction.transfer_to):
        db.session.delete(transaction.transfer_to[0])
    db.session.delete(transaction)
    db.session.commit()
    return redirect('/account/%d/transactions' % account_id)


@app.route('/account/<int:account_id>/add_transaction/<operationtype>', methods=['GET', 'POST'])
def add_transaction(account_id, operationtype):
    if operationtype == 'transfer':
        return redirect('/account/%d/add_transfer' % account_id)
    
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

    # setting operation_type_choices
    form.operation_type.choices = zip(list_operation_type, list_operation_type)
    if operationtype == 'credit':
        form.operation_type.data = list_operation_type[-1]

    if form.validate_on_submit():
        # whatever the entry, if debit, the amount is negative
        # if credit, it is positive
        if operationtype == 'debit':
            amount = -abs(float(form.amount.data))
        elif operationtype == 'credit':
            amount = abs(float(form.amount.data))

        # creating database entry
        u = models.Transaction(date=form.date.data,
                               account=account.name,
                               amount=amount,
                               description=form.description.data.upper(),
                               category=form.category.data,
                               note=form.note.data.upper(),
                               operation_type=form.operation_type.data)

        if form.operation_type.data == 'cheque':
            u.cheque_number = int(form.cheque_number.data)

        # adding to database
        db.session.add(u)
        db.session.commit()
        return redirect('/account/%d/transactions' % account_id)
    else:
        previous_cheque_nb = models.Transaction.query.filter(models.Transaction.account == account.name)\
                                                 .filter(models.Transaction.cheque_number != None)\
                                                 .order_by(models.Transaction.cheque_number)\
                                                 .order_by(desc(models.Transaction.date)).all()

        if previous_cheque_nb:
            previous_cheque_nb = previous_cheque_nb[-1].cheque_number
        else:
            previous_cheque_nb = 0

        if operationtype == 'debit':
            form.cheque_number.data = str(int(previous_cheque_nb) + 1)

    return render_template('add_transaction.html',
                           account_id=account_id,
                           form=form, label_operationtype= 'Add %s' % operationtype,
                           currency=account.currency,
                           **context)


@app.route('/account/<int:account_id>/add_transfer', methods=['GET', 'POST'])
def add_transfer(account_id):
    account = models.Account.query.get(account_id)
    form = forms.AddTransferForm()
    accounts = pd.read_sql_table('account', db.engine)
    accounts = accounts[accounts.id != account_id]
    form.account_to.choices = zip(accounts.name, accounts.name)

    if form.validate_on_submit():
        # creating database entry
        amount = abs(float(form.amount.data))
        a = models.Transaction(date=form.date.data,
                               account=account.name,
                               amount=-amount,
                               description=form.description.data.upper(),
                               category='Transfer',
                               note=form.note.data.upper(),
                               operation_type='transfer')

        b = models.Transaction(date=form.date.data,
                               account=form.account_to.data,
                               amount=amount,
                               description=form.description.data.upper(),
                               category='Transfer',
                               note=form.note.data.upper(),
                               operation_type='transfer',
                               transfer_to=[a])
        a.transfer_to = [b]

        # adding to database
        db.session.add(a)
        db.session.add(b)
        db.session.commit()
        return redirect('/account/%d/transactions' % account_id)

    return render_template('add_transfer.html',
                           account_id=account_id,
                           account_from=account.name,
                           operationtype='transfer',
                           form=form,
                           currency=account.currency,
                           **context)


@app.route('/edit_transaction/account/<int:account_id>/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(account_id, transaction_id):
    form = forms.AddTransactionForm()

    # setting categories choice
    categories = list_category + ['Misc. Expense', 'Misc. Income']
    categories.sort()
    form.category.choices = zip(categories, categories)
    form.operation_type.choices = zip(list_operation_type, list_operation_type)

    # getting the transaction that is edited
    transaction = models.Transaction.query.get(transaction_id)

    if transaction.operation_type == 'transfer':
        abort(404)

    account = models.Account.query.get(account_id)

    if form.validate_on_submit():
        transaction.date = form.date.data
        transaction.amount = form.amount.data
        transaction.description = form.description.data.upper()
        transaction.category = form.category.data
        transaction.note = form.note.data.upper()
        transaction.operation_type = form.operation_type.data
        if transaction.operation_type == 'cheque':
            transaction.cheque_number = int(form.cheque_number.data)
        db.session.commit()
        return redirect('/account/%d/transactions' % account.id)
    else:
        form.date.data = transaction.date
        form.amount.data = '%.2f' % transaction.amount
        form.description.data = transaction.description
        form.category.data = transaction.category
        form.note.data = transaction.note
        form.operation_type.data = transaction.operation_type
        if transaction.operation_type == 'cheque':
            form.cheque_number.data = transaction.cheque_number
        else:
            previous_cheque_nb = models.Transaction.query.filter(models.Transaction.account == account.name)\
                                                     .filter(models.Transaction.cheque_number != None)\
                                                     .order_by(models.Transaction.cheque_number)\
                                                     .order_by(desc(models.Transaction.date)).all()

            if previous_cheque_nb:
                previous_cheque_nb = previous_cheque_nb[-1].cheque_number
            else:
                previous_cheque_nb = 0

            form.cheque_number.data = str(int(previous_cheque_nb) + 1)

    return render_template('add_transaction.html', 
                           label_operationtype= 'Edit transaction',
                           account_id=account.id,
                           form=form, currency=account.currency,
                           **context)


@app.route('/account/<int:account_id>/scheduled_transactions')
def scheduled_transactions(account_id):
    account = models.Account.query.get(account_id)
    data = pd.read_sql_table('scheduled_transaction', db.engine)
    data = data[data['account'] == account.name]

    monthly_income = 0
    monthly_expense = 0
    for idx, operation in data.iterrows():
        i = 0
        first_day = datetime.datetime.now().replace(day=1)
        last_day = first_day + relativedelta(months=+1)
        while first_day \
            + relativedelta(**{operation.every_type: i * operation.every_nb}) \
            < last_day:
            i += 1
        if operation.amount >= 0:
            monthly_income += operation.amount * i
        else:
            monthly_expense += operation.amount * i

    # selecting only scheduled transactions that are still active
    data = data[(data['ends'] > datetime.datetime.now()) | pd.isnull(data['ends'])]

    pd.to_datetime(data['next_occurence'])

    data = data.rename(columns={'next_occurence': 'next occurence'})

    pd.set_option('display.max_colwidth', 2000)

    # category icons
    data['category'] = data['category'].map(lambda x: '<i class="fa %s fa-fw" rel="tooltip" data-toggle="tooltip" data-placement="top" title="%s"></i>' % (dict_category2icon[x], x))
    
    # every is mix of two columns
    data['every'] = data['every_nb'].astype(str) + ' ' + data['every_type'].astype(str)


    data['action'] = ('<div class="btn-group">'
                 '    <a class="btn btn-xs dropdown-toggle" data-toggle="dropdown" style="color: #2C3E50;" rel="tooltip" data-toggle="tooltip" data-placement="top" title="actions">'
                       '         <i class="fa fa-cog"></i>'
                       '    </a>'
                 '<ul class="dropdown-menu" role="menu">')
    data['action'] += np.where(data['note'] != '', 
                          ('<li>'
                           '<a href="/info_scheduled_transaction/' + data['id'].astype(str) + 
                           '" class="transactioninfo"><i class="fa fa-info fa-fw"></i> Information</a>'
                           '</li>'),
                          '')
    data['action'] += ('<li>'
                  '<a href="/edit_scheduled_transaction/account/%s/' % account_id + data['id'].astype(str) + 
                  '"><i class="fa fa-edit fa-fw"></i> Edit</a></li>')
    data['action'] += ('<li>'
                  '<a href="/delete_scheduled_transaction/account/%s/' % account_id + data['id'].astype(str) + 
                  '" class="confirmdelete"><i class="fa fa-trash-o fa-fw"></i> Delete </a></li>')
    data['action'] += '</ul></div>'

    # sorting based on next occurence
    data = data.sort('next occurence')

    # adding the total amount
    currency = '(<i class="fa fa-%s"></i>)' % account.currency

    # replacing amount by in and out for easier reading
    data['amount %s' % currency] = np.nan
    data['amount %s' % currency].loc[data['amount'] >= 0] = "<p class='text-success'> <i class='fa fa-chevron-up'></i> " + data[data['amount'] >= 0]['amount'].astype(str) + "</p>" 
    data['amount %s' % currency].loc[data['amount'] < 0] = "<p class='text-danger'> <i class='fa fa-chevron-down'></i> " + data[data['amount'] < 0]['amount'].astype(str) + "</p>" 

    data['create_btn'] = np.where(data['next occurence'] <= datetime.datetime.now(), '#E74C3C', '#95a5a6')

    data['action'] += ('<a href="/create_scheduled_transaction/%s/' % account_id + data['id'].astype(str) + '" class="btn btn-xs confirmcreate" style="color:' + data['create_btn'] + ';" rel="tooltip" data-toggle="tooltip" data-placement="top" title="create">'
                       '         <i class="fa fa-play-circle"></i>'
                       '</a>')    
    data['action'] += ('<a href="/skip_scheduled_transaction/%s/' % account_id + data['id'].astype(str) + '" class="btn btn-xs confirmskip" style="color:#95a5a6;" rel="tooltip" data-toggle="tooltip" data-placement="top" title="skip">'
                       '         <i class="fa fa-step-forward"></i>'
                       '</a>')

    # displaying the pandas data as an html table
    data = data[['action', 'next occurence', 'description', 
                 'category', 'amount %s' % currency, 
                 'every']]

    data = data.to_html(classes=['table table-hover table-bordered table-striped table-condensed'], 
                        index=False, escape=False, na_rep='')

    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions(account_name=account.name)

    return render_template('scheduled_transactions.html', data=data,
                           monthly_expense=monthly_expense, monthly_income=monthly_income,
                           currency=account.currency,
                           account_id=account_id, **context)


@app.route('/delete_scheduled_transaction/account/<int:account_id>/<int:transaction_id>')
def delete_scheduled_transaction(account_id, transaction_id):
    transaction = models.ScheduledTransaction.query.get(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    account = models.Account.query.get(account_id)
    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions(account_name=account.name)
    return redirect('/account/%d/scheduled_transactions' % account_id)


@app.route('/account/<int:account_id>/add_scheduled_transaction/<operationtype>', methods=['GET', 'POST'])
def add_scheduled_transaction(account_id, operationtype):
    account = models.Account.query.get(account_id)
    form = forms.AddScheduledTransactionForm()
    form.date.label = 'next occurence'

    # adding an extra category depending on type of operation
    if operationtype == 'debit':
        additional_category = 'Misc. Expense'
    elif operationtype == 'credit':
        additional_category = 'Misc. Income'
    categories = list_category + [additional_category]
    categories.sort()
    form.category.choices = zip(categories, categories)

    if form.is_submitted():
        if operationtype == 'debit':
            amount = -abs(float(form.amount.data))
        elif operationtype == 'credit':
            amount = abs(float(form.amount.data))
        # creating database entry
        u = models.ScheduledTransaction(next_occurence=form.date.data,
                                        amount=amount,
                                        account=account.name,
                                        description=form.description.data.upper(),
                                        category=form.category.data,
                                        note=form.note.data.upper(),
                                        every_nb=form.every_nb.data, 
                                        every_type=form.every_type.data,
                                        ends=form.ends.data)

        # adding to database
        db.session.add(u)
        db.session.commit()
        context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions(account_name=account.name)
        return redirect('/account/%d/scheduled_transactions' % account_id)
    return render_template('add_transaction.html', 
                           form=form, 
                           account_id=account_id,
                           currency=account.currency,
                           label_operationtype= 'Add scheduled %s' % operationtype,
                           **context)


@app.route('/create_scheduled_transaction/<int:account_id>/<int:transaction_id>')
def create_scheduled_transaction(account_id, transaction_id):
    s_transaction = models.ScheduledTransaction.query.get(transaction_id)
    u = models.Transaction(date=s_transaction.next_occurence,
                           account=s_transaction.account,
                           amount=s_transaction.amount,
                           description=s_transaction.description.upper(),
                           operation_type='other',
                           category=s_transaction.category,
                           note=s_transaction.note.upper())

    # adding new transaction to database
    db.session.add(u)

    # updating scheduled transaction next occurence
    s_transaction.next_occurence = s_transaction.next_occurence + \
        relativedelta(**{s_transaction.every_type: s_transaction.every_nb})
    db.session.commit()

    account = models.Account.query.get(account_id)
    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions(account_name=account.name)

    return redirect('/account/%d/scheduled_transactions' % account_id)


@app.route('/skip_scheduled_transaction/<int:account_id>/<int:transaction_id>')
def skip_scheduled_transaction(account_id, transaction_id):
    s_transaction = models.ScheduledTransaction.query.get(transaction_id)
    s_transaction.next_occurence = s_transaction.next_occurence + \
        relativedelta(**{s_transaction.every_type: s_transaction.every_nb})
    db.session.commit()
    account = models.Account.query.get(account_id)

    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions(account_name=account.name)
    return redirect('/account/%d/scheduled_transactions' % account_id)


@app.route('/info_scheduled_transaction/<int:transaction_id>')
def info_scheduled_transaction(transaction_id):
    s_transaction = models.ScheduledTransaction.query.get(transaction_id)
    return render_template('info_transaction.html', 
                           note=s_transaction.note,
                           **context)


@app.route('/edit_scheduled_transaction/account/<int:account_id>/<int:transaction_id>', methods=['GET', 'POST'])
def edit_scheduled_transaction(account_id, transaction_id):
    form = forms.AddScheduledTransactionForm()
    form.date.label = 'next occurence'
    categories = list_category + ['Misc. Expense', 'Misc. Income']
    categories.sort()
    form.category.choices = zip(categories, categories)
    # getting the transaction element
    transaction = models.ScheduledTransaction.query.get(transaction_id)
    account = models.Account.query.get(account_id)

    if form.is_submitted():
        # update the rssfeed column
        transaction.next_occurence = form.date.data
        transaction.amount = form.amount.data
        transaction.description = form.description.data.upper()
        transaction.category = form.category.data
        transaction.note = form.note.data.upper()
        transaction.every_nb = int(form.every_nb.data)
        transaction.every_type = form.every_type.data
        transaction.ends = form.ends.data
        db.session.commit()
        context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions(account_name=account.name)
        return redirect('/account/%d/scheduled_transactions' % account.id)
    else:
        form.date.data = transaction.next_occurence
        form.amount.data = '%.2f' % transaction.amount
        form.description.data = transaction.description
        form.category.data = transaction.category
        form.note.data = transaction.note
        form.every_nb.data = str(transaction.every_nb)
        form.every_type.data = transaction.every_type
        form.ends.data = transaction.ends
    return render_template('add_transaction.html', 
                           account_id=account.id,
                           currency=account.currency,
                           label_operationtype= 'Edit scheduled transaction',
                           form=form,
                           **context)


@app.route('/account/<int:account_id>/graph/', methods=['GET', 'POST'])
def display_graph(account_id):
    account = models.Account.query.get(account_id)
    df = pd.read_sql_table('transaction', db.engine)
    df = df[df['account'] == account.name]

    try:
        min_date = df['date'].min().strftime('%d/%m/%Y')
    except AttributeError:
        min_date = 0

    def compute(df, start_day, end_day):
        df = df[(df['date'] >= start_day) & (df['date'] <= end_day)]
        df = df.groupby('category')[['amount']].sum()
        return df

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

    data = compute(df, start_day, end_day)
    csv_fname = os.path.join(app.config['DB_FOLDER'], '..', 'analysis_per_category.xls')
    data.to_excel(csv_fname)
    csv_fname = os.path.relpath(csv_fname, start=app.config['BASEDIR'])
    data['str_category'] = data.index.copy()
    data['category'] = np.nan

    normalization = max(abs(data[data['amount'] < 0].sum()['amount']), 
                        abs(data[data['amount'] >= 0].sum()['amount']))

    total_expense = np.sum(data[data['amount'] < 0]['amount'])
    total_expense_width = 80 * total_expense / normalization
    total_income = np.sum(data[data['amount'] >= 0]['amount'])
    total_income_width = 80 * total_income / normalization

    data.loc[data['amount'] >= 0, 'category'] = data[data['amount'] >= 0].index.map(lambda x: '<i class="fa %s fa-fw"></i>' % (dict_category2icon[x]))
    data.loc[data['amount'] < 0, 'category'] = data[data['amount'] < 0].index.map(lambda x: '<i class="fa %s fa-fw"></i>' % (dict_category2icon[x]))
    data['percent'] = 80 * data['amount'] / normalization

    
    data['category_link'] = data['str_category'].map(lambda x: category_id(x)).astype(str) \
                            + '/' + start_day.strftime('%d%m%Y') + end_day.strftime('%d%m%Y')

    return render_template('graphs.html',
                           account_id=account.id, csv_fname=csv_fname, 
                           form=form, data=list(data.itertuples()), min_date=min_date,
                           total_expense=total_expense, total_expense_width=total_expense_width,
                           total_income=total_income, total_income_width=total_income_width,
                           currency=account.currency,
                           **context)


@app.route('/account/<int:account_id>/graph/<category_id>/<date_range>')
def transactions_category(account_id, category_id, date_range):
    account = models.Account.query.get(account_id)

    start_date = datetime.datetime.strptime(date_range[:8], '%d%m%Y')
    end_date = datetime.datetime.strptime(date_range[8:], '%d%m%Y')

    data = pd.read_sql_table('transaction', db.engine)
    data = data[(data['account'] == account.name) & 
                (data['category'] == category_name(int(category_id))) &
                (data['date'] >= start_date) &
                (data['date'] <= end_date)]

    pd.set_option('display.max_colwidth', 1000)

    data['action'] = ('<div class="btn-group">'
                 '    <button type="button" class="btn btn btn-default btn-xs dropdown-toggle" data-toggle="dropdown">'
                 '         <i class="fa fa-cog"></i>'
                 '    </button>'
                 '<ul class="dropdown-menu" role="menu">')
    data['action'] += np.where(data['note'] != '', 
                          ('<li>'
                           '<a href="/info_transaction/' + data['id'].astype(str) + 
                           '" class="transactioninfo"><i class="fa fa-info fa-fw"></i> Information</a>'
                           '</li>'),
                          '')
    data['action'] += ('<li>'
                  '<a href="/edit_transaction/' + data['id'].astype(str) + 
                  '"><i class="fa fa-edit fa-fw"></i> Edit</a></li>')
    data['action'] += ('<li>'
                  '<a href="/delete_transaction/' + data['id'].astype(str) + 
                  '" class="confirmdelete"><i class="fa fa-trash-o fa-fw"></i> Delete </a></li>')
    data['action'] += '</ul></div>'

    # sorting based on descending date
    total_amount = np.sum(data['amount'])
    if total_amount >= 0:
        data = data.sort(['amount'], ascending=False)
    else:
        data = data.sort(['amount'], ascending=True)

    # adding the total amount
    currency = '(<i class="fa fa-%s"></i>)' % account.currency

    # replacing amount by in and out for easier reading
    data['amount %s' % currency] = np.nan
    data['amount %s' % currency].loc[data['amount'] >= 0] = "<p class='text-success'> <i class='fa fa-chevron-up'></i> " + data[data['amount'] >= 0]['amount'].astype(str) + "</p>" 
    data['amount %s' % currency].loc[data['amount'] < 0] = "<p class='text-danger'> <i class='fa fa-chevron-down'></i> " + data[data['amount'] < 0]['amount'].astype(str) + "</p>" 

    # displaying the pandas data as an html table
    data = data[['action', 'date', 'description',
                 'amount %s' % currency]]

    data = data.to_html(classes=['table table-hover table-bordered table-striped table-condensed'], 
                        index=False, escape=False, na_rep='')
    return render_template('transactions.html', data=data, 
                           currency=account.currency, category=category_name(int(category_id)), 
                           account_id=account_id, **context)


@app.route('/account/<int:account_id>/reconcile')
def reconcile_transactions(account_id):
    form = forms.ReconcileTransactionsForm()
    account = models.Account.query.get(account_id)
    return render_template('reconcile_form.html', form=form,
                           currency=account.currency,
                           account_id=account_id, **context)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', **context), 404
