import os

DB_FNAME = 'static/db/test.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % DB_FNAME
SQLALCHEMY_MIGRATE_REPO = os.path.join(os.path.split(DB_FNAME)[0], 'db_repository')
FREEZER_DESTINATION = '../build/'
CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'
