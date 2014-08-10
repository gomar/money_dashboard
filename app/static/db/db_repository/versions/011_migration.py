from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
scheduled_transaction = Table('scheduled_transaction', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('next_occurence', DATE),
    Column('amount', NUMERIC(precision=2)),
    Column('description', TEXT),
    Column('category', TEXT),
    Column('note', TEXT),
    Column('account', TEXT),
)

transaction = Table('transaction', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('date', DATE),
    Column('amount', NUMERIC(precision=2)),
    Column('description', TEXT),
    Column('category', TEXT),
    Column('note', TEXT),
    Column('reconciled', BOOLEAN),
    Column('account', TEXT),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['scheduled_transaction'].columns['account'].drop()
    pre_meta.tables['transaction'].columns['account'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['scheduled_transaction'].columns['account'].create()
    pre_meta.tables['transaction'].columns['account'].create()
