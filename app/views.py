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
'Misc. Expense': 'fa-question-circle'}

list_currency = [('euro', u'Euro (<i class="fa fa-euro"></i>)'), 
                 ('gbp', u'British pound (<i class="fa fa-gbp"></i>)')]

list_operation_type = ['credit card', 'online payment', 'cheque', 'other']


def update_waiting_scheduled_transactions():
    if os.path.exists(app.config['DB_FNAME']):
        return models.ScheduledTransaction.query\
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
    accounts = get_balance()
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
    scheduled_transactions = models.ScheduledTransaction.query.filter(models.Transaction.account == account.name).all()
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

    pd.set_option('display.max_colwidth', 1000)

    data['category'] = data['category'].map(lambda x: '<i class="fa %s fa-fw" rel="tooltip" data-toggle="tooltip" data-placement="top" title="%s"></i>' % (dict_category2icon[x], x))

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
                  '" class="confirmdelete"><i class="fa fa-trash-o fa-fw"></i> Remove</a></li>')
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


@app.route('/delete_transaction/<int:transaction_id>')
def delete_transaction(transaction_id):
    transaction = models.Transaction.query.get(transaction_id)
    if len(transaction.transfer_to):
        db.session.delete(transaction.transfer_to[0])
    db.session.delete(transaction)
    db.session.commit()
    account_id = models.Account.query\
            .filter(models.Account.name == transaction.account).all()[0].id
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
                           operationtype='Transfer',
                           form=form,
                           currency=account.currency,
                           **context)


@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
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

    account = models.Account.query.filter(models.Account.name == transaction.account).all()[0]

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
    df = pd.read_sql_table('scheduled_transaction', db.engine)
    df = df[df['account'] == account.name]
    df = df[(df['ends'] > datetime.datetime.now()) | pd.isnull(df['ends'])]
    pd.to_datetime(df['next_occurence'])
    df = df.sort('next_occurence')
    df = pd.DataFrame(df.values, columns=df.columns)
    df_dict = df.T.to_dict()
    scheduled_transactions = [df_dict[i] for i in range(len(df_dict))]
    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()
    return render_template('scheduled_transactions.html', 
                           scheduled_transactions=scheduled_transactions,
                           account_id=account_id,
                           currency=account.currency,
                           **context)


@app.route('/delete_scheduled_transaction/<int:transaction_id>')
def delete_scheduled_transaction(transaction_id):
    transaction = models.ScheduledTransaction.query.get(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    account_id = models.Account.query\
            .filter(models.Account.name == transaction.account).all()[0].id
    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()
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
        context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()
        return redirect('/account/%d/scheduled_transactions' % account_id)
    return render_template('add_transaction.html', 
                           form=form, 
                           account_id=account_id,
                           currency=account.currency,
                           label_operationtype= 'Add scheduled transaction',
                           **context)


@app.route('/create_scheduled_transaction/<int:transaction_id>')
def create_scheduled_transaction(transaction_id):
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

    account_id = models.Account.query\
            .filter(models.Account.name == s_transaction.account).all()[0].id
    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()

    return redirect('/account/%d/scheduled_transactions' % account_id)


@app.route('/skip_scheduled_transaction/<int:transaction_id>')
def skip_scheduled_transaction(transaction_id):
    s_transaction = models.ScheduledTransaction.query.get(transaction_id)
    s_transaction.next_occurence = s_transaction.next_occurence + \
        relativedelta(**{s_transaction.every_type: s_transaction.every_nb})
    db.session.commit()
    account_id = models.Account.query\
            .filter(models.Account.name == s_transaction.account).all()[0].id
    context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()
    return redirect('/account/%d/scheduled_transactions' % account_id)


@app.route('/info_scheduled_transaction/<int:transaction_id>')
def info_scheduled_transaction(transaction_id):
    s_transaction = models.ScheduledTransaction.query.get(transaction_id)
    return render_template('info_transaction.html', 
                           note=s_transaction.note,
                           **context)


@app.route('/edit_scheduled_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_scheduled_transaction(transaction_id):
    form = forms.AddScheduledTransactionForm()
    form.date.label = 'next occurence'
    categories = list_category + ['Misc. Expense', 'Misc. Income']
    categories.sort()
    form.category.choices = zip(categories, categories)
    # getting the transaction element
    transaction = models.ScheduledTransaction.query.get(transaction_id)
    account = models.Account.query\
        .filter(models.Account.name == transaction.account).all()[0]

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
        context['waiting_scheduled_transactions'] = update_waiting_scheduled_transactions()
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


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', **context), 404
