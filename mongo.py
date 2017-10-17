from flask_mongoalchemy import MongoAlchemy
from flask_bcrypt import Bcrypt
db=MongoAlchemy()
bcrypt=Bcrypt()

def generatePassword(fn,ln,empID):
    return str(fn[0]).lower()+str(ln[0]).lower()+str(empID) #first initial, last initial, employee id

class Employee(db.Document):
    fn = db.StringField()
    ln = db.StringField()
    empID = db.StringField()
    password = db.StringField()
    admin = db.BoolField()
    clockedIn = db.StringField()
    active = db.BoolField()
    depts = db.ListField(db.StringField())
    def init(self,fn,ln,empID,admin,depts=["Lifeguard"]):
        self.fn = fn
        self.ln = ln
        self.password = bcrypt.generate_password_hash(generatePassword(fn,ln,empID))
        self.empID = empID
        self.admin = admin
        self.clockedIn = "None"
        self.active = True
        self.depts = depts
        self.save()
    
class Timecard(db.Document):
    empID = db.StringField()
    dept = db.StringField()
    action = db.StringField()
    datetime = db.DateTimeField()
    warning = db.BoolField()
    timecardID = db.StringField()

class User():
    def __init__(self,_id,admin=False):
        self.id = _id
        self.admin = admin
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def is_admin(self):
        return self.admin
    def get_id(self):
        return self.id