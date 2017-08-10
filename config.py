from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from datetime import timedelta
from mongo import *
from db import *

app = Flask(__name__)
app.config['MONGOALCHEMY_DATABASE'] = DATABASE
app.config['MONGOALCHEMY_CONNECTION_STRING'] = CONNECTION_STRING#flaskapp

app.secret_key = "blackbird"

lm = LoginManager()

bcrypt.init_app(app)
db.init_app(app)
lm.init_app(app)
lm.refresh_view = "timecard"
lm.login_view = "timecard"
lm.login_message = "Please enter your Employee ID and Password below."