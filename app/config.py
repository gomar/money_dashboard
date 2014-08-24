import os
basedir = os.path.abspath(os.path.dirname(__file__))

DB_FOLDER = os.path.join(basedir, 'static', 'db')
DB_FNAME = os.path.join(DB_FOLDER, 'woney.db')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_FNAME
SQLALCHEMY_MIGRATE_REPO = os.path.join(DB_FOLDER, 'db_repository')
CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'
