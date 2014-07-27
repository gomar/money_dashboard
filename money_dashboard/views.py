from flask import render_template
import os
from money_dashboard import money_dashboard
from flask.ext.sqlalchemy import SQLAlchemy

money_dashboard.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///static/db/test.db'
db = SQLAlchemy(money_dashboard)

if not os.path.isfile('static/db/test.db'):
	db.create_all()


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

    def __repr__(self):
        return '<index %r>' % self.index


@money_dashboard.route('/')
def index():
    return render_template('index.html')
