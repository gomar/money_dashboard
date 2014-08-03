from flask_wtf import Form
from wtforms import TextField, DateField, SelectField
from wtforms.validators import DataRequired, length
from unidecode import unidecode


class AddTransactionForm(Form):
    date = DateField('date', format='%d/%m/%Y', validators=[DataRequired()])
    amount = TextField('amount', validators=[DataRequired()])
    description = TextField('description', validators=[DataRequired(), length(max=20)])
    category = SelectField('category', validators=[DataRequired()])
    note = TextField('note')