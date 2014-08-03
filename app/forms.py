from flask_wtf import Form
from wtforms import TextField, DateField, SelectField
from wtforms.validators import Required, length
from unidecode import unidecode


class AddTransactionForm(Form):
    date = DateField('date', format='%d/%m/%Y', validators=[Required()])
    amount = TextField('amount', validators=[Required()])
    description = TextField('description', validators=[Required(), length(max=20)])
    category = SelectField('category', validators=[Required()])
    note = TextField('note')