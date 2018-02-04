from flask import Flask
from flask_login import LoginManager
import os
import pytz
from connect import *

app = Flask(__name__)

try:
    app.config['MONGOALCHEMY_DATABASE'] = os.environ['DB_NAME']
    app.config['MONGOALCHEMY_CONNECTION_STRING'] = os.environ['DB_URI']
except EnvironmentError as e:
    print("Make sure you have DB_NAME and DB_URI Environment variables defined.")
    raise e


app.secret_key = "blackbird"  # shh it's a secret

# Bcrypt
bcrypt.init_app(app)  # Initialize BCrypt -- imported from mongo.py

# Database
db.init_app(app)  # Initialize Database Connection -- imported from mongo.py

# Login Manager
lm = LoginManager()
lm.init_app(app)  # Initialize Login Manager
lm.login_view = "index"
lm.login_message = "Please enter your Employee ID and Password below."

tz = pytz.timezone('America/Los_Angeles')
time_string = '%m/%d/%Y %I:%M %p'
