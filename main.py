"""
this is the "secret sauce" -- a single entry-point that resolves the
import dependencies.  If you're using blueprints, you can import your
blueprints here too.

then when you want to run your app, you point to main.py or `main.app`
"""
from app import app, db

# from models import *
from models.author import Author
from models.book import Book
from models.page import Page
from models.marginalia import Marginalia
from models.import_models import ImportItem
from models.user import *

# from admin_views import *
from front_views import *
from test_views import *
from search_views import *
from api import *
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore

# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
security = Security(app, user_datastore)

if __name__ == '__main__':
    # db.session.rollback()
    # db.create_all()
    # user_datastore.create_user(email='thgrace@ua.edu', password='Soccer12!@')
	# db.session.commit()
    app.run(debug=True)