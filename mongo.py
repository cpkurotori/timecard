from flask_mongoalchemy import MongoAlchemy
from flask_bcrypt import Bcrypt
import uuid
db = MongoAlchemy()
bcrypt = Bcrypt()


def generate_password(fn, ln, emp_id):
    """Returns a string of the default password in
       the form {FirstInitial}{LastInitial}{EmployeeID}"""
    return "{0}{1}{2}".format(str(fn[0]).lower(), str(ln[0]).lower(), str(emp_id))


def check_password(hashed, check):
    """Returns boolean of if the input password matches the hashed password"""
    return bcrypt.check_password_hash(hashed, check)


class Department(db.Document):
    name = db.StringField()
    dept_id = db.StringField()

    def init(self, dept):
        self.name = dept
        self.dept_id = uuid.uuid4().hex
        self.save()

class Employee(db.Document):
    fn = db.StringField()
    ln = db.StringField()
    emp_id = db.StringField()
    password = db.StringField()
    admin = db.BoolField()
    clocked_in = db.StringField()
    active = db.BoolField()
    depts = db.ListField(db.StringField())

    def init(self, fn, ln, emp_id, admin, depts):
        """Creates employee object and saves it to the database"""
        self.fn = fn
        self.ln = ln
        self.password = bcrypt.generate_password_hash(generate_password(fn, ln, emp_id))
        self.emp_id = emp_id
        self.admin = admin
        self.clocked_in = "None"
        self.active = True
        self.depts = depts
        self.save()
        return self

    def clock_in(self, dept, datetime, warning=False):
        assert dept in self.depts, "Department must be in user's departments"
        assert self.clocked_in == "None", "Must be currently clocked out"
        self.clocked_in = Timecard().init(self.emp_id, dept, datetime, "Clock In", warning=warning).timecard_id
        self.save()

    def clock_out(self, dept, datetime, warning=False):
        assert self.clocked_in != "None", "Must be currently clocked in"
        Timecard().init(self.emp_id, dept, datetime, "Clock Out", timecard_id=self.clocked_in, warning=warning)
        self.clocked_in = "None"
        self.save()




class Timecard(db.Document):
    emp_id = db.StringField()
    dept = db.StringField()
    action = db.StringField()
    datetime = db.DateTimeField()
    warning = db.BoolField()
    timecard_id = db.StringField()

    def init(self, emp_id, dept, datetime, action, timecard_id=None, warning=False):
        """Creates timecard object"""
        self.emp_id = emp_id
        self.dept = dept
        self.datetime = datetime
        self.warning = warning
        self.action = action
        self.timecard_id = timecard_id or uuid.uuid4().hex
        self.save()
        return self


class User:
    def __init__(self, _id, admin=False):
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

