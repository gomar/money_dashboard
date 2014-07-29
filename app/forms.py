from flask_wtf import Form
from wtforms import TextField, DateField


class AddTransactionForm(Form):
    date = DateField('date')
    description = TextField('description')
