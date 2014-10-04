from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
account = Table('account', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('name', Text),
    Column('currency', Text),
    Column('reconciled_balance', Numeric(precision=2)),
    Column('reconciled_date', Date),
    Column('tmp_reconciled_balance', Numeric(precision=2)),
    Column('tmp_reconciled_date', Date),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['account'].columns['tmp_reconciled_balance'].create()
    post_meta.tables['account'].columns['tmp_reconciled_date'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['account'].columns['tmp_reconciled_balance'].drop()
    post_meta.tables['account'].columns['tmp_reconciled_date'].drop()
