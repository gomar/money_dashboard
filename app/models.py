from app import db

#Table to handle the self-referencing many-to-many relationship for the User class:
#First column holds the user who follows, the second the user who is being followed.
transfer = db.Table('transfer',
    db.Column("from_account", db.Text, db.ForeignKey("transaction.id"), primary_key=True),
    db.Column("to_account", db.Text, db.ForeignKey("transaction.id"), primary_key=True)
)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    account = db.Column(db.Text, db.ForeignKey("account.name"))
    amount = db.Column(db.Numeric(precision=2))
    description = db.Column(db.Text)
    category = db.Column(db.Text)
    note = db.Column(db.Text)
    operation_type = db.Column(db.Text)
    cheque_number = db.Column(db.Integer)
    transfer_to = db.relationship("Transaction", 
                                  secondary=transfer,
                                  primaryjoin=id==transfer.c.from_account,
                                  secondaryjoin=id==transfer.c.to_account,
                                  backref="transfer_from")

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
    every_nb = db.Column(db.Integer)
    every_type = db.Column(db.Text)
    ends = db.Column(db.Date)

    def __repr__(self):
        return '<id %r>' % self.id


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    currency = db.Column(db.Text)
    reconciled_balance = db.Column(db.Numeric(precision=2))

    def __repr__(self):
        return '<name %r>' % self.name

