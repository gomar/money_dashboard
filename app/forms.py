from flask_wtf import Form
from wtforms import TextField, DateField, SelectField
from wtforms.validators import Required, length
from unidecode import unidecode


class AddTransactionForm(Form):
    date = DateField('date', format='%d/%m/%Y', validators=[Required()])
    amount = TextField('amount', validators=[Required()])
    description = TextField(unidecode('description'), validators=[Required()])
    category = SelectField('category', choices=[('', '--'),
    											('household', 'Household'), 
    	                                        ('day2day', 'Day to day'),
    	                                        ('extras', 'Extra activities')])
    note = TextField(unidecode('note'), [length(max=20)])