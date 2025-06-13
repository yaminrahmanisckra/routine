import os
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from .config import Config
from .db import db

app = Flask(__name__, template_folder=os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'templates'))
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from .models import Teacher

@login_manager.user_loader
def load_user(user_id):
    return Teacher.query.get(int(user_id))

with app.app_context():
    from . import models
    db.create_all()

from . import routes
