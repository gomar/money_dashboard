from flask_wtf import Form
from wtforms import TextField, DateField, SelectField


class AddTransactionForm(Form):
    date = DateField('date')
    amount = TextField('amount')
    description = TextField('description')
    category = SelectField('category', choices=[(None, ''),
    											('household', 'Household'), 
    	                                        ('day2day', 'Day to day'),
    	                                        ('extras', 'Extra activities')])
    note = TextField('note')