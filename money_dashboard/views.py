from flask import render_template
from money_dashboard import money_dashboard
from flask.ext.sqlalchemy import SQLAlchemy

money_dashboard.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////static/db/test.db'
db = SQLAlchemy(money_dashboard)


class Transaction(db.Model):
    index = db.Column(db.Integer, primary_key=True)
    reconciled = db.Column(db.Boolean)
    date = db.Column(db.Date)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(precision=2))

    def __init__(self, reconciled, date, description, amount):
        self.reconciled = reconciled
        self.date = date
        self.description = description
        self.amount = amount


@money_dashboard.route('/')
def index():
    return render_template('index.html')
