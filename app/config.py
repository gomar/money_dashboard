import os
basedir = os.path.abspath(os.path.dirname(__file__))

DB_FNAME = os.path.join(basedir, 'static', 'db', 'app.db')
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_FNAME
CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'
