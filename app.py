from config import *


@lm.user_loader
def load_user(user_id):
    u = Employee.query.filter(Employee.mongo_id == user_id).first()
    if not u:
        return None
    print("Loading User...")
    return User(str(u.mongo_id), bool(u.admin))


@app.route('/', methods=['GET', 'POST'])
def index():
    nxt = request.args.get('next')
    if nxt is None:
        nxt = "timeEntry"
    elif str(nxt).strip('/') == "portal":
        if current_user.is_active:
            return redirect(url_for('portal'))
    return render_template('login.html', next=str(nxt).strip('/'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    nxt = request.args.get('next')
    if request.method == 'POST':
        user = Employee.query.filter(Employee.empID == request.form['employee-id']).first()
        if user and bcrypt.check_password_hash(user.password,request.form['employee-password']):
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
def timeEntry():
    user = Employee.query.get(current_user.get_id())
    if len(user.depts) > 1:
        return render_template('multidepts.html', Timecard=Timecard, Employee=Employee)
    else:
        return redirect(url_for('makeEntry', dept=user.depts[0]), code=307)



@app.route('/makeEntry', methods=['GET', 'POST'])
@login_required
def makeEntry():
    if request.method == "POST":
        user = Employee.query.get(current_user.get_id())
        skip = request.args.get('skip', False)
        dept = request.args['dept']
        time = datetime.datetime.now(tz)
        clock = Timecard().init(user.empID, dept, False, time)
        if user.clockedIn != "None":  # if currently clocked in
            lastIn = Timecard.query.filter(Timecard.timecardID == user.clockedIn).first()
            # lastIn = Timecard.query.filter(Timecard.empID==user.empID).descending(Timecard.datetime).first()
            if (datetime.datetime.now()-lastIn.datetime).total_seconds() > 36000 and not skip: # clocked in too long
                    return render_template('warning.html', dept=dept, time=time, lastIn=lastIn.datetime.ctime())
            if lastIn.dept == dept:
                clockOut(clock, user)
                clock.save()
                flash("You have clocked out as "+dept+" at "+str(time))
                return redirect(url_for('logout'))
            else:
                transition = Timecard().init(user.empID, dept, False, time)
                clockOut(transition, user)
                transition.save()
                flash("You have been clocked out as "+lastIn.dept+" and clocked in as "+dept+" at "+str(time))
        else:
            flash("You have been clocked in as "+dept+" at "+str(time))
        clockIn(clock, user)
        clock.save()
        return redirect(url_for('logout'))
    else:
        flash("Cannot access that page")
        return redirect(url_for('logout'))



def clockOut(clock, user):
    clock.action = "Clock Out"
    clock.timecardID = user.clockedIn
    user.clockedIn = "None"
    user.save()

def clockIn(clock, user):
    clock.action = "Clock In"
    user.clockedIn = clock.timecardID
    user.save()


@app.route('/error', methods=['GET', 'POST'])
def error():
    if request.method=="POST":
        dept = request.args['dept']
        user = Employee.query.get(current_user.get_id())
        lastIn = Timecard.query.filter(Timecard.empID==user.empID).descending(Timecard.datetime).first()
        lastIn.warning = True
        lastIn.save()
        user.clockedIn = "None"
        user.save()
        return redirect(url_for('makeEntry',dept=dept,skip=True),code=307)
    else:
        flash("You cannot access that page that way! Please try again!")
        return redirect(url_for('index',Employee=Employee))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/portal', methods=['GET', 'POST'])
@login_required
def portal():
    return render_template('portal.html', Employee=Employee, Timecard=Timecard)


@app.route('/reg', methods=['GET', 'POST'])
def reg():
    return redirect(url_for('index'))


@app.route('/registerEmp', methods=['GET', 'POST'])
def registerEmp():
    return redirect(url_for('index'))


@app.route('/view', methods=['GET', 'POST'])
@login_required
def view():
    user = Employee.query.get(current_user.get_id())
    entryList = []
    entries = Timecard.query.filter(Timecard.empID == user.empID, Timecard.action == "Clock In").descending(Timecard.datetime)
    for entry in entries:
        entryId = entry.timecardID
        convertedIn = pytz.timezone('UTC').localize(entry.datetime).astimezone(tz)
        try:
            clockOut = Timecard.query.filter(Timecard.timecardID == entryId,Timecard.action == "Clock Out").first()
            convertedOut = pytz.timezone('UTC').localize(clockOut.datetime).astimezone(tz)
            duration = (convertedOut - convertedIn).total_seconds()//.36/10000
            foo = Entry(entry.dept,convertedIn.strftime('%m/%d/%Y %I:%M %p'),convertedOut.strftime('%m/%d/%Y %I:%M %p'),duration)
        except:
            if user.clockedIn == entry.timecardID:
                flag = 1
                out = "Currently Clocked In"
            else:
                flag = 2
                out = "Error"
            foo = Entry(entry.dept,convertedIn.strftime('%m/%d/%Y %I:%M %p'),out,flag=flag)
        entryList.append(foo)
    return render_template('timecard.html', entries=entryList)


@app.route('/settings',methods=['GET','POST'])
@login_required
def settings():
    return render_template('settings.html',Employee=Employee)



@app.route('/changePass', methods=["GET","POST"])
@fresh_login_required
def changePass():
    if request.method=="POST":
        user = Employee.query.get(current_user.get_id())
        if bcrypt.check_password_hash(user.password,request.form['current-pass']) and request.form['new-pass']==request.form['new-pass-confirm']:
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
app.run(host=host,port=port)
    

    
