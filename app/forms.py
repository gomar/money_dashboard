from flask_wtf import Form
from wtforms import TextField, DateField, SelectField
from wtforms.validators import Required, length
from unidecode import unidecode


class AddTransactionForm(Form):
    date = DateField('date', format='%d/%m/%Y', validators=[Required()])
    amount = TextField('amount', validators=[Required()])
    description = TextField('description', validators=[Required(), length(max=20)])
    category = SelectField('category', choices=[('child', 'Childcare'), 
                                                ('transport', 'Transport'), 
                                                ('leisure', 'Entertainment & Leisure'), 
                                                ('beauty', 'Beauty & Clothing'), 
                                                ('bills', 'Bills'), 
                                                ('other', 'Other'), 
                                                ('day2day', 'Day to day expenses'), 
                                                ('healthcare', 'Healthcare')],
                           validators=[Required()])
    note = TextField('note')