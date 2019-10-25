from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from util import ListConverter


app = Flask(__name__)

app.url_map.converters['list'] = ListConverter

app.config['ENVIRONMENT'] = 'DEVELOPMENT'

if app.config['ENVIRONMENT']=='DEVELOPMENT':
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root@localhost/mill"
    app.config['DEBUG'] = True

if app.config['ENVIRONMENT']=='TESTING':
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root@localhost/mill_staging"
    app.config['SQLALCHEMY_BINDS'] = {
        'TEST_STAGING': 'mysql+pymysql://root@localhost/mill_staging?charset=utf8',
        'STAGING': 'mysql+pymysql://root@localhost/mill_staging',
    }
    app.config['DEBUG'] = True
    app.config['SECURITY_PASSWORD_SALT'] = 'aijldbvaihwrbviqu3b4u8o'
    app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin'
    app.config['SECURITY_TRACKABLE'] = True



if app.config['ENVIRONMENT']=='STAGING':
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://staging-millmarginalia:BPeuVxrjp2FklMGIQEHU@localhost/staging_millmarginalia"
    app.config['SQLALCHEMY_BINDS'] = {
        'PRODUCTION': 'mysql+pymysql://mill:D&AdWX43**s5A4tvj#((11.&6@localhost/mill',
    }

    app.config['DEBUG'] = True
    app.config['SECURITY_PASSWORD_SALT'] = 'aijldbvaihwrbviqu3b4u8o'
    app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin'
    app.config['SECURITY_TRACKABLE'] = True



if app.config['ENVIRONMENT'] == 'PRODUCTION':
    from raven.contrib.flask import Sentry
    import logging
    from flask_htmlmin import HTMLMIN

    sentry = Sentry(app, dsn='https://ed830be94ad4456c9bfa285200855403:670cd1b81cee490b99e890453f0e1c8f@sentry.io/208499', logging=True, level=logging.ERROR)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://mill:D&AdWX43**s5A4tvj#((11.&6@localhost/mill"
    # app.config['SQLALCHEMY_BINDS'] = {
    #     'staging': 'mysql+pymysql://root@localhost/mill_staging',
    # }
    # app.config["APPLICATION_ROOT"] = "/apps/millmarginalia"
    app.config['DEBUG'] = False
    app.config['MINIFY_PAGE'] = True
    HTMLMIN(app)


app.secret_key = "super secret key"
db = SQLAlchemy(app)


# python3 -m venv venv
# source venv/bin/activate
# pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-Script Flask-Security psycopg2 bcrypt pymysql raven[flask]
