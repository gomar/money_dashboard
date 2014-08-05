from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
scheduled_transaction = Table('scheduled_transaction', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('next_occurence', Date),
    Column('amount', Numeric(precision=2)),
    Column('description', Text),
    Column('category', Text),
    Column('note', Text),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['scheduled_transaction'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['scheduled_transaction'].drop()
