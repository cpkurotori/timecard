from mongo import *


def get_employee(emp_id):
    """Returns Employee object with matching emp_id (Simple Employee ID i.e. 0438828)"""
    return Employee.query.filter(Employee.emp_id == emp_id).first()


def get_current_user(user_id):
    """Returns Employee object with matching user_id (MongoDB id)"""
    return Employee.query.get(user_id)


def get_one_timecard(timecard_id):
    """Returns Timecard object with matching timecard_id"""
    return Timecard.query.filter(Timecard.timecard_id == timecard_id).first()


def get_timecards(emp_id, action=None):
    """Returns Query of Timecard object with matching employee id and action
       in descending order"""
    if action:
        return Timecard.query.filter(Timecard.emp_id == emp_id, Timecard.action == action).descending(Timecard.datetime)
    else:
        return Timecard.query.filter(Timecard.emp_id == emp_id).descending(Timecard.datetime)


def get_corresponding_timecard(entry_id, action=None):
    if action:
        return Timecard.query.filter(Timecard.timecard_id == entry_id, Timecard.action == action).descending(Timecard.datetime)
    else:
        return Timecard.query.filter(Timecard.timecard_id == entry_id).descending(Timecard.datetime)


def get_all_depts():
    return [(dept.name, dept.dept_id) for dept in Department.query.filter().all()]


def get_dept(dept_id):
    return Department.query.filter(Department.dept_id == dept_id).first()
