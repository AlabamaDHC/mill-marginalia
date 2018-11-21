from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_htmlmin import HTMLMIN
from util import ListConverter

#PRODUCTION
from raven.contrib.flask import Sentry
import logging

app = Flask(__name__)

app.url_map.converters['list'] = ListConverter

# PRODUCTION SETTINGS
sentry = Sentry(app, dsn='https://ed830be94ad4456c9bfa285200855403:670cd1b81cee490b99e890453f0e1c8f@sentry.io/208499', logging=True, level=logging.ERROR)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://mill:D&AdWX43**s5A4tvj#((11.&6@localhost/mill"
app.config["APPLICATION_ROOT"] = "/apps/millmarginalia"
app.config['DEBUG'] = False
app.config['MINIFY_PAGE'] = True



# NEW DEV SETTINGSdeactivate
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root@localhost/mill"
# app.config['SECURITY_PASSWORD_SALT'] = 'aijldbvaihwrbviqu3b4u8o'
# app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin'
# app.config['SECURITY_TRACKABLE'] = True
# app.config['DEBUG'] = True


# OLD DEV SETTINGS
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://localhost:5432/mill"
# app.config['SECURITY_PASSWORD_SALT'] = 'aijldbvaihwrbviqu3b4u8o'
# app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin'
# app.config['SECURITY_TRACKABLE'] = True


# app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = 'username'

app.secret_key = "super secret key"
db = SQLAlchemy(app)
HTMLMIN(app)



# python3 -m venv venv
# source venv/bin/activate
# pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-Script Flask-Security psycopg2 bcrypt pymysql raven[flask]
