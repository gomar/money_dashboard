from app import db


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reconciled = db.Column(db.Boolean)
    date = db.Column(db.Date)
    description = db.Column(db.Text)
    amount = db.Column(db.Numeric(precision=2))
    note = db.Column(db.Text)

    def __init__(self, reconciled, date, description, amount, note):
        self.reconciled = reconciled
        self.date = date
        self.description = description
        self.amount = amount
        self.note = note

    def __repr__(self):
        return '<id %r>' % self.id