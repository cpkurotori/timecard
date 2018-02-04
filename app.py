from flask import request, flash, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, fresh_login_required, current_user
import datetime
from config import *
from classes import *


@lm.user_loader
def load_user(user_id):
    u = get_current_user(user_id)
    if not u:
        return None
    print("Loading User...")
    return User(str(u.mongo_id), bool(u.admin))


@app.route('/', methods=['GET', 'POST'])
def index():
    nxt = request.args.get('next')
    if nxt is None:
        nxt = "time_entry"
    elif str(nxt).strip('/') == "portal":
        if current_user.is_active:
            return redirect(url_for('portal'))
    return render_template('login.html', next=str(nxt).strip('/'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    nxt = request.args.get('next')
    if request.method == 'POST':
        user = get_employee(request.form['employee-id'])
        if user and check_password(user.password, request.form['employee-password']):
            user_obj = User(str(user.mongo_id))
            login_user(user_obj, remember=True)
            return redirect(url_for(nxt), code=307)
        else:
            flash("Invalid credentials. Try again.")
            return redirect(url_for('index', next=str(nxt)))
    else:
        flash("Cannot access that page")
        return redirect(url_for('logout'))


@app.route('/timeEntry', methods=['GET', 'POST'])
@login_required
def time_entry():
    user = get_current_user(current_user.get_id())
    if len(user.depts) > 1:
        return render_template('multidepts.html', get_timecard=get_one_timecard, get_user=get_current_user)
    else:
        return redirect(url_for('make_entry', dept=user.depts[0]), code=307)


@app.route('/makeEntry', methods=['GET', 'POST'])
@login_required
def make_entry():
    if request.method == "POST":
        user = get_current_user(current_user.get_id())
        skip = request.args.get('skip', False)
        dept = request.args['dept']
        time = datetime.datetime.now(tz)
        clock = Timecard().init(user.emp_id, dept, False, time)
        if user.clocked_in != "None":  # if currently clocked in
            last_in = get_one_timecard(user.clocked_in)
            if (datetime.datetime.now()-last_in.datetime).total_seconds() > 36000 and not skip:  # clocked in too long
                    return render_template('warning.html', dept=dept, time=time, last_in=last_in.datetime.ctime())
            if last_in.dept == dept:
                clock_out(clock, user)
                clock.save()
                flash("You have clocked out as {} at {}".format(dept, str(time)))
                return redirect(url_for('logout'))
            else:
                transition = Timecard().init(user.emp_id, dept, False, time)
                clock_out(transition, user)
                transition.save()
                flash("You have been clocked out as {} and clocked in as {} at {}".format(
                                                                last_in.dept, dept, str(time)))
        else:
            flash("You have been clocked in as {} at {}".format(dept, str(time)))
        clock_in(clock, user)
        clock.save()
        return redirect(url_for('logout'))
    else:
        flash("Cannot access that page")
        return redirect(url_for('logout'))


def clock_out(clock, user):
    clock.action = "Clock Out"
    clock.timecard_id = user.clocked_in
    user.clocked_in = "None"
    user.save()


def clock_in(clock, user):
    clock.action = "Clock In"
    user.clocked_in = clock.timecard_id
    user.save()


@app.route('/error', methods=['GET', 'POST'])
def error():
    if request.method == "POST":
        dept = request.args['dept']
        user = Employee.query.get(current_user.get_id())
        last_in = Timecard.query.filter(Timecard.emp_id == user.emp_id).descending(Timecard.datetime).first()
        last_in.warning = True
        last_in.save()
        user.clocked_in = "None"
        user.save()
        return redirect(url_for('make_entry', dept=dept, skip=True), code=307)
    else:
        flash("You cannot access that page that way! Please try again!")
        return redirect(url_for('index', get_user=get_current_user))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/portal', methods=['GET', 'POST'])
@login_required
def portal():
    return render_template('portal.html', get_user=get_current_user, get_timecard=get_one_timecard)


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    return redirect(url_for('index'))


@app.route('/registerEmp', methods=['GET', 'POST'])
def register_emp():
    return redirect(url_for('index'))


@app.route('/view', methods=['GET', 'POST'])
@login_required
def view():
    user = Employee.query.get(current_user.get_id())
    entry_list = []
    entries = get_timecards(user.emp_id, "Clock In")
    for entry in entries:
        entry_id = entry.timecard_id
        converted_in = pytz.timezone('UTC').localize(entry.datetime).astimezone(tz)
        out = get_corresponding_timecard(entry_id, "Clock Out").first()
        if out is not None:
            converted_out = pytz.timezone('UTC').localize(out.datetime).astimezone(tz)
            duration = (converted_out - converted_in).total_seconds()//.36/10000
            foo = Entry(entry.dept, converted_in.strftime(time_string), converted_out.strftime(time_string), duration)
        else:
            if user.clocked_in == entry.timecard_id:
                flag = 1
                out = "Currently Clocked In"
            else:
                flag = 2
                out = "Error"
            foo = Entry(entry.dept, converted_in.strftime(time_string), out, flag=flag)
        entry_list.append(foo)
    return render_template('timecard.html', entries=entry_list)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template('settings.html', get_user=get_current_user)


@app.route('/changePass', methods=["GET", "POST"])
@fresh_login_required
def change_pass():
    if request.method == "POST":
        user = Employee.query.get(current_user.get_id())
        matching = request.form['new-pass'] == request.form['new-pass-confirm']
        if check_password(user.password, request.form['current-pass']) and matching:
            user.password = bcrypt.generate_password_hash(request.form['new-pass'])
            user.save()
            flash("Password successfully changed.")
        else:
            flash("Could not authenticate password change. Please try again.")
        return redirect('/settings')
    return redirect(url_for('portal'))


app.debug = False
host = os.environ.get('IP', '0.0.0.0')
port = os.environ.get('PORT', 5000)
app.run(host=host, port=port)
