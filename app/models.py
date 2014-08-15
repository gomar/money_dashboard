from app import db


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reconciled = db.Column(db.Boolean)
    date = db.Column(db.Date)
    amount = db.Column(db.Numeric(precision=2))
    description = db.Column(db.Text)
    category = db.Column(db.Text)
    note = db.Column(db.Text)

    def __repr__(self):
        return '<id %r>' % self.id


class ScheduledTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    next_occurence = db.Column(db.Date)
    amount = db.Column(db.Numeric(precision=2))
    description = db.Column(db.Text)
    category = db.Column(db.Text)
    note = db.Column(db.Text)

    def __repr__(self):
        return '<id %r>' % self.id