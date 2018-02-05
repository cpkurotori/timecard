from flask import request, flash, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, fresh_login_required, current_user
import datetime
from config import *
from classes import *
from functools import wraps


def admin_required(func):
    @wraps(func)
    @login_required
    def decorated(*args, **kargs):
        if not current_user.is_admin():
            flash("You must be an admin to access that page.")
            return redirect(url_for('portal'))
        else:
            return func(*args, **kargs)
    return decorated


def post_only(message, url, *oargs, **okargs):
    def post_decorator(func):
        @wraps(func)
        def decorator(*args, **kargs):
            if request.method == "POST":
                return func(*args, **kargs)
            else:
                flash(message)
                return redirect(url_for(url, **okargs), *oargs)
        return decorator
    return post_decorator


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
@post_only("Cannot access that page", 'logout')
def login():
    nxt = request.args.get('next')
    user = get_employee(request.form['employee-id'])
    if user and check_password(user.password, request.form['employee-password']):
        user_obj = User(str(user.mongo_id))
        login_user(user_obj, remember=True)
        return redirect(url_for(nxt), code=307)
    else:
        flash("Invalid credentials. Try again.")
        return redirect(url_for('index', next=str(nxt)))


@app.route('/timeEntry', methods=['GET', 'POST'])
@login_required
def time_entry():
    user = get_current_user(current_user.get_id())
    if len(user.depts) > 1:
        return redirect(url_for('multidept'), code=307)
    else:
        return redirect(url_for('make_entry', dept=user.depts[0]), code=307)


@app.route('/multidepts', methods=['GET', 'POST'])
@login_required
@post_only("Cannot access that page", 'logout')
def multidept():
    return render_template('multidepts.html',
                           get_timecard=get_one_timecard,
                           get_user=get_current_user,
                           get_dept=get_dept)


@app.route('/makeEntry', methods=['GET', 'POST'])
@login_required
@post_only("Cannot access that page", 'logout')
def make_entry():
    user = get_current_user(current_user.get_id())
    warning = request.args.get('skip', False)
    dept = request.args['dept']
    time = datetime.datetime.now(tz)
    if user.clocked_in != "None":  # if currently clocked in
        last_in = get_one_timecard(user.clocked_in)
        if (datetime.datetime.now()-last_in.datetime).total_seconds() > 36000 and not warning:
                return render_template('warning.html', dept=dept, time=time, last_in=last_in.datetime.ctime())
        if last_in.dept == dept:
            user.clock_out(dept, time, warning=warning)
            flash("You have clocked out as {} at {}".format(get_dept(dept).name, str(time)))
            return redirect(url_for('logout'))
        else:
            user.clock_out(last_in.dept, time, warning=warning)
            flash("You have been clocked out as {} and clocked in as {} at {}".format(
                                                    get_dept(last_in.dept).name,
                                                    dept,
                                                    str(time)))
    else:
        flash("You have been clocked in as {} at {}".format(get_dept(dept).name, str(time)))
    user.clock_in(dept, time, warning=warning)
    return redirect(url_for('logout'))


@app.route('/error', methods=['GET', 'POST'])
@post_only("You cannot access that page that way! Please try again!", 'logout')
def error():
    dept = request.args['dept']
    user = Employee.query.get(current_user.get_id())
    last_in = get_timecards(user.emp_id).first()
    last_in.warning = True
    last_in.save()
    user.clocked_in = "None"
    user.save()
    return redirect(url_for('make_entry', dept=dept, skip=True), code=307)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/portal', methods=['GET', 'POST'])
@login_required
def portal():
    return render_template('portal.html',
                           get_user=get_current_user,
                           get_timecard=get_one_timecard,
                           get_dept=get_dept)


@app.route('/reg', methods=['GET', 'POST'])
@admin_required
def reg():
    return render_template('register.html', depts=get_all_depts())


@app.route('/registerEmp', methods=['GET', 'POST'])
@admin_required
@post_only("You cannot access the page that way", 'portal')
def register_emp():
    fn = request.form.get('employee-fn')
    ln = request.form.get('employee-ln')
    emp_id = request.form.get('employee-id')
    admin = request.form.get('employee-admin') == 'on'
    depts = request.form.getlist('employee-depts')
    if not (fn or ln or emp_id):
        flash("Please fill out all fields.")
        return redirect(url_for('reg'))
    elif get_employee(emp_id) is not None:
            flash("There already exists an employee with that ID.")
            return redirect(url_for('reg'))
    else:
        Employee().init(fn, ln, emp_id, admin, depts)
        print("{} {} {} {} {}", fn, ln, emp_id, admin, depts)
        flash("{0} {1}'s password is {2}. This can and should be changed in the employee portal.".format(
              fn, ln, generate_password(fn, ln, emp_id)))
        return redirect(url_for('portal'))


@app.route('/view', methods=['GET', 'POST'])
@login_required
def view():
    show = request.args.get('show', 10)
    page = request.args.get('page', 1)
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
            foo = Entry(get_dept(entry.dept).name, converted_in.strftime(time_string), converted_out.strftime(time_string), duration)
        else:
            if user.clocked_in == entry.timecard_id:
                flag = 1
                out = "Currently Clocked In"
            else:
                flag = 2
                out = "Error"
            foo = Entry(get_dept(entry.dept).name, converted_in.strftime(time_string), out, flag=flag)
        entry_list.append(foo)
    return render_template('timecard.html', entries=entry_list)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return render_template('settings.html', get_user=get_current_user)


@app.route('/changePass', methods=["GET", "POST"])
@fresh_login_required
@post_only("BAD! DON'T DO THAT!", 'portal')
def change_pass():
    user = Employee.query.get(current_user.get_id())
    matching = request.form['new-pass'] == request.form['new-pass-confirm']
    if check_password(user.password, request.form['current-pass']) and matching:
        user.password = bcrypt.generate_password_hash(request.form['new-pass'])
        user.save()
        flash("Password successfully changed.")
    else:
        flash("Could not authenticate password change. Please try again.")
    return redirect('/settings')


app.debug = os.environ.get('DEBUG') == "True"
host = os.environ.get('IP', '0.0.0.0')
port = os.environ.get('PORT', 5000)
app.run(host=host, port=port)
