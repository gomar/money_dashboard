from flask_wtf import Form
from wtforms import TextField, DateField, SelectField
from wtforms.validators import Required



class AddTransactionForm(Form):
    date = DateField('date', format='%d/%m/%Y', validators=[Required()])
    amount = TextField('amount', validators=[Required()])
    description = TextField('description', validators=[Required()])
    category = SelectField('category', choices=[('', '--'),
    											('household', 'Household'), 
    	                                        ('day2day', 'Day to day'),
    	                                        ('extras', 'Extra activities')])
    note = TextField('note')