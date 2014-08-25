from flask_wtf import Form
from wtforms import TextField, DateField, SelectField, RadioField, BooleanField
from wtforms.validators import DataRequired, length, ValidationError, NumberRange
from unidecode import unidecode


class AddTransactionForm(Form):
    date = DateField('date', format='%d/%m/%Y', validators=[DataRequired()])
    amount = TextField('amount', validators=[DataRequired()])
    description = TextField('description', validators=[DataRequired(), length(max=30)])
    category = SelectField('category', validators=[DataRequired()])
    note = TextField('note')


class AddScheduledTransactionForm(Form):
    date = DateField('date', format='%d/%m/%Y', validators=[DataRequired()])
    amount = TextField('amount', validators=[DataRequired()])
    description = TextField('description', validators=[DataRequired(), length(max=30)])
    category = SelectField('category', validators=[DataRequired()])
    note = TextField('note')
    every_nb = TextField('every', default=1, validators=[])
    every_type = RadioField('every_type', default='months', choices=zip(['months', 'weeks', 'days'],
                                                       ['months', 'weeks', 'days']), 
                             validators=[DataRequired()])
    ends = DateField('date', format='%d/%m/%Y')


class AddTransferForm(Form):
    date = DateField('date', format='%d/%m/%Y', validators=[DataRequired()])
    amount = TextField('amount', validators=[DataRequired()])
    description = TextField('description', validators=[DataRequired(), length(max=30)])
    note = TextField('note')
    account_to = SelectField('account_to', validators=[DataRequired()])


class SelectDateRangeForm(Form):
    start = TextField('start', validators=[DataRequired()])
    end = TextField('end', validators=[DataRequired()])


class AddAccount(Form):
    name = TextField('name', validators=[DataRequired()])
    currency = SelectField('currency', 
                           validators=[DataRequired()])
    initial_balance = TextField('initial balance', default=0, validators=[DataRequired()])
