from flask import Flask, request, flash, render_template, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, fresh_login_required, current_user
import os, datetime, pytz
from flask_bcrypt import Bcrypt
from datetime import timedelta
from mongo import *
from db import *
from classes import *

app = Flask(__name__)
app.config['MONGOALCHEMY_DATABASE'] = DATABASE
app.config['MONGOALCHEMY_CONNECTION_STRING'] = CONNECTION_STRING#flaskapp

app.secret_key = "blackbird"

lm = LoginManager()

bcrypt.init_app(app)
db.init_app(app)
lm.init_app(app)
lm.login_view = "index"
lm.login_message = "Please enter your Employee ID and Password below."

tz = pytz.timezone('America/Los_Angeles')