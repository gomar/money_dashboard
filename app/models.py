from app import db


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    account = db.Column(db.Text, db.ForeignKey("account.name"))
    amount = db.Column(db.Numeric(precision=2))
    description = db.Column(db.Text)
    category = db.Column(db.Text)
    note = db.Column(db.Text)

    def __repr__(self):
        return '<id %r>' % self.id


class ScheduledTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    next_occurence = db.Column(db.Date)
    account = db.Column(db.Text, db.ForeignKey("account.name"))
    amount = db.Column(db.Numeric(precision=2))
    description = db.Column(db.Text)
    category = db.Column(db.Text)
    note = db.Column(db.Text)

    def __repr__(self):
        return '<id %r>' % self.id


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    currency = db.Column(db.Text)

    def __repr__(self):
        return '<name %r>' % self.name

